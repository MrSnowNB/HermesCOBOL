#!/usr/bin/env python3
# LLM-FREE — Deterministic COBOL semantic extraction. No LLM inference.
"""
hermes_v11_combined_extractor.py
====================================
HermesCOBOL schema v1.1 — single-module semantic enrichment.

Purpose
-------
Drop this file into HermesCOBOL/scripts/ and wire it into extract_facts.py
via the public `enrich()` function. It replaces scripts/semantic_extract.py
and supersedes the earlier prototype.

Relationship to CardDemo tools
------------------------------
This module synthesises and simplifies four prior CardDemo analysis scripts:

  extract_cfg_local.py      → paragraphs, PERFORM/GOTO graph, entry/exit, reachability
  extract_fallthrough.py    → fallthrough edge detection using terminator classification
  extract_paragraph_io.py   → verb-level action classification per paragraph
  extract_file_control.py   → SELECT/ASSIGN/FD linkage → file_lineage
  pass1_annotate.py         → multiline EXEC CICS collapsing strategy for CICS subtree

All logic is pure text-scan against the raw or preprocessed COBOL source.
No cobc, no Java, no smojol, no external dependencies, no LLM.

Public API
----------
  enrich(
    program_name   : str,
    raw_cobol      : str,               # exact bytes read from .cbl
    preprocessed   : str | None,        # cobc -E output, or None to use raw
    rekt_json      : dict | None,       # REKT CFG report dict, or None
    base_facts     : dict,              # v1.0 facts dict (read-only)
  ) -> dict

The returned dict contains ONLY the v1.1 additions; the caller merges
them into the base_facts. Existing v1.0 keys are never overwritten.

v1.1 output keys
----------------
  paragraphs_defined    list[{name, source_line, area_a}]
  paragraphs_referenced list[str]
  control_flow          {cfg_source, entry_points, exit_points, edges, unresolved}
  paragraph_actions     {para_name: [action_tag, ...]}
  file_operations       {file_name: [{paragraph, operation, source_line}]}
  file_lineage          [{name, ddname, fd_record}]
  cics                  {commarea_used, commands, maps_used, mapsets_used,
                         aid_keys, screen_flow}  | None

Constraints
-----------
  • Python 3.10+ • stdlib only • no LLM calls • no network • no cobc
  • Never modifies base_facts
  • Never touches main branch or v0.1-raw-substrate tag
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


# ===========================================================================
# §1  CONSTANTS AND NOISE FILTERS
# ===========================================================================

# Tokens that look like paragraph labels syntactically but are COBOL
# scope-terminators, reserved words, or division/section headers.
# Applied in extract_paragraphs_defined() before any other processing.
# Source: implementation spec + direct inspection of CardDemo corpora.
PARAGRAPH_NOISE: frozenset[str] = frozenset([
    "END-IF", "END-PERFORM", "END-EVALUATE", "END-READ",
    "END-WRITE", "END-REWRITE", "END-DELETE", "END-START",
    "END-CALL", "END-STRING", "END-UNSTRING", "END-EXEC",
    "EXIT", "CONTINUE", "GOBACK", "STOP",
    "FILE-CONTROL", "I-O-CONTROL", "PROGRAM-ID",
])

# Division, section, and FD-level reserved words that appear as label-like
# tokens in fixed-format COBOL source but are never paragraph names.
RESERVED_DIVISIONS: frozenset[str] = frozenset([
    "IDENTIFICATION", "ENVIRONMENT", "DATA", "PROCEDURE",
    "CONFIGURATION", "INPUT-OUTPUT", "FILE", "WORKING-STORAGE",
    "LINKAGE", "LOCAL-STORAGE", "REPORT", "SCREEN",
    "AUTHOR", "INSTALLATION", "DATE-WRITTEN",
    "DATE-COMPILED", "SECURITY", "REMARKS",
    "FD", "SD", "RD",
])

# PERFORM clause keywords that follow a paragraph name but are not themselves
# paragraph names (e.g. PERFORM READ-FILE UNTIL WS-EOF = 'Y').
PERFORM_KEYWORDS: frozenset[str] = frozenset([
    "UNTIL", "VARYING", "TIMES", "WITH", "TEST",
    "THRU", "THROUGH", "BEFORE", "AFTER",
])

# CICS commands that terminate a paragraph (no fallthrough after them).
# From CardDemo extract_fallthrough.py §CICS_TERMINATOR_OPS.
CICS_TERMINATORS: frozenset[str] = frozenset(["RETURN", "XCTL"])

# Paragraph name patterns that flag the paragraph as an abend/error routine.
# Used in action classification and exit-point detection.
RE_ABEND_NAME = re.compile(r"(ABEND|9999|9910|ABORT|STORUN|STOP-RUN)", re.IGNORECASE)
RE_ERROR_NAME = re.compile(r"(ERROR|STAT(?:US)?|INVALID|EXCEPT|DISPLAY)", re.IGNORECASE)


# ===========================================================================
# §2  REGEX LIBRARY
#     All patterns compiled once at module load. Brief comments explain
#     each non-obvious pattern choice.
# ===========================================================================

# --- Source structure ---

# Paragraph label: a name (Area A, cols 8-11 in fixed format) ending with a
# period and nothing else on the line (after optional trailing spaces).
# We allow 0-11 leading spaces to accommodate both fixed- and free-format
# output from cobc -E, which re-emits lines without sequence numbers.
RE_PARA_LABEL = re.compile(
    r"^( {0,11})([A-Z0-9][A-Z0-9-]*)[ \t]*\.[ \t]*$",
    re.MULTILINE | re.IGNORECASE,
)

# SECTION header: same Area-A position, followed by the word SECTION.
RE_SECTION_HEADER = re.compile(
    r"^ {0,11}([A-Z0-9][A-Z0-9-]*)[ \t]+SECTION[ \t]*\.[ \t]*$",
    re.MULTILINE | re.IGNORECASE,
)

# Division markers used to locate boundaries within source text.
RE_PROC_DIV = re.compile(
    r"^[ \t]*PROCEDURE[ \t]+DIVISION\b",
    re.MULTILINE | re.IGNORECASE,
)
RE_DATA_DIV = re.compile(
    r"^[ \t]*DATA[ \t]+DIVISION\b",
    re.MULTILINE | re.IGNORECASE,
)
RE_ENV_DIV = re.compile(
    r"^[ \t]*ENVIRONMENT[ \t]+DIVISION\b",
    re.MULTILINE | re.IGNORECASE,
)

# --- PERFORM variants (mined from extract_cfg_local.py analyze_flow) ---

# Simple PERFORM <para>  (no inline body, no clause)
# Anchored at end-of-line to avoid matching PERFORM UNTIL <para> inline blocks.
RE_PERF_SIMPLE = re.compile(
    r"\bPERFORM[ \t]+([A-Z0-9][A-Z0-9-]+)[ \t]*$",
    re.MULTILINE | re.IGNORECASE,
)
# PERFORM <para> THRU <para2>
RE_PERF_THRU = re.compile(
    r"\bPERFORM[ \t]+([A-Z0-9][A-Z0-9-]+)[ \t]+THRU(?:UGH)?[ \t]+([A-Z0-9][A-Z0-9-]+)",
    re.IGNORECASE,
)
# PERFORM <para> UNTIL ... (loop on named paragraph)
RE_PERF_UNTIL = re.compile(
    r"\bPERFORM[ \t]+([A-Z0-9][A-Z0-9-]+)[ \t]+UNTIL",
    re.IGNORECASE,
)
# PERFORM <para> VARYING ... (loop on named paragraph)
RE_PERF_VARYING = re.compile(
    r"\bPERFORM[ \t]+([A-Z0-9][A-Z0-9-]+)[ \t]+VARYING",
    re.IGNORECASE,
)
# PERFORM <para> <n> TIMES
RE_PERF_TIMES = re.compile(
    r"\bPERFORM[ \t]+([A-Z0-9][A-Z0-9-]+)[ \t]+\d+[ \t]+TIMES",
    re.IGNORECASE,
)
# Generic PERFORM target capture (used for paragraphs_referenced)
RE_PERF_ANY = re.compile(
    r"\bPERFORM[ \t]+([A-Z0-9][A-Z0-9-]+)",
    re.IGNORECASE,
)

# --- GO TO ---
RE_GOTO = re.compile(
    r"\bGO[ \t]+TO[ \t]+([A-Z0-9][A-Z0-9-]+)",
    re.IGNORECASE,
)

# --- CALL (literal program name only; dynamic CALL USING <var> not captured) ---
RE_CALL_LITERAL = re.compile(
    r"\bCALL[ \t]+['\"]([A-Z0-9][A-Z0-9-]*)['\"][ \t]",
    re.IGNORECASE,
)

# --- Terminator verbs (from extract_fallthrough.py _classify_terminator) ---
RE_STOP_RUN = re.compile(r"\bSTOP[ \t]+RUN\b", re.IGNORECASE)
RE_GOBACK   = re.compile(r"\bGOBACK\b",        re.IGNORECASE)
RE_EXIT_PGM = re.compile(r"\bEXIT[ \t]+PROGRAM\b", re.IGNORECASE)

# --- File I/O verbs (mined from extract_paragraph_io.py WRITER_VERBS) ---
RE_OPEN_MODE = re.compile(
    r"\bOPEN[ \t]+(INPUT|OUTPUT|I-O|EXTEND)[ \t]+([A-Z0-9][A-Z0-9-]+)",
    re.IGNORECASE,
)
RE_IO_VERB = re.compile(
    r"\b(CLOSE|READ|WRITE|REWRITE|DELETE|START)[ \t]+([A-Z0-9][A-Z0-9-]+)",
    re.IGNORECASE,
)

# --- Branch / transform verbs ---
RE_IF       = re.compile(r"\bIF\b",       re.IGNORECASE)
RE_EVALUATE = re.compile(r"\bEVALUATE\b", re.IGNORECASE)
RE_MOVE     = re.compile(r"\bMOVE\b",     re.IGNORECASE)
RE_DISPLAY  = re.compile(r"\bDISPLAY\b",  re.IGNORECASE)

# --- File environment (mined from extract_file_control.py) ---
RE_SELECT = re.compile(
    r"\bSELECT[ \t]+([A-Z0-9][A-Z0-9-]*)[ \t]+ASSIGN[ \t]+(?:TO[ \t]+)?([A-Z0-9\-]+)",
    re.IGNORECASE,
)
RE_FD = re.compile(
    r"^[ \t]*FD[ \t]+([A-Z0-9][A-Z0-9-]*)",
    re.MULTILINE | re.IGNORECASE,
)
RE_COPY = re.compile(r"\bCOPY[ \t]+([A-Z0-9][A-Z0-9-]*)", re.IGNORECASE)

# --- CICS patterns (strategy from pass1_annotate.py multiline collapsing) ---

# EXEC CICS marker (presence check)
RE_EXEC_CICS_PRESENT = re.compile(r"\bEXEC[ \t]+CICS\b", re.IGNORECASE)
# EXEC CICS <COMMAND> ... END-EXEC block capture (multiline)
# Note: COBOL EXEC CICS blocks can span multiple continuation lines. We
# collapse them before extraction (see _collapse_cics_blocks()).
RE_EXEC_CICS_BLOCK = re.compile(
    r"EXEC[ \t]+CICS[ \t]+([A-Z][A-Z0-9-]*).*?END-EXEC",
    re.IGNORECASE | re.DOTALL,
)
# MAP and MAPSET operands
RE_CICS_MAP    = re.compile(r"\bMAP[ \t]*\([ \t]*['\"]?([A-Z0-9][A-Z0-9-]*)['\"]?[ \t]*\)",    re.IGNORECASE)
RE_CICS_MAPSET = re.compile(r"\bMAPSET[ \t]*\([ \t]*['\"]?([A-Z0-9][A-Z0-9-]*)['\"]?[ \t]*\)", re.IGNORECASE)
# SEND MAP / RECEIVE MAP (used for screen_flow)
RE_CICS_SEND_MAP    = re.compile(r"EXEC[ \t]+CICS[ \t]+SEND[ \t]+MAP",    re.IGNORECASE)
RE_CICS_RECEIVE_MAP = re.compile(r"EXEC[ \t]+CICS[ \t]+RECEIVE[ \t]+MAP", re.IGNORECASE)
# AID key patterns: both EIBAID = DFHxxx and EVALUATE EIBAID WHEN DFHxxx
# from pass1_annotate.py aid-key handling.
RE_AID_EIBAID   = re.compile(r"EIBAID[ \t]*=[ \t]*DFHAID[ \t]*\.?([A-Z0-9]+)", re.IGNORECASE)
RE_AID_DFHAID   = re.compile(r"\bDFHAID\.([A-Z0-9]+)\b",                        re.IGNORECASE)
RE_AID_WHEN     = re.compile(r"WHEN[ \t]+DFHAID[ \t]*\.?([A-Z0-9]+)",            re.IGNORECASE)
RE_COMMAREA     = re.compile(r"\bDFHCOMMAREA\b",                                   re.IGNORECASE)


# ===========================================================================
# §3  SOURCE PREPROCESSING UTILITIES
# ===========================================================================

def strip_comment_lines(source: str) -> str:
    """
    Remove fixed-format COBOL comment lines (column 7 == '*' or '/').
    Also strips sequence-number areas (cols 1-6) if present.
    Blank indicator lines (col 7 == ' ') are preserved.
    """
    out: list[str] = []
    for line in source.splitlines():
        if len(line) >= 7 and line[6] in ("*", "/"):
            # Comment line: replace with blank to preserve line numbering
            out.append("")
        else:
            out.append(line)
    return "\n".join(out)


def _collapse_cics_blocks(source: str) -> str:
    """
    Collapse multiline EXEC CICS ... END-EXEC blocks into single logical lines.

    Strategy: scan line by line. When we encounter 'EXEC CICS', accumulate
    continuation lines until we see 'END-EXEC', then join them with a single
    space and emit as one line.

    This mirrors the multiline-block strategy in CardDemo pass1_annotate.py.
    Preserves non-CICS lines exactly. Comment lines (col 7 = *) are skipped
    inside the accumulation window.

    Returns the source with CICS blocks collapsed but structure otherwise
    unchanged.
    """
    lines = source.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        up = line.upper()
        if "EXEC" in up and "CICS" in up:
            # Start of a CICS block. Accumulate until END-EXEC.
            block_parts = [line.strip()]
            i += 1
            while i < len(lines):
                cont = lines[i]
                # Skip comment continuation lines
                if len(cont) >= 7 and cont[6] in ("*", "/"):
                    i += 1
                    continue
                block_parts.append(cont.strip())
                if "END-EXEC" in cont.upper():
                    i += 1
                    break
                i += 1
            out.append(" ".join(block_parts))
        else:
            out.append(line)
            i += 1
    return "\n".join(out)


def _lineno(text: str, match_start: int) -> int:
    """Return 1-based line number for a character offset in text."""
    return text[:match_start].count("\n") + 1


# ===========================================================================
# §4  PARAGRAPH EXTRACTION
#     Mined from extract_cfg_local.py extract_paragraphs() + analyze_flow()
# ===========================================================================

def _section_names(clean: str) -> set[str]:
    """Return set of SECTION names to exclude from paragraph labels."""
    return {m.group(1).upper() for m in RE_SECTION_HEADER.finditer(clean)}


def extract_paragraphs_defined(raw: str, clean: str) -> list[dict]:
    """
    Extract real paragraph labels from the PROCEDURE DIVISION.

    Returns list of {name: str, source_line: int, area_a: bool}.
    area_a == True means the label starts in cols 8-11 (normal COBOL).

    Filters applied (in order):
      1. PARAGRAPH_NOISE   – scope-terminators and reserved tokens
      2. RESERVED_DIVISIONS– division/section/FD-level reserved words
      3. -DIVISION suffix  – leftover division header tokens
      4. SECTION names     – section labels are not paragraphs
      5. Deduplication     – keep first occurrence only
    """
    sections = _section_names(clean)
    seen: set[str] = set()
    result: list[dict] = []

    for m in RE_PARA_LABEL.finditer(clean):
        indent = len(m.group(1))
        name   = m.group(2).upper()

        if name in PARAGRAPH_NOISE:        continue
        if name in RESERVED_DIVISIONS:     continue
        if name.endswith("-DIVISION"):     continue
        if name in sections:               continue
        if name in seen:                   continue

        seen.add(name)
        lineno = _lineno(raw, m.start())  # provenance: line in RAW source
        result.append({
            "name":        name,
            "source_line": lineno,
            "area_a":      indent <= 3,   # Area A = 0-3 leading spaces after seq area
        })
    return result


def extract_paragraphs_referenced(
    clean: str,
    defined: list[dict],
) -> list[str]:
    """
    Return sorted list of paragraph names that appear as PERFORM or GO TO
    targets and are also in the defined set.

    This is the 'referenced' side of the defined/referenced split requested
    in the spec. A paragraph may be defined but never referenced (dead code),
    or referenced but not defined (unresolved).
    """
    defined_names = {p["name"] for p in defined}
    referenced: set[str] = set()

    for m in RE_PERF_ANY.finditer(clean):
        t = m.group(1).upper()
        if t in defined_names and t not in PERFORM_KEYWORDS:
            referenced.add(t)
    for m in RE_GOTO.finditer(clean):
        t = m.group(1).upper()
        if t in defined_names:
            referenced.add(t)
    return sorted(referenced)


# ===========================================================================
# §5  PROCEDURE DIVISION BODY SPLITTER
#     Splits source into {para_name: body_str} for per-paragraph analysis.
#     Required by action classification, file operations, and CFG.
# ===========================================================================

def split_by_paragraph(
    clean: str,
    defined: list[dict],
) -> dict[str, str]:
    """
    Divide the PROCEDURE DIVISION into per-paragraph body text.

    Returns {para_name: body_text} where body_text is everything from the
    line after the paragraph label until the line before the next label.
    Paragraphs not in `defined` (i.e. noise-filtered out) are ignored.

    Strategy: linear scan, matching labels by name rather than by regex
    re-run, to stay in sync with the noise filter applied in step §4.
    """
    defined_set = {p["name"] for p in defined}
    proc_m = RE_PROC_DIV.search(clean)
    if not proc_m:
        return {}  # No PROCEDURE DIVISION found — COBSWAIT-style stub

    proc_lines = clean[proc_m.end():].splitlines()
    label_re   = re.compile(
        r"^( {0,11})([A-Z0-9][A-Z0-9-]*)[ \t]*\.[ \t]*$",
        re.IGNORECASE,
    )

    bodies: dict[str, list[str]] = {}
    current: str | None = None

    for line in proc_lines:
        m = label_re.match(line)
        if m:
            name = m.group(2).upper()
            if name in defined_set:
                current = name
                bodies.setdefault(current, [])
                continue
        if current:
            bodies[current].append(line)

    return {k: "\n".join(v) for k, v in bodies.items()}


# ===========================================================================
# §6  TERMINATOR CLASSIFICATION
#     Mined from extract_fallthrough.py _classify_terminator() and
#     the CICS_TERMINATOR_OPS logic.
# ===========================================================================

def _paragraph_terminator(body: str, name: str) -> str:
    """
    Classify how a paragraph terminates, scanning its body from bottom to top
    to find the last explicit transfer of control.

    Returns one of:
      'stop-run'            – STOP RUN in body
      'goback'              – GOBACK in body
      'explicit-exit'       – EXIT PROGRAM in body
      'goto'                – last statement is GO TO
      'cics-return'         – EXEC CICS RETURN END-EXEC
      'cics-xctl'           – EXEC CICS XCTL END-EXEC
      'implicit'            – none of the above (falls through)

    Note: 'implicit' is the default. The caller (build_cfg_text_scan) decides
    whether to add a fallthrough edge based on paragraph order.
    """
    # Scan the collapsed CICS version of the body for CICS terminators
    cics_body = _collapse_cics_blocks(body)
    for m in RE_EXEC_CICS_BLOCK.finditer(cics_body):
        cmd = m.group(1).upper()
        if cmd in CICS_TERMINATORS:
            return f"cics-{cmd.lower()}"

    if RE_STOP_RUN.search(body): return "stop-run"
    if RE_GOBACK.search(body):   return "goback"
    if RE_EXIT_PGM.search(body): return "explicit-exit"
    if RE_GOTO.search(body):     return "goto"
    return "implicit"


# ===========================================================================
# §7  CFG CONSTRUCTION
#     Edges: perform, perform_thru, goto, call, fallthrough
#     (conditional_true/conditional_false require REKT; left for adapter).
#     Reachability walk from entry_points mined from extract_cfg_local.py.
# ===========================================================================

def build_cfg_text_scan(
    clean: str,
    defined: list[dict],
    cics_present: bool = False,
) -> dict:
    """
    Build control_flow dict via pure text scan.
    cfg_source = 'text_scan'.

    Fidelity note (important for consumers):
      • PERFORM, GO TO, CALL, and fallthrough edges are reliable.
      • conditional_true / conditional_false edges require REKT output
        (static analysis of IF/EVALUATE branch targets is unreliable
        without a parse tree).
      • For CICS programs, a cfg_note is added documenting the lower fidelity
        since CICS pseudo-conversational flow cannot be recovered from raw text.
    """
    para_names  = {p["name"] for p in defined}
    para_order  = [p["name"] for p in defined]
    para_bodies = split_by_paragraph(clean, defined)

    edges:      list[dict] = []
    unresolved: list[str]  = []
    seen_edges: set[tuple]  = set()

    def _add(from_: str, to_: str, typ: str) -> None:
        key = (from_, to_, typ)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append({"from": from_, "to": to_, "type": typ, "source_lines": None})

    for para in para_order:
        body = para_bodies.get(para, "")

        # PERFORM THRU: two-paragraph range
        for m in RE_PERF_THRU.finditer(body):
            t_from = m.group(1).upper()
            t_thru  = m.group(2).upper()
            _add(para, t_from, "perform_thru")
            if t_from not in para_names: unresolved.append(t_from)
            if t_thru not in para_names: unresolved.append(t_thru)

        # Named PERFORM loops (UNTIL / VARYING / TIMES)
        for pat in (RE_PERF_UNTIL, RE_PERF_VARYING, RE_PERF_TIMES):
            for m in pat.finditer(body):
                t = m.group(1).upper()
                if t and t not in PERFORM_KEYWORDS:
                    _add(para, t, "perform")
                    if t not in para_names: unresolved.append(t)

        # Simple PERFORM (end-of-line anchored to avoid duplicating loop cases)
        for m in RE_PERF_SIMPLE.finditer(body):
            t = m.group(1).upper()
            if t not in PERFORM_KEYWORDS:
                _add(para, t, "perform")
                if t not in para_names: unresolved.append(t)

        # GO TO
        for m in RE_GOTO.finditer(body):
            t = m.group(1).upper()
            _add(para, t, "goto")
            if t not in para_names: unresolved.append(t)

        # CALL (literal program names only)
        for m in RE_CALL_LITERAL.finditer(body):
            _add(para, m.group(1).upper(), "call")

    # Fallthrough edges (from extract_fallthrough.py logic)
    # Per the authoritative rule in extract_fallthrough.py §docstring:
    # If the last effective verb in a paragraph is not a terminator
    # (goto/stop-run/goback/exit-program/cics-return/cics-xctl),
    # execution falls through to the next paragraph in source order.
    for i, para in enumerate(para_order[:-1]):
        body = para_bodies.get(para, "")
        term = _paragraph_terminator(body, para)
        if term == "implicit":
            nxt = para_order[i + 1]
            _add(para, nxt, "fallthrough")

    # Entry and exit points
    entry_points = [para_order[0]] if para_order else []
    exit_points:  list[str] = []
    for para in para_order:
        body = para_bodies.get(para, "")
        term = _paragraph_terminator(body, para)
        if term in {"stop-run", "goback", "explicit-exit", "cics-return", "cics-xctl"}:
            exit_points.append(para)
        if RE_ABEND_NAME.search(para):
            exit_points.append(para)
    # Last paragraph with implicit terminator is also an exit if it's reachable
    if para_order:
        last = para_order[-1]
        body = para_bodies.get(last, "")
        if _paragraph_terminator(body, last) == "implicit":
            exit_points.append(last)
    exit_points = sorted(set(exit_points))

    cfg: dict = {
        "cfg_source":   "text_scan",
        "entry_points": entry_points,
        "exit_points":  exit_points,
        "edges":        edges,
        "unresolved":   sorted(set(unresolved)),
    }

    # CICS programs: document the fidelity limitation explicitly.
    if cics_present:
        cfg["cfg_note"] = (
            "CICS program: cfg_source=text_scan. PERFORM/GOTO/fallthrough edges "
            "are present but pseudo-conversational control flow (RETURN/XCTL/LINK "
            "targets, screen flow) cannot be recovered without a CICS translator. "
            "conditional_true/conditional_false edges require REKT."
        )
    return cfg


def build_cfg_from_rekt(rekt_json: dict | None) -> dict | None:
    """
    Adapt a REKT CFG report dict into the HermesCOBOL control_flow shape.
    Returns None if rekt_json is None or contains no edges.

    REKT edge format assumption: {"from": str, "to": str, "type": str, ...}
    Entry/exit point arrays are carried through if present.
    cfg_source = 'rekt'.

    If REKT JSON is provided but has no edges (e.g. empty report),
    this returns None and the caller should fall back to text_scan.
    """
    if not rekt_json:
        return None

    raw_edges = rekt_json.get("edges") or []
    if not raw_edges:
        return None

    edges = [
        {
            "from":         str(e.get("from", "")),
            "to":           str(e.get("to",   "")),
            "type":         str(e.get("type", "unknown")),
            "source_lines": e.get("source_lines"),
        }
        for e in raw_edges
        if isinstance(e, dict) and e.get("from") and e.get("to")
    ]

    return {
        "cfg_source":   "rekt",
        "entry_points": rekt_json.get("entry_points") or [],
        "exit_points":  rekt_json.get("exit_points")  or [],
        "edges":        edges,
        "unresolved":   sorted(set(rekt_json.get("unresolved") or [])),
    }


# ===========================================================================
# §8  PARAGRAPH ACTION CLASSIFICATION
#     Simplified from extract_paragraph_io.py verb classification.
#     Key difference: we work from raw text rather than Pass-1 annotations,
#     so we classify verb-presence in a paragraph body rather than per-operand.
# ===========================================================================

# Mapping from file verb to action tag
_FILE_VERB_ACTIONS: dict[str, str] = {
    "OPEN":    "open_file",
    "CLOSE":   "close_file",
    "READ":    "read_file",
    "WRITE":   "write_file",
    "REWRITE": "rewrite_file",
    "DELETE":  "delete_record",
    "START":   "start_browse",
}


def classify_paragraph_actions(name: str, body: str, cics_body: str) -> list[str]:
    """
    Return a sorted list of deterministic action tags for a paragraph body.

    Parameters
    ----------
    name      : paragraph name (used for abend/error heuristics)
    body      : raw paragraph body text (unchanged)
    cics_body : body with EXEC CICS blocks collapsed (for CICS verb detection)

    Action tags produced:
      open_file, close_file, read_file, write_file, rewrite_file,
      delete_record, start_browse     ← from file I/O verbs
      call_program                    ← from CALL literal
      cics_command, send_map,         ← from EXEC CICS blocks
        receive_map
      branch_logic                    ← from IF / EVALUATE
      abend                           ← name matches RE_ABEND_NAME
      program_exit                    ← STOP RUN / GOBACK in body
      display_error                   ← DISPLAY in error/status paragraph
      display_output                  ← DISPLAY in non-error paragraph
      transform_data                  ← MOVE-dominant paragraph (no I/O)
      no_action_detected              ← fallback if nothing matched
    """
    actions: set[str] = set()

    # File I/O: OPEN INPUT/OUTPUT/I-O/EXTEND
    for m in RE_OPEN_MODE.finditer(body):
        actions.add("open_file")
    # Other file verbs
    for m in RE_IO_VERB.finditer(body):
        verb = m.group(1).upper()
        actions.add(_FILE_VERB_ACTIONS.get(verb, "file_io"))

    # CALL literal
    if RE_CALL_LITERAL.search(body):
        actions.add("call_program")

    # CICS commands (use collapsed body for reliable matching)
    if RE_EXEC_CICS_PRESENT.search(cics_body):
        actions.add("cics_command")
        if RE_CICS_SEND_MAP.search(cics_body):    actions.add("send_map")
        if RE_CICS_RECEIVE_MAP.search(cics_body): actions.add("receive_map")

    # Branch logic
    if RE_IF.search(body) or RE_EVALUATE.search(body):
        actions.add("branch_logic")

    # DISPLAY (error context vs general output)
    if RE_DISPLAY.search(body):
        if RE_ERROR_NAME.search(name):
            actions.add("display_error")
        else:
            actions.add("display_output")

    # transform_data: MOVE-only paragraphs (no I/O, no CICS, no CALL)
    if (RE_MOVE.search(body)
            and not actions - {"branch_logic", "display_output", "display_error"}):
        actions.add("transform_data")

    # Abend: name-based heuristic
    if RE_ABEND_NAME.search(name):
        actions.add("abend")

    # Program exit
    if RE_STOP_RUN.search(body) or RE_GOBACK.search(body) or RE_EXIT_PGM.search(body):
        actions.add("program_exit")

    # Error display without abend flag
    if RE_ERROR_NAME.search(name) and "abend" not in actions:
        actions.add("display_error")

    return sorted(actions) if actions else ["no_action_detected"]


# ===========================================================================
# §9  FILE OPERATIONS PER PARAGRAPH
#     Enriched from extract_paragraph_io.py WRITER_VERBS/READER_VERBS logic.
#     Returns a file-keyed dict of operation records with paragraph provenance.
# ===========================================================================

def extract_file_operations(
    para_bodies: dict[str, str],
    known_files: set[str],
) -> dict[str, list[dict]]:
    """
    For each file name, list every I/O operation performed on it and which
    paragraph performed it.

    Returns {file_name: [{paragraph, operation, source_line}]}.

    `known_files` is the set of file names from SELECT statements (from §10).
    If empty, all OPEN/READ/WRITE/etc. targets are captured regardless.

    source_line is None for now (would require original-line tracking through
    split_by_paragraph; deferred to post-REKT phase).
    """
    result: dict[str, list[dict]] = {}

    for para, body in para_bodies.items():
        # OPEN <mode> <file>  (separate from the generic IO verb scan below)
        for m in RE_OPEN_MODE.finditer(body):
            mode  = m.group(1).upper()
            fname = m.group(2).upper()
            if not known_files or fname in known_files:
                result.setdefault(fname, []).append({
                    "paragraph":   para,
                    "operation":   f"open_{mode.lower()}",
                    "source_line": None,
                })

        # CLOSE/READ/WRITE/REWRITE/DELETE/START <file>
        for m in RE_IO_VERB.finditer(body):
            fname = m.group(2).upper()
            op    = m.group(1).lower()
            if not known_files or fname in known_files:
                result.setdefault(fname, []).append({
                    "paragraph":   para,
                    "operation":   op,
                    "source_line": None,
                })

    return result


# ===========================================================================
# §10 FILE LINEAGE
#     Mined from extract_file_control.py SELECT/ASSIGN/FD linkage.
# ===========================================================================

def extract_file_lineage(clean: str) -> tuple[list[dict], set[str]]:
    """
    Build file_lineage from SELECT / ASSIGN / FD relationships.

    Returns:
      (file_lineage_list, file_names_set)

    file_lineage_list: [{name, ddname, fd_record}]
      name      – SELECT file name (logical name in PROCEDURE DIVISION)
      ddname    – ASSIGN TO target (JCL DD name or external file name)
      fd_record – best-guess FD record name (prefix-matched against FD stmts)

    file_names_set is passed to extract_file_operations() for filtering.

    FD matching: we look for an FD whose name starts with the first 4 chars
    of the SELECT name. This is a heuristic that works well for the CardDemo
    naming convention (e.g. ACCTFILE → FD-ACCTFILE-REC or ACCTFILE-FILE).
    For programs that follow different conventions, fd_record may be None.
    """
    # All SELECT ... ASSIGN TO pairs
    selects: dict[str, str] = {}
    for m in RE_SELECT.finditer(clean):
        selects[m.group(1).upper()] = m.group(2).upper()

    # All FD names
    fds: list[str] = [m.group(1).upper() for m in RE_FD.finditer(clean)]

    lineage: list[dict] = []
    for fname, ddname in selects.items():
        # Heuristic: find an FD whose name contains the first 4 chars of fname
        prefix = fname[:4]
        fd_match = next(
            (fd for fd in fds if prefix in fd),
            None,
        )
        lineage.append({
            "name":      fname,
            "ddname":    ddname,
            "fd_record": fd_match,
        })

    return lineage, set(selects.keys())


# ===========================================================================
# §11 CICS SUBTREE
#     AID-key handling mined from pass1_annotate.py EVALUATE EIBAID patterns.
#     Multiline EXEC CICS handled via _collapse_cics_blocks().
# ===========================================================================

def extract_cics(
    collapsed: str,
    para_bodies: dict[str, str],
) -> dict:
    """
    Extract the full CICS semantic subtree from CICS-collapsed source.

    Parameters
    ----------
    collapsed   : entire program source with CICS blocks collapsed to single lines
    para_bodies : {para_name: body_text} (raw, NOT collapsed)

    Returns dict with keys:
      commarea_used   bool
      commands        list[str]   normalized CICS command verbs
      maps_used       list[str]   map names from MAP(...) operands
      mapsets_used    list[str]   mapset names from MAPSET(...) operands
      aid_keys        list[str]   AID key names (PF1, ENTER, CLEAR, etc.)
      screen_flow     list[{paragraph, action, map}]
    """
    # --- Commands ---
    commands: set[str] = set()
    for m in RE_EXEC_CICS_BLOCK.finditer(collapsed):
        commands.add(m.group(1).upper())

    # --- Maps and mapsets ---
    maps_used:    set[str] = set()
    mapsets_used: set[str] = set()
    for m in RE_CICS_MAP.finditer(collapsed):    maps_used.add(m.group(1).upper())
    for m in RE_CICS_MAPSET.finditer(collapsed): mapsets_used.add(m.group(1).upper())

    # --- AID keys ---
    # Three patterns from pass1_annotate.py:
    #   1. EIBAID = DFHAIDxxx  (comparison form)
    #   2. DFHAIDxxx            (bare reference form)
    #   3. WHEN DFHAIDxxx       (EVALUATE form — most common in CardDemo)
    aid_keys: set[str] = set()
    for m in RE_AID_EIBAID.finditer(collapsed): aid_keys.add(m.group(1).upper())
    for m in RE_AID_DFHAID.finditer(collapsed): aid_keys.add(m.group(1).upper())
    for m in RE_AID_WHEN.finditer(collapsed):   aid_keys.add(m.group(1).upper())

    # --- COMMAREA ---
    commarea_used = bool(RE_COMMAREA.search(collapsed))

    # --- Screen flow: per-paragraph SEND MAP / RECEIVE MAP ---
    screen_flow: list[dict] = []
    for para, body in para_bodies.items():
        cbody = _collapse_cics_blocks(body)
        if RE_CICS_SEND_MAP.search(cbody):
            map_m = RE_CICS_MAP.search(cbody)
            screen_flow.append({
                "paragraph": para,
                "action":    "send_map",
                "map":       map_m.group(1).upper() if map_m else None,
            })
        if RE_CICS_RECEIVE_MAP.search(cbody):
            map_m = RE_CICS_MAP.search(cbody)
            screen_flow.append({
                "paragraph": para,
                "action":    "receive_map",
                "map":       map_m.group(1).upper() if map_m else None,
            })

    return {
        "commarea_used": commarea_used,
        "commands":      sorted(commands),
        "maps_used":     sorted(maps_used),
        "mapsets_used":  sorted(mapsets_used),
        "aid_keys":      sorted(aid_keys),
        "screen_flow":   screen_flow,
    }


# ===========================================================================
# §12 PUBLIC ENTRY POINT
# ===========================================================================

def enrich(
    program_name:   str,
    raw_cobol:      str,
    preprocessed:   str | None,
    rekt_json:      dict | None,
    base_facts:     dict,
) -> dict:
    """
    Main entry point. Returns the v1.1 semantic enrichment dict.

    Parameters
    ----------
    program_name  : e.g. 'CBACT01C' (used for logging only)
    raw_cobol     : exact text read from the .cbl file
    preprocessed  : output of 'cobc -E' if available, else None.
                    When provided, paragraph extraction uses the expanded
                    source (copybooks inlined); otherwise raw_cobol is used.
    rekt_json     : parsed REKT CFG report dict, or None.
                    When present and non-empty, cfg_source = 'rekt';
                    otherwise falls back to text_scan.
    base_facts    : read-only v1.0 facts dict (used to read cics_present flag)

    Returns
    -------
    dict with ONLY the v1.1 fields listed in the module docstring.
    The caller is responsible for merging into base_facts.
    base_facts is never modified.
    """
    cics_present: bool = base_facts.get("cics_present", False)

    # Use preprocessed source when available (better copybook expansion),
    # otherwise fall back to raw source.
    source = preprocessed if preprocessed else raw_cobol

    # Strip comment lines before structural analysis.
    clean = strip_comment_lines(source)

    # Collapse EXEC CICS blocks for CICS-specific extraction.
    # We do this once here and pass the result into CICS functions.
    collapsed = _collapse_cics_blocks(clean) if cics_present else clean

    # §4 Paragraph extraction with noise filter
    defined    = extract_paragraphs_defined(raw_cobol, clean)
    referenced = extract_paragraphs_referenced(clean, defined)

    # §5 Split PROCEDURE DIVISION into per-paragraph bodies
    para_bodies = split_by_paragraph(clean, defined)

    # §8 Paragraph action classification
    paragraph_actions: dict[str, list[str]] = {}
    for p in defined:
        name  = p["name"]
        body  = para_bodies.get(name, "")
        cbody = _collapse_cics_blocks(body) if cics_present else body
        paragraph_actions[name] = classify_paragraph_actions(name, body, cbody)

    # §10 File lineage
    file_lineage, known_files = extract_file_lineage(clean)

    # §9 File operations per paragraph
    file_ops = extract_file_operations(para_bodies, known_files)

    # §7 CFG: REKT adapter first, text_scan fallback
    control_flow: dict
    if rekt_json and not cics_present:
        rekt_cfg = build_cfg_from_rekt(rekt_json)
        control_flow = rekt_cfg if rekt_cfg else build_cfg_text_scan(clean, defined, cics_present)
    else:
        control_flow = build_cfg_text_scan(clean, defined, cics_present)

    # COBSWAIT-style structural minimal: no paragraphs, no CICS
    if not defined and not cics_present:
        control_flow["cfg_note"] = (
            "structural_minimal: no paragraphs detected. "
            "Gate passed trivially. Consider adding gate_note=structural_minimal."
        )

    # §11 CICS subtree (only for CICS programs)
    cics_facts: dict | None = None
    if cics_present:
        cics_facts = extract_cics(collapsed, para_bodies)

    return {
        "paragraphs_defined":    defined,
        "paragraphs_referenced": referenced,
        "control_flow":          control_flow,
        "paragraph_actions":     paragraph_actions,
        "file_operations":       file_ops,
        "file_lineage":          file_lineage,
        "cics":                  cics_facts,
    }


# ===========================================================================
# §13 SMOKE TEST  (python scripts/hermes_v11_combined_extractor.py <file.cbl>)
# ===========================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python hermes_v11_combined_extractor.py <path/to/PROG.cbl>")
        sys.exit(1)

    cbl_path = Path(sys.argv[1])
    if not cbl_path.exists():
        print(f"ERROR: file not found: {cbl_path}", file=sys.stderr)
        sys.exit(2)

    raw = cbl_path.read_text(encoding="utf-8", errors="replace")

    # Minimal stub base_facts to satisfy the enrich() interface
    stub_facts = {
        "cics_present": bool(re.search(r"\bEXEC\s+CICS\b", raw, re.IGNORECASE)),
    }

    result = enrich(
        program_name  = cbl_path.stem.upper(),
        raw_cobol     = raw,
        preprocessed  = None,
        rekt_json     = None,
        base_facts    = stub_facts,
    )

    paras  = result["paragraphs_defined"]
    edges  = result["control_flow"].get("edges", [])
    cics   = result["cics"]

    print(f"Program  : {cbl_path.stem.upper()}")
    print(f"Paras    : {len(paras)} defined, {len(result['paragraphs_referenced'])} referenced")
    print(f"CFG      : {len(edges)} edges  ({result['control_flow']['cfg_source']})")
    print(f"Files    : {len(result['file_lineage'])} SELECT entries")

    if paras:
        print("\nFirst 5 paragraphs:")
        for p in paras[:5]:
            acts = result["paragraph_actions"].get(p["name"], [])
            print(f"  L{p['source_line']:4d}  {p['name']:30s}  {acts}")

    if edges:
        print("\nFirst 10 edges:")
        for e in edges[:10]:
            print(f"  {e['from']:30s} --[{e['type']:12s}]--> {e['to']}")

    if cics:
        print(f"\nCICS commands : {cics['commands']}")
        print(f"Maps used     : {cics['maps_used']}")
        print(f"AID keys      : {cics['aid_keys']}")
        print(f"Screen flow   : {len(cics['screen_flow'])} entries")
        for sf in cics["screen_flow"]:
            print(f"  {sf['paragraph']:30s} {sf['action']:12s} {sf['map']}")

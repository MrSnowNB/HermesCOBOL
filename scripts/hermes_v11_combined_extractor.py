#!/usr/bin/env python3
# LLM-FREE — Deterministic COBOL semantic extraction. No LLM inference.
"""
hermes_v11_combined_extractor.py
================================
HermesCOBOL schema v1.1 semantic enrichment module.

This script is the *single authoritative source* for all v1.1 fields added
to the HermesCOBOL facts JSON. It is intentionally self-contained (stdlib
only) and invocable both as a library (via ``enrich()``) and as a CLI smoke
test.

Relationship to prior CardDemo scripts
---------------------------------------
Logic is mined and simplified from four CardDemo analysis scripts:

  extract_cfg_local.py      -> paragraph graph, reachability, PERFORM/GOTO,
                               CICS command scan, entry/exit detection
  extract_fallthrough.py    -> fallthrough edge detection (last-verb approach
                               adapted to text-scan without pass1 annotations)
  extract_paragraph_io.py   -> file verb classification per paragraph,
                               paragraph_actions taxonomy
  extract_file_control.py   -> SELECT/ASSIGN/FD linkage -> file_lineage

All of those scripts required pre-built annotation JSON (pass1_annotate.py
pipeline).  This module operates directly on raw COBOL text so it can run
in Stage 1 before any preprocessing pipeline exists.

CFG fidelity notes
-------------------
- ``cfg_source = "rekt"``       Highest fidelity: populated from smojol/REKT
                                JSON when available (non-CICS only).
- ``cfg_source = "text_scan"``  Lower fidelity: PERFORM graph + fallthrough
                                derived from raw text.  Used for CICS programs
                                and any program where REKT JSON is absent.
  For text_scan the following limitations apply:
    * conditional_true / conditional_false edges are not resolved
      (we emit ``branch_logic`` action but a single ``perform`` edge)
    * PERFORM VARYING / UNTIL loops emit a single ``perform`` edge with
      no loop-count information
    * EXEC CICS XCTL / LINK targets are not followed as call edges

Schema v1.1 additions returned by enrich()
-------------------------------------------
  paragraphs_defined    list[{name, source_line, area_a}]
  paragraphs_referenced list[str]
  paragraph_actions     dict[str, list[str]]
  file_lineage          list[{name, ddname, fd_record}]
  file_operations       dict[str, list[{paragraph, operation, source_line}]]
  control_flow          {cfg_source, entry_points, exit_points, edges, unresolved}
  cics                  {commarea_used, commands, maps_used, mapsets_used,
                         aid_keys, screen_flow}  -- None for non-CICS programs

All v1.0 fields are unchanged by this module.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

__LLM_FREE__ = True


# ===========================================================================
# 1.  CONSTANTS
# ===========================================================================

# Parser-noise pseudo-paragraphs that appear because the paragraph regex
# matches any Area-A label-like token.  These are compiler delimiters, scope
# terminators, or reserved words -- never real paragraph names.
PARAGRAPH_NOISE = frozenset([
    "END-IF", "END-PERFORM", "END-EVALUATE", "END-READ",
    "END-WRITE", "END-REWRITE", "END-DELETE", "END-START",
    "END-CALL", "END-STRING", "END-UNSTRING", "END-EXEC",
    "EXIT", "CONTINUE", "GOBACK", "STOP",
    "FILE-CONTROL", "I-O-CONTROL", "PROGRAM-ID",
])

# Division / section header keywords that are never paragraph labels.
RESERVED_DIVISIONS = frozenset([
    "IDENTIFICATION", "ENVIRONMENT", "DATA", "PROCEDURE",
    "CONFIGURATION", "INPUT-OUTPUT", "FILE", "WORKING-STORAGE",
    "LINKAGE", "LOCAL-STORAGE", "REPORT", "SCREEN",
    "AUTHOR", "INSTALLATION", "DATE-WRITTEN", "DATE-COMPILED",
    "SECURITY", "REMARKS", "FD", "SD", "RD",
])

# PERFORM modifier keywords that follow PERFORM but are NOT paragraph targets.
# e.g.  PERFORM UNTIL WS-EOF  -- "UNTIL" must not be treated as a para name.
PERFORM_NON_TARGETS = frozenset([
    "UNTIL", "VARYING", "TIMES", "WITH", "TEST",
    "THRU", "THROUGH", "BEFORE", "AFTER",
])

# CICS command verbs that constitute a program terminator (per
# extract_fallthrough.py CICS_TERMINATOR_OPS).  Used to detect exit_points.
CICS_TERMINATOR_OPS = frozenset(["RETURN", "XCTL"])

# Valid AID token length range (inclusive).
# DFH tokens shorter than 4 or longer than 10 chars are noise:
#   too short: e.g. bare 'DFH' prefix match artefacts
#   too long:  e.g. internal data-name false positives
_AID_MIN_LEN = 4
_AID_MAX_LEN = 10


# ===========================================================================
# 2.  REGEX LIBRARY
#     All regexes are compiled at module load (fast) and documented inline.
# ===========================================================================

# --- structural markers ---

# PROCEDURE DIVISION header (marks start of executable code)
RE_PROC_DIV   = re.compile(r"^[ \t]*PROCEDURE[ \t]+DIVISION", re.M | re.I)
# DATA DIVISION header (marks start of data declarations)
RE_DATA_DIV   = re.compile(r"^[ \t]*DATA[ \t]+DIVISION",      re.M | re.I)

# A paragraph/section label in Area A: 0-11 spaces, identifier, dot, EOL.
# This is the canonical form after fixed-format column stripping.
RE_PARA_LABEL = re.compile(
    r"^([ ]{0,11})([A-Z0-9][A-Z0-9-]*)[ \t]*\.[ \t]*$",
    re.M | re.I,
)
# SECTION declaration (name + SECTION + dot).  Used to exclude section names
# from the paragraph list.
RE_SECTION    = re.compile(
    r"^[ ]{0,11}([A-Z0-9][A-Z0-9-]*)[ \t]+SECTION[ \t]*\.[ \t]*$",
    re.M | re.I,
)

# --- flow control verbs ---

# PERFORM <para>  (simple, no modifier)
RE_PERFORM_SIMPLE  = re.compile(
    r"\bPERFORM[ \t]+([A-Z0-9][A-Z0-9-]+)[ \t]*$",
    re.M | re.I,
)
# PERFORM <para> THRU <para>  -- both ends emit a perform_thru edge
RE_PERFORM_THRU    = re.compile(
    r"\bPERFORM[ \t]+([A-Z0-9][A-Z0-9-]+)[ \t]+THRU[ \t]+([A-Z0-9][A-Z0-9-]+)",
    re.I,
)
# PERFORM <para> UNTIL / VARYING  (loop forms -- lower fidelity)
RE_PERFORM_LOOP    = re.compile(
    r"\bPERFORM[ \t]+([A-Z0-9][A-Z0-9-]+)[ \t]+(?:UNTIL|VARYING)",
    re.I,
)
# GO TO <para>
RE_GOTO            = re.compile(r"\bGO[ \t]+TO[ \t]+([A-Z0-9][A-Z0-9-]+)", re.I)
# CALL '<literal-name>'
RE_CALL            = re.compile(r"\bCALL[ \t]+['\"]([A-Z0-9][A-Z0-9-]*)['\"] ", re.I)
# Program terminators
RE_STOP_RUN        = re.compile(r"\bSTOP[ \t]+RUN\b",   re.I)
RE_GOBACK          = re.compile(r"\bGOBACK\b",          re.I)
RE_EXIT_PROGRAM    = re.compile(r"\bEXIT[ \t]+PROGRAM\b", re.I)

# --- file I/O verbs ---

# OPEN INPUT/OUTPUT/I-O/EXTEND <file>  (captures the mode and file name)
RE_OPEN_MODE  = re.compile(
    r"\bOPEN[ \t]+(INPUT|OUTPUT|I-O|EXTEND)[ \t]+([A-Z0-9][A-Z0-9-]*)",
    re.I,
)
# READ / WRITE / REWRITE / DELETE / START / CLOSE <file>
# Note: OPEN handled separately because mode matters.
RE_IO_VERB    = re.compile(
    r"\b(READ|WRITE|REWRITE|DELETE|START|CLOSE)[ \t]+([A-Z0-9][A-Z0-9-]*)",
    re.I,
)
# SELECT <file> ASSIGN TO <ddname>
RE_SELECT     = re.compile(
    r"\bSELECT[ \t]+([A-Z0-9][A-Z0-9-]*)[ \t]+ASSIGN[ \t]+TO[ \t]+([A-Z0-9][A-Z0-9-]*)",
    re.I,
)
# FD <record-name>  (file descriptor in FILE SECTION)
RE_FD         = re.compile(r"^[ \t]*FD[ \t]+([A-Z0-9][A-Z0-9-]*)", re.M | re.I)
# COPY <copybook>
RE_COPY       = re.compile(r"\bCOPY[ \t]+([A-Z0-9][A-Z0-9-]*)", re.I)

# --- CICS patterns ---

# Any EXEC CICS block start
RE_EXEC_CICS_START = re.compile(r"\bEXEC[ \t]+CICS\b", re.I)
# Normalised: first command keyword after EXEC CICS on collapsed block
RE_EXEC_CICS_CMD   = re.compile(r"\bEXEC[ \t]+CICS[ \t]+([A-Z][A-Z0-9-]*)", re.I)
# MAP(<name>) clause inside EXEC CICS SEND/RECEIVE MAP
RE_CICS_MAP        = re.compile(
    r"\bMAP[ \t]*\([ \t]*['\"]?([A-Z0-9][A-Z0-9-]*)['\"]?[ \t]*\)", re.I
)
# MAPSET(<name>) clause
RE_CICS_MAPSET     = re.compile(
    r"\bMAPSET[ \t]*\([ \t]*['\"]?([A-Z0-9][A-Z0-9-]*)['\"]?[ \t]*\)", re.I
)
# EXEC CICS SEND MAP  (specific sub-type of SEND)
RE_CICS_SEND_MAP   = re.compile(r"\bEXEC[ \t]+CICS[ \t]+SEND[ \t]+MAP\b", re.I)
# EXEC CICS RECEIVE MAP
RE_CICS_RECV_MAP   = re.compile(r"\bEXEC[ \t]+CICS[ \t]+RECEIVE[ \t]+MAP\b", re.I)

# --- AID key matchers ---
# Three complementary matchers cover the full CardDemo AID-key vocabulary.
#
# Primary (dominant CardDemo pattern):
#   EVALUATE EIBAID
#       WHEN DFHENTER   PERFORM ...
#       WHEN DFHPF3     PERFORM ...
#   END-EVALUATE
# The block scanner RE_EVAL_EIBAID_START + RE_WHEN_DFH (see Section 9)
# handles this case by scanning forward to END-EVALUATE.
RE_EVAL_EIBAID_START = re.compile(r"\bEVALUATE[ \t]+EIBAID\b", re.I)
RE_WHEN_DFH          = re.compile(r"\bWHEN[ \t]+(DFH[A-Z0-9]+)\b", re.I)

# Secondary:
#   IF EIBAID = DFHPF3 / IF EIBAID NOT = DFHENTER
# Note: does NOT require DFHAID. prefix -- matches the bare constant form
# that is most common in CardDemo.
RE_IF_EIBAID = re.compile(
    r"\bEIBAID[ \t]*(?:NOT[ \t]*)?=[ \t]*(DFH[A-Z0-9]+)\b",
    re.I,
)

# Fallback (legacy form with DFHAID. prefix):
#   EIBAID = DFHAID.PF3   or   DFHAID.PF3
# These appear in some IBM sample programs; retained as a secondary path.
RE_EIBAID_EQ  = re.compile(
    r"EIBAID[ \t]*=[ \t]*DFHAID[ \t]*\.?([A-Z0-9]+)", re.I
)
RE_DFHAID_DOT = re.compile(r"\bDFHAID\.([A-Z0-9]+)\b", re.I)

# DFHCOMMAREA present in source
RE_COMMAREA        = re.compile(r"\bDFHCOMMAREA\b", re.I)
# EXEC SQL (flag only, no deep extraction at this stage)
RE_EXEC_SQL        = re.compile(r"\bEXEC[ \t]+SQL\b", re.I)

# --- action classifiers ---
# These are applied to the *body* of each paragraph (the lines between two
# paragraph labels) to produce a coarse action tag list.
RE_ACT_DISPLAY   = re.compile(r"\bDISPLAY\b",   re.I)
RE_ACT_MOVE      = re.compile(r"\bMOVE\b",      re.I)
RE_ACT_IF        = re.compile(r"\bIF\b",         re.I)
RE_ACT_EVALUATE  = re.compile(r"\bEVALUATE\b",  re.I)
# Name patterns that identify abend / error paragraphs
RE_ABEND_NAME    = re.compile(r"(ABEND|9999|ABORT|STORUN)", re.I)
RE_ERROR_NAME    = re.compile(r"(ERROR|STATUS|STAT|INVALID|EXCEPT)", re.I)


# ===========================================================================
# 2b. AID KEY UTILITIES
# ===========================================================================

def _is_valid_aid_token(token: str) -> bool:
    """
    Return True iff *token* looks like a real DFHAID constant.

    Rules:
      * Must start with 'DFH' (callers already ensure this via regex group)
      * Total length 4-10 characters (inclusive)
        - min 4: DFHx (e.g. DFHPF1 is 6, but DFHPA1 is 6 -- shortest real
          constants are DFHPA1=6, DFHPF1=6; but we accept 4 to be safe)
        - max 10: DFHMSRE=7, DFHOPID=7 -- nothing legitimate exceeds 10
    """
    return _AID_MIN_LEN <= len(token) <= _AID_MAX_LEN


def _extract_aid_keys_from_text(text: str) -> set[str]:
    """
    Extract all AID key constants from *text* using the three matcher strategy.

    Operates on the procedure body text (not the EXEC-CICS-collapsed form,
    because EVALUATE EIBAID blocks live outside EXEC CICS statements).

    Returns a set of upper-cased DFHxxx constants that pass the length filter.

    Matcher priority (all feed the same output set):
      1. EVALUATE EIBAID block scanner  -- dominant CardDemo pattern
      2. IF EIBAID = DFHxxx             -- conditional comparison form
      3. EIBAID = DFHAID.xxx / DFHAID.x -- legacy dotted form (fallback)
    """
    keys: set[str] = set()
    lines = text.splitlines()

    # --- Matcher 1: EVALUATE EIBAID block scanner ---
    # Scan the text line-by-line.  When we encounter EVALUATE EIBAID, enter
    # a block-collection mode and gather every WHEN DFHxxx until END-EVALUATE.
    # This handles the dominant pattern used by all CardDemo CICS programs.
    in_eval_eibaid = False
    for line in lines:
        # Skip COBOL comment lines (col 7 indicator)
        if len(line) >= 7 and line[6] in ("*", "/"):
            continue
        upper = line.upper()
        if not in_eval_eibaid:
            if RE_EVAL_EIBAID_START.search(line):
                in_eval_eibaid = True
                # The EVALUATE line itself won't contain WHEN DFH, but start
                # scanning immediately in case it is a single-line form.
        if in_eval_eibaid:
            # Collect every WHEN DFHxxx on this line
            for m in RE_WHEN_DFH.finditer(line):
                tok = m.group(1).upper()
                if _is_valid_aid_token(tok):
                    keys.add(tok)
            # Exit block on END-EVALUATE
            if "END-EVALUATE" in upper and RE_EVAL_EIBAID_START.search(line) is None:
                in_eval_eibaid = False

    # --- Matcher 2: IF EIBAID = DFHxxx  /  IF EIBAID NOT = DFHxxx ---
    for m in RE_IF_EIBAID.finditer(text):
        tok = m.group(1).upper()
        if _is_valid_aid_token(tok):
            keys.add(tok)

    # --- Matcher 3: legacy DFHAID. prefix forms (fallback) ---
    for m in RE_EIBAID_EQ.finditer(text):
        tok = m.group(1).upper()
        # Reconstruct full token for length check: the captured group is
        # only the suffix after DFHAID., so prepend DFH for the check.
        full = "DFH" + tok
        if _is_valid_aid_token(full):
            keys.add(full)
    for m in RE_DFHAID_DOT.finditer(text):
        tok = m.group(1).upper()
        full = "DFH" + tok
        if _is_valid_aid_token(full):
            keys.add(full)

    return keys


# ===========================================================================
# 3.  TEXT PREPARATION UTILITIES
# ===========================================================================

def strip_fixed_format_comments(text: str) -> str:
    """
    Remove COBOL fixed-format comment lines.

    In standard fixed-format COBOL, a line whose indicator column (col 7,
    0-based index 6) contains '*' or '/' is a comment.  This function blanks
    such lines so that downstream regexes do not accidentally match content
    inside comments.

    NOTE: Lines shorter than 7 characters are left unchanged (they cannot
    have an indicator column).
    """
    out: list[str] = []
    for line in text.splitlines():
        if len(line) >= 7 and line[6] in ("*", "/"):
            out.append("")          # preserve line-number alignment
        else:
            out.append(line)
    return "\n".join(out)


def collapse_exec_cics_blocks(text: str) -> str:
    """
    Collapse multi-line EXEC CICS ... END-EXEC blocks into a single logical
    line.

    COBOL EXEC CICS blocks routinely span many continuation lines, which means
    a naive single-line regex will only capture the command keyword when it
    happens to sit on the same line as 'EXEC CICS'.  This function joins the
    content of each block (stripping the column-6 sequence/indicator area)
    into one space-separated string, making single-line regexes reliable.

    Strategy (adapted from CardDemo pass1_annotate.py multiline handling):
      1. Find the EXEC CICS marker.
      2. Accumulate continuation lines until END-EXEC.
      3. Replace the block with a single normalised line in-place.

    Fixed-format rules applied:
      * Columns 1-6  (0-5): sequence number -- ignored
      * Column  7    (6):   indicator -- '*' or '/' -> skip line
      * Columns 8-72 (7-71): Area A + Area B -- the actual code
      * Columns 73+  (72+): identification area -- ignored
    """
    lines   = text.splitlines()
    result  = []
    i       = 0
    while i < len(lines):
        raw_line = lines[i]
        # Strip comment and identification area for the check
        if len(raw_line) >= 7 and raw_line[6] in ("*", "/"):
            result.append(raw_line)
            i += 1
            continue
        area = raw_line[7:72] if len(raw_line) > 7 else raw_line
        if RE_EXEC_CICS_START.search(area):
            # Start accumulating the block
            block_tokens: list[str] = [area.strip()]
            i += 1
            while i < len(lines):
                cont = lines[i]
                if len(cont) >= 7 and cont[6] in ("*", "/"):
                    i += 1
                    continue
                cont_area = cont[7:72] if len(cont) > 7 else cont
                block_tokens.append(cont_area.strip())
                if "END-EXEC" in cont_area.upper():
                    i += 1
                    break
                i += 1
            # Emit the entire block as one line (preserving original indentation
            # for column-position accounting is unnecessary here -- we only
            # care about extracting keywords, not source positions).
            result.append(" ".join(block_tokens))
        else:
            result.append(raw_line)
            i += 1
    return "\n".join(result)


# ===========================================================================
# 4.  PARAGRAPH EXTRACTION
# ===========================================================================

def extract_paragraphs_defined(raw: str, clean: str) -> list[dict]:
    """
    Return all real paragraph labels defined in the PROCEDURE DIVISION.

    Each entry: {"name": str, "source_line": int, "area_a": bool}
      name        : upper-cased paragraph name
      source_line : 1-based line number in *raw* source (for provenance)
      area_a      : True if the label starts in Area A (indent <= 3 spaces)
                    which is the standard placement for paragraph labels

    Filters applied (adapted from extract_cfg_local.extract_paragraphs):
      * PARAGRAPH_NOISE        : scope terminators, reserved verbs
      * RESERVED_DIVISIONS     : division / section keyword names
      * Names ending -DIVISION  : e.g. DATA-DIVISION appearing as a token
      * Section names (SECTION keyword immediately following)

    Uses *clean* (comment-stripped) for matching but *raw* for line numbers
    so that provenance references the actual source file.
    """
    # Collect all SECTION names so we can exclude them from the para list
    section_names: set[str] = {
        m.group(1).upper() for m in RE_SECTION.finditer(clean)
    }

    results : list[dict] = []
    seen    : set[str]   = set()

    for m in RE_PARA_LABEL.finditer(clean):
        name   = m.group(2).upper()
        indent = len(m.group(1))          # leading spaces

        # Apply noise / reserved-word filters
        if name in PARAGRAPH_NOISE:      continue
        if name in RESERVED_DIVISIONS:   continue
        if name.endswith("-DIVISION"):   continue
        if name in section_names:        continue
        if name in seen:                 continue   # keep first occurrence only

        seen.add(name)
        lineno = raw[:m.start()].count("\n") + 1
        results.append({
            "name":        name,
            "source_line": lineno,
            "area_a":      indent <= 3,
        })
    return results


def extract_paragraphs_referenced(
    clean: str, defined: list[dict]
) -> list[str]:
    """
    Return names of defined paragraphs that appear as PERFORM / GO TO targets.

    This is the *referenced* set -- the complement of *defined* allows
    detection of unreachable paragraphs (defined but never referenced).
    """
    defined_names = {p["name"] for p in defined}
    referenced: set[str] = set()

    for m in re.finditer(r"\bPERFORM[ \t]+([A-Z0-9][A-Z0-9-]+)", clean, re.I):
        t = m.group(1).upper()
        if t in defined_names and t not in PERFORM_NON_TARGETS:
            referenced.add(t)

    for m in RE_GOTO.finditer(clean):
        t = m.group(1).upper()
        if t in defined_names:
            referenced.add(t)

    return sorted(referenced)


# ===========================================================================
# 5.  PROCEDURE DIVISION BODY SPLITTER
#     Splits source into a mapping of {paragraph_name: body_text} for
#     per-paragraph analysis.
# ===========================================================================

def split_procedure_bodies(clean: str) -> dict[str, str]:
    """
    Return {para_name: body_lines_str} for every paragraph in the PROCEDURE
    DIVISION.

    'Body' is the text between a paragraph label and the next label
    (exclusive of both labels).  Section headers are treated as paragraph
    separators.

    The splitter does NOT require knowledge of *which* paragraphs are real --
    it uses the same label regex as extract_paragraphs_defined so the bodies
    align with the defined-paragraph list.
    """
    proc_m = RE_PROC_DIV.search(clean)
    if not proc_m:
        return {}

    proc_lines = clean[proc_m.end():].splitlines()
    para_map: dict[str, list[str]] = {}
    current: str | None = None

    label_re = re.compile(
        r"^([ ]{0,11})([A-Z0-9][A-Z0-9-]*)[ \t]*\.[ \t]*$",
        re.I,
    )
    for line in proc_lines:
        m = label_re.match(line)
        if m:
            name = m.group(2).upper()
            # Skip noise tokens -- do not start a new paragraph bucket for them
            if name in PARAGRAPH_NOISE or name.endswith("-DIVISION"):
                if current is not None:
                    para_map[current].append(line)
                continue
            current = name
            para_map.setdefault(current, [])
        else:
            if current is not None:
                para_map[current].append(line)

    return {k: "\n".join(v) for k, v in para_map.items()}


# ===========================================================================
# 6.  PARAGRAPH ACTION CLASSIFIER
#     Adapted from CardDemo extract_paragraph_io.py verb taxonomy and
#     the HermesCOBOL action vocabulary defined in the spec.
# ===========================================================================

# Mapping from COBOL I/O verb (upper-cased) to action tag
_FILE_VERB_TO_ACTION: dict[str, str] = {
    "READ":    "read_file",
    "WRITE":   "write_file",
    "REWRITE": "rewrite_file",
    "DELETE":  "delete_record",
    "START":   "start_browse",
    "OPEN":    "open_file",
    "CLOSE":   "close_file",
}


def classify_paragraph_actions(name: str, body: str) -> list[str]:
    """
    Return a sorted, deduplicated list of action tags for a paragraph.

    Tags are derived *deterministically* from verb presence in the paragraph
    body -- no probabilistic inference.  The action vocabulary matches the
    HermesCOBOL v1.1 spec:

      open_file, close_file, read_file, write_file, rewrite_file,
      delete_record, start_browse, call_program,
      cics_command, send_map, receive_map, aid_branch,
      branch_logic, abend, program_exit, display_error, display_output,
      transform_data, no_action_detected

    The paragraph *name* is used for abend / error heuristics (adapted from
    CardDemo extract_cfg_local.py dead-code detection heuristics).

    aid_branch is added when the paragraph body contains an EVALUATE EIBAID
    block -- this is the primary AID-driven dispatch pattern in CardDemo CICS
    programs.  It is separate from branch_logic so downstream consumers can
    identify AID-conditioned branches without scanning cics.aid_keys.
    """
    # Use the collapsed version so multi-line EXEC CICS is seen as one unit
    collapsed = collapse_exec_cics_blocks(body)
    actions: set[str] = set()

    # --- File I/O verbs ---
    for m in RE_OPEN_MODE.finditer(collapsed):
        actions.add("open_file")
    for m in RE_IO_VERB.finditer(collapsed):
        verb = m.group(1).upper()
        tag  = _FILE_VERB_TO_ACTION.get(verb)
        if tag:
            actions.add(tag)

    # --- CALL ---
    if RE_CALL.search(collapsed):
        actions.add("call_program")

    # --- CICS ---
    if RE_EXEC_CICS_START.search(collapsed):
        actions.add("cics_command")
        if RE_CICS_SEND_MAP.search(collapsed):
            actions.add("send_map")
        if RE_CICS_RECV_MAP.search(collapsed):
            actions.add("receive_map")

    # --- AID branch: EVALUATE EIBAID present in paragraph body ---
    # Uses the raw body (not collapsed) because EVALUATE EIBAID is never
    # inside an EXEC CICS block -- it is standard COBOL conditional logic.
    if RE_EVAL_EIBAID_START.search(body):
        actions.add("aid_branch")
        actions.add("branch_logic")   # aid_branch implies branch_logic

    # --- IF EIBAID comparison form also implies aid_branch ---
    if RE_IF_EIBAID.search(body):
        actions.add("aid_branch")
        actions.add("branch_logic")

    # --- DISPLAY ---
    if RE_ACT_DISPLAY.search(collapsed):
        # Distinguish error display (paragraph name heuristic) from generic
        actions.add("display_error" if RE_ERROR_NAME.search(name) else "display_output")

    # --- Branch logic (non-AID) ---
    if RE_ACT_IF.search(collapsed) or RE_ACT_EVALUATE.search(collapsed):
        actions.add("branch_logic")

    # --- Transform data: MOVE with no I/O and no calls ---
    io_tags = {
        "open_file", "close_file", "read_file", "write_file",
        "rewrite_file", "delete_record", "start_browse",
        "call_program", "cics_command",
    }
    if RE_ACT_MOVE.search(collapsed) and not (actions & io_tags):
        actions.add("transform_data")

    # --- Abend / exit ---
    if RE_ABEND_NAME.search(name):
        actions.add("abend")
    if RE_STOP_RUN.search(collapsed) or RE_GOBACK.search(collapsed) or RE_EXIT_PROGRAM.search(collapsed):
        actions.add("program_exit")

    # --- Error-handler (name heuristic, not already tagged as abend) ---
    if RE_ERROR_NAME.search(name) and "abend" not in actions:
        actions.add("display_error")

    return sorted(actions) if actions else ["no_action_detected"]


# ===========================================================================
# 7.  FILE OPERATIONS
#     Per-paragraph file verb extraction with provenance.
#     Adapted from CardDemo extract_paragraph_io.py verb classification
#     (WRITER_VERBS / READER_VERBS taxonomy simplified for file verbs only).
# ===========================================================================

def extract_file_operations(
    para_bodies: dict[str, str],
    file_names:  set[str],
) -> dict[str, list[dict]]:
    """
    Return {file_name: [{paragraph, operation, source_line}]}.

    For each paragraph body, scan for OPEN and I/O verbs.  Only files in
    *file_names* are recorded (pass the SELECT-derived set to avoid spurious
    matches on non-file identifiers).  If *file_names* is empty, all matches
    are recorded.

    Operations emitted: open_input, open_output, open_i_o, open_extend,
                        read, write, rewrite, delete, start, close
    """
    result: dict[str, list[dict]] = {}

    for para, body in para_bodies.items():
        collapsed = collapse_exec_cics_blocks(body)

        # OPEN <mode> <file>  -- mode is significant
        for m in RE_OPEN_MODE.finditer(collapsed):
            mode  = m.group(1).upper().replace("-", "_").lower()
            fname = m.group(2).upper()
            if not file_names or fname in file_names:
                result.setdefault(fname, []).append({
                    "paragraph":   para,
                    "operation":   f"open_{mode}",
                    "source_line": None,   # raw line# not available in body slice
                })

        # READ / WRITE / REWRITE / DELETE / START / CLOSE <file>
        for m in RE_IO_VERB.finditer(collapsed):
            verb  = m.group(1).upper()
            fname = m.group(2).upper()
            if not file_names or fname in file_names:
                result.setdefault(fname, []).append({
                    "paragraph":   para,
                    "operation":   verb.lower(),
                    "source_line": None,
                })

    return result


# ===========================================================================
# 8.  FILE LINEAGE  (SELECT / ASSIGN / FD linkage)
#     Adapted from CardDemo extract_file_control.py
# ===========================================================================

def extract_file_lineage(clean: str) -> list[dict]:
    """
    Link file logical names to ddnames and FD record names.

    Returns: [{"name": str, "ddname": str, "fd_record": str | None}]

    The heuristic for FD matching: take the first FD whose name *starts with*
    the first four characters of the file logical name.  This works reliably
    for the AWS CardDemo corpus (e.g. ACCTFILE -> FD ACCTFILE-REC) and most
    standard COBOL naming conventions.

    If no FD match is found, fd_record is None.
    """
    selects: dict[str, str] = {}
    for m in RE_SELECT.finditer(clean):
        selects[m.group(1).upper()] = m.group(2).upper()

    fds: list[str] = [m.group(1).upper() for m in RE_FD.finditer(clean)]

    result: list[dict] = []
    for fname, ddname in selects.items():
        fd_match: str | None = None
        prefix = fname[:4]                 # 4-char heuristic match
        for fd in fds:
            if fd.startswith(prefix):
                fd_match = fd
                break
        result.append({
            "name":      fname,
            "ddname":    ddname,
            "fd_record": fd_match,
        })
    return result


# ===========================================================================
# 9.  CICS SUBTREE EXTRACTOR
# ===========================================================================

def extract_cics(
    raw:         str,
    clean:       str,
    para_bodies: dict[str, str],
) -> dict:
    """
    Extract the full CICS semantic subtree for CICS-present programs.

    Called ONLY when cics_present == True.  Returns:

      {
        "commarea_used": bool,
        "commands":      list[str],   -- sorted unique command verbs
        "maps_used":     list[str],
        "mapsets_used":  list[str],
        "aid_keys":      list[str],   -- sorted unique DFHxxx AID constants
        "screen_flow":   list[dict]   -- see below
      }

    AID key extraction (three complementary matchers, all deterministic):
      1. EVALUATE EIBAID block scanner  -- dominant CardDemo CICS pattern
         Scans forward line-by-line from EVALUATE EIBAID to END-EVALUATE,
         collecting every WHEN DFHxxx constant.  Applied per-paragraph so
         aid_keys can be associated with screen_flow entries.
      2. IF EIBAID = DFHxxx form         -- secondary comparison pattern
      3. EIBAID = DFHAID.xxx / DFHAID.x  -- legacy dotted form (fallback)

    All three matchers feed a single de-duplicated, alphabetically sorted
    cics.aid_keys list.  A defensive length filter (4-10 chars) discards
    obvious false positives.

    screen_flow entries:
      Standard (send/receive without AID context):
        {"paragraph": str, "action": "send_map"|"receive_map", "map": str|None}
      Enhanced (paragraph also has EVALUATE EIBAID):
        {"paragraph": str, "action": "aid_dispatch",
         "aid_keys": [str, ...], "maps": [str, ...]}
    """
    # Collapse EXEC CICS blocks for command/map extraction.
    # AID key extraction intentionally uses the NON-collapsed form because
    # EVALUATE EIBAID blocks are pure COBOL, never inside EXEC CICS blocks.
    collapsed_full = collapse_exec_cics_blocks(clean)

    # --- Command verbs ---
    commands: set[str] = set()
    for m in RE_EXEC_CICS_CMD.finditer(collapsed_full):
        commands.add(m.group(1).upper())
    commands.discard("MAP")     # MAP is a clause keyword, not a command verb
    commands.discard("MAPSET")

    # --- Map and mapset names ---
    maps_used:    set[str] = set()
    mapsets_used: set[str] = set()
    for m in RE_CICS_MAP.finditer(collapsed_full):
        maps_used.add(m.group(1).upper())
    for m in RE_CICS_MAPSET.finditer(collapsed_full):
        mapsets_used.add(m.group(1).upper())

    # --- AID keys (program-wide, all three matchers) ---
    # Run over the full clean (non-collapsed) procedure text so that
    # EVALUATE EIBAID blocks spanning many lines are picked up correctly.
    aid_keys: set[str] = _extract_aid_keys_from_text(clean)

    # --- COMMAREA ---
    commarea_used = bool(RE_COMMAREA.search(raw))

    # --- Screen flow: per-paragraph, with AID context ---
    screen_flow: list[dict] = []
    for para, body in para_bodies.items():
        collapsed_body = collapse_exec_cics_blocks(body)

        # Collect maps referenced in this paragraph
        para_maps: list[str] = [
            m.group(1).upper() for m in RE_CICS_MAP.finditer(collapsed_body)
        ]

        # Collect AID keys for this specific paragraph (non-collapsed body)
        para_aids = sorted(_extract_aid_keys_from_text(body))

        if para_aids:
            # Paragraph has AID-driven dispatch -- emit enhanced screen_flow
            # entry regardless of whether it also does send/receive.
            # action = "aid_dispatch" signals this is the primary entry-condition
            # paragraph (typically the MAIN-PARA / KEY-HANDLER equivalent).
            screen_flow.append({
                "paragraph": para,
                "action":    "aid_dispatch",
                "aid_keys":  para_aids,
                "maps":      para_maps if para_maps else None,
            })
        else:
            # Standard send/receive map entries (no AID context)
            if RE_CICS_SEND_MAP.search(collapsed_body):
                map_m = RE_CICS_MAP.search(collapsed_body)
                screen_flow.append({
                    "paragraph": para,
                    "action":    "send_map",
                    "map":       map_m.group(1).upper() if map_m else None,
                })
            if RE_CICS_RECV_MAP.search(collapsed_body):
                map_m = RE_CICS_MAP.search(collapsed_body)
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
# 10. CONTROL FLOW GRAPH — TEXT-SCAN BUILDER
#     Adapted from CardDemo extract_cfg_local.py (analyze_flow + reachability)
#     combined with extract_fallthrough.py (last-verb terminator classification)
# ===========================================================================

def _last_verb_terminator(body: str) -> str | None:
    """
    Determine the terminator type for a paragraph body using the same
    last-verb classification as CardDemo extract_fallthrough.py.

    Returns one of: 'goto', 'stop_run', 'goback', 'explicit_exit',
                    'cics_return', 'cics_xctl', or None (implicit fallthrough).
    """
    # Scan in reverse line order to find the last substantive verb
    # (skip blank lines and comments)
    non_blank = [l for l in reversed(body.splitlines()) if l.strip()]
    for line in non_blank:
        u = line.upper().strip()
        if RE_GOTO.search(line):                    return "goto"
        if RE_STOP_RUN.search(line):                return "stop_run"
        if RE_GOBACK.search(line):                  return "goback"
        if RE_EXIT_PROGRAM.search(line):            return "explicit_exit"
        # CICS RETURN / XCTL: check collapsed single line
        if "EXEC" in u and "CICS" in u:
            for cics_op in CICS_TERMINATOR_OPS:
                if cics_op in u:
                    return f"cics_{cics_op.lower()}"
    return None  # implicit fallthrough


def build_cfg_text_scan(
    clean:   str,
    defined: list[dict],
) -> dict:
    """
    Build a control_flow dict using text-scan only.

    cfg_source = "text_scan".

    Limitations vs. REKT:
      * No conditional_true / conditional_false edge distinction.
        (IF / EVALUATE produce a ``branch_logic`` action tag but edges are
         not split into true/false branches.)
      * PERFORM VARYING / UNTIL loops emit one ``perform`` edge; loop bounds
        are not captured.
      * EXEC CICS XCTL / LINK are not followed as inter-program call edges.

    Algorithm (derived from CardDemo extract_cfg_local.analyze_flow):
      For each paragraph (in source order):
        1. Emit perform / perform_thru / goto / call edges from the body.
        2. Detect the paragraph's last-verb terminator.
        3. If terminator is None (implicit), emit a fallthrough edge to the
           next paragraph in source order (from extract_fallthrough.py rule).
      Entry point  = first paragraph in source order.
      Exit points  = paragraphs whose last verb is a terminal statement OR
                     whose name matches the abend heuristic.

    Structural-minimal programs (COBSWAIT pattern):
      When paragraphs_defined is empty and cics_present is False, no edges
      are emitted and cfg_note is set to 'structural_minimal: no paragraphs
      detected' so downstream consumers have a machine-readable annotation.
    """
    para_order  = [p["name"] for p in defined]
    para_names  = set(para_order)
    para_bodies = split_procedure_bodies(clean)

    edges     : list[dict] = []
    unresolved: list[str]  = []
    exit_points: set[str]  = set()
    seen_edges : set[tuple] = set()

    def add_edge(frm: str, to: str, etype: str) -> None:
        key = (frm, to, etype)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append({"from": frm, "to": to, "type": etype, "source_lines": None})
        if to not in para_names and etype in ("perform", "perform_thru", "goto"):
            unresolved.append(to)

    for idx, para in enumerate(para_order):
        body = para_bodies.get(para, "")
        collapsed = collapse_exec_cics_blocks(body)

        # --- PERFORM THRU <from> THRU <to> ---
        for m in RE_PERFORM_THRU.finditer(collapsed):
            t_start = m.group(1).upper()
            t_end   = m.group(2).upper()
            key = (para, t_start, "perform_thru")
            if key not in seen_edges:
                seen_edges.add(key)
                edges.append({
                    "from": para, "to": t_start, "type": "perform_thru",
                    "thru": t_end, "source_lines": None,
                })
            if t_start not in para_names:
                unresolved.append(t_start)

        # --- PERFORM <loop> UNTIL / VARYING ---
        for m in RE_PERFORM_LOOP.finditer(collapsed):
            t = m.group(1).upper()
            if t not in PERFORM_NON_TARGETS:
                add_edge(para, t, "perform")

        # --- PERFORM <para> (simple / inline) ---
        for m in RE_PERFORM_SIMPLE.finditer(collapsed):
            t = m.group(1).upper()
            if t not in PERFORM_NON_TARGETS:
                add_edge(para, t, "perform")

        # --- GO TO <para> ---
        for m in RE_GOTO.finditer(collapsed):
            t = m.group(1).upper()
            add_edge(para, t, "goto")

        # --- CALL '<name>' ---
        for m in RE_CALL.finditer(collapsed):
            t = m.group(1).upper()
            key = (para, t, "call")
            if key not in seen_edges:
                seen_edges.add(key)
                edges.append({"from": para, "to": t, "type": "call", "source_lines": None})

        # --- Fallthrough (extract_fallthrough.py rule) ---
        terminator = _last_verb_terminator(body)
        if terminator is None:
            if idx < len(para_order) - 1:
                nxt = para_order[idx + 1]
                add_edge(para, nxt, "fallthrough")
            else:
                exit_points.add(para)
        else:
            exit_points.add(para)

        if RE_ABEND_NAME.search(para):
            exit_points.add(para)

    entry_points = [para_order[0]] if para_order else []

    cfg = {
        "cfg_source":   "text_scan",
        "entry_points": entry_points,
        "exit_points":  sorted(exit_points),
        "edges":        edges,
        "unresolved":   sorted(set(unresolved)),
    }

    # Structural-minimal annotation: COBSWAIT pattern.
    # Set when no paragraphs were found AND the program is not a CICS program
    # (CICS programs with no batch paragraphs are handled separately in enrich).
    if not para_order:
        cfg["cfg_note"] = "structural_minimal: no paragraphs detected"

    return cfg


# ===========================================================================
# 11. CONTROL FLOW GRAPH — REKT JSON ADAPTER
# ===========================================================================

def build_cfg_from_rekt(
    rekt_dir: Path,
    program:  str,
) -> dict | None:
    """
    Attempt to build control_flow from smojol/REKT JSON output.

    REKT writes a report directory per program.  We look for
    ``<rekt_dir>/<program>.cbl.report*`` and recursively scan for *.json
    files that contain an 'edges' list.

    Returns None if no REKT output exists or if the output has no edges,
    so the caller can fall back to build_cfg_text_scan.

    cfg_source = "rekt" (higher fidelity: REKT has resolved conditional
    branches and full scope information).
    """
    pattern = f"{program}.cbl.report*"
    candidates = sorted(rekt_dir.glob(pattern))
    if not candidates:
        return None

    report_dir   = candidates[0]
    edges        : list[dict] = []
    unresolved   : list[str]  = []
    entry_points : list[str]  = []
    exit_points  : list[str]  = []

    for jf in sorted(report_dir.rglob("*.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue

        for e in data.get("edges", []):
            if isinstance(e, dict) and "from" in e and "to" in e:
                edges.append({
                    "from":         str(e["from"]),
                    "to":           str(e["to"]),
                    "type":         str(e.get("type", "unknown")),
                    "source_lines": e.get("source_lines"),
                })
        unresolved   += [str(u) for u in data.get("unresolved", [])]
        entry_points += [str(p) for p in data.get("entry_points", [])]
        exit_points  += [str(p) for p in data.get("exit_points",  [])]

    if not edges:
        return None

    return {
        "cfg_source":   "rekt",
        "entry_points": sorted(set(entry_points)),
        "exit_points":  sorted(set(exit_points)),
        "edges":        edges,
        "unresolved":   sorted(set(unresolved)),
    }


# ===========================================================================
# 12. TOP-LEVEL ENRICH FUNCTION
# ===========================================================================

def enrich(
    program_name:       str,
    raw_cobol:          str,
    preprocessed_cobol: str | None,
    rekt_json:          dict | None,
    base_facts:         dict,
    rekt_dir:           Path | None = None,
) -> dict:
    """
    Produce and return the v1.1 semantic enrichment fields.

    Parameters
    ----------
    program_name        : The COBOL program name (used for REKT lookup).
    raw_cobol           : Raw COBOL source text (required).
    preprocessed_cobol  : cobc -E output if available; otherwise None.
    rekt_json           : Pre-loaded REKT CFG dict (optional).
    base_facts          : v1.0 facts dict (used to read cics_present flag).
    rekt_dir            : Path to directory containing REKT report subdirs.

    Returns
    -------
    dict with v1.1 enrichment keys merged into base facts by extract_facts.py.
    """
    cics_present: bool = base_facts.get("cics_present", False)

    analysis_text = strip_fixed_format_comments(
        preprocessed_cobol if preprocessed_cobol else raw_cobol
    )

    defined    = extract_paragraphs_defined(raw_cobol, analysis_text)
    referenced = extract_paragraphs_referenced(analysis_text, defined)
    para_bodies = split_procedure_bodies(analysis_text)

    paragraph_actions: dict[str, list[str]] = {
        p["name"]: classify_paragraph_actions(p["name"], para_bodies.get(p["name"], ""))
        for p in defined
    }

    file_lineage    = extract_file_lineage(analysis_text)
    file_names      = {f["name"] for f in file_lineage}
    file_operations = extract_file_operations(para_bodies, file_names)

    control_flow: dict | None = None
    if not cics_present:
        if rekt_json and isinstance(rekt_json.get("edges"), list) and rekt_json["edges"]:
            control_flow = {
                "cfg_source":   "rekt",
                "entry_points": rekt_json.get("entry_points", []),
                "exit_points":  rekt_json.get("exit_points",  []),
                "edges":        rekt_json["edges"],
                "unresolved":   rekt_json.get("unresolved", []),
            }
        elif rekt_dir and rekt_dir.is_dir():
            control_flow = build_cfg_from_rekt(rekt_dir, program_name)

    if control_flow is None:
        control_flow = build_cfg_text_scan(analysis_text, defined)
        if cics_present:
            control_flow["cfg_note"] = (
                "CICS program: text_scan CFG; conditional branches not resolved "
                "without a CICS translator.  Maps, commands, and AID keys are "
                "captured separately in the 'cics' subtree."
            )

    cics_facts: dict | None = (
        extract_cics(raw_cobol, analysis_text, para_bodies)
        if cics_present else None
    )

    return {
        "paragraphs_defined":    defined,
        "paragraphs_referenced": referenced,
        "paragraph_actions":     paragraph_actions,
        "file_lineage":          file_lineage,
        "file_operations":       file_operations,
        "control_flow":          control_flow,
        "cics":                  cics_facts,
    }


# ===========================================================================
# 13. CLI SMOKE TEST
# ===========================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python hermes_v11_combined_extractor.py <file.cbl>", file=sys.stderr)
        sys.exit(1)

    src = Path(sys.argv[1])
    if not src.exists():
        print(f"ERROR: file not found: {src}", file=sys.stderr)
        sys.exit(2)

    raw  = src.read_text(encoding="utf-8", errors="replace")
    cics = bool(RE_EXEC_CICS_START.search(raw))
    base = {"cics_present": cics, "sql_present": bool(RE_EXEC_SQL.search(raw))}

    result = enrich(
        program_name=src.stem.upper(),
        raw_cobol=raw,
        preprocessed_cobol=None,
        rekt_json=None,
        base_facts=base,
        rekt_dir=None,
    )

    cf = result["control_flow"]
    print(f"Program       : {src.stem.upper()}")
    print(f"CICS          : {cics}")
    print(f"Paragraphs    : {len(result['paragraphs_defined'])} defined, "
          f"{len(result['paragraphs_referenced'])} referenced")
    print(f"CFG source    : {cf['cfg_source']}")
    print(f"CFG edges     : {len(cf.get('edges', []))}")
    print(f"Entry points  : {cf.get('entry_points', [])}")
    print(f"Exit points   : {cf.get('exit_points', [])}")
    print(f"Unresolved    : {cf.get('unresolved', [])}")
    print(f"Files         : {[f['name'] for f in result['file_lineage']]}")
    if cf.get("cfg_note"):
        print(f"CFG note      : {cf['cfg_note']}")
    print()
    print("Paragraph actions (first 5 paragraphs):")
    for name, acts in list(result["paragraph_actions"].items())[:5]:
        print(f"  {name:<32s}: {acts}")
    if cics and result["cics"]:
        c = result["cics"]
        sf_with_aids = [e for e in c["screen_flow"] if e.get("aid_keys")]
        print()
        print(f"CICS commands : {c['commands']}")
        print(f"Maps used     : {c['maps_used']}")
        print(f"AID keys      : {c['aid_keys']}")
        print(f"COMMAREA      : {c['commarea_used']}")
        print(f"Screen flow   : {len(c['screen_flow'])} entries "
              f"({len(sf_with_aids)} with aid_keys)")
        if sf_with_aids:
            print("  AID dispatch entries:")
            for e in sf_with_aids:
                print(f"    {e['paragraph']}: {e['aid_keys']}")

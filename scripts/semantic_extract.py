#!/usr/bin/env python3
"""
semantic_extract.py — HermesCOBOL schema v1.1 semantic enrichment.

Mined and adapted from:
  aws-mainframe-modernization-carddemo/scripts/extract_cfg_local.py
  aws-mainframe-modernization-carddemo/scripts/extract_fallthrough.py
  aws-mainframe-modernization-carddemo/scripts/extract_paragraph_io.py
  aws-mainframe-modernization-carddemo/scripts/extract_file_control.py

This module is text-scan only. It does NOT invoke cobc or any external tool.
CFG fidelity is explicitly marked: cfg_source = "rekt" (if REKT JSON present)
or "text_scan" (always available). CICS programs use text_scan only.

No LLMs. No network. Manual-first.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Paragraph noise filter
# Exact set from implementation spec; applied after raw paragraph extraction.
# ---------------------------------------------------------------------------
PARAGRAPH_NOISE = frozenset([
    "END-IF", "END-PERFORM", "END-EVALUATE", "END-READ",
    "END-WRITE", "END-REWRITE", "END-DELETE", "END-START",
    "END-CALL", "END-STRING", "END-UNSTRING", "END-EXEC",
    "EXIT", "CONTINUE", "GOBACK", "STOP",
    "FILE-CONTROL", "I-O-CONTROL", "PROGRAM-ID",
])

# Broader reserved names that are never paragraph labels
RESERVED_DIVISIONS = frozenset([
    "IDENTIFICATION", "ENVIRONMENT", "DATA", "PROCEDURE",
    "CONFIGURATION", "INPUT-OUTPUT", "FILE", "WORKING-STORAGE",
    "LINKAGE", "LOCAL-STORAGE", "REPORT", "SCREEN",
    "AUTHOR", "INSTALLATION", "DATE-WRITTEN",
    "DATE-COMPILED", "SECURITY", "REMARKS",
    "FD", "SD", "RD",
])

PERFORM_NON_TARGETS = frozenset([
    "UNTIL", "VARYING", "TIMES", "WITH", "TEST",
    "THRU", "THROUGH", "BEFORE", "AFTER",
])


# ---------------------------------------------------------------------------
# Regex library
# ---------------------------------------------------------------------------
RE_PARA_LABEL = re.compile(
    r"^([ ]{0,11})([A-Z0-9][A-Z0-9-]*)[ \t]*\.[ \t]*$",
    re.MULTILINE | re.IGNORECASE,
)
RE_SECTION = re.compile(
    r"^[ ]{0,11}([A-Z0-9][A-Z0-9-]*)[ \t]+SECTION[ \t]*\.[ \t]*$",
    re.MULTILINE | re.IGNORECASE,
)
RE_PERFORM_SIMPLE = re.compile(
    r"\bPERFORM[ \t]+([A-Z0-9][A-Z0-9-]+)[ \t]*$",
    re.MULTILINE | re.IGNORECASE,
)
RE_PERFORM_THRU = re.compile(
    r"\bPERFORM[ \t]+([A-Z0-9][A-Z0-9-]+)[ \t]+THRU[ \t]+([A-Z0-9][A-Z0-9-]+)",
    re.IGNORECASE,
)
RE_PERFORM_UNTIL = re.compile(
    r"\bPERFORM[ \t]+([A-Z0-9][A-Z0-9-]*)[ \t]+UNTIL",
    re.IGNORECASE,
)
RE_PERFORM_VARYING = re.compile(
    r"\bPERFORM[ \t]+([A-Z0-9][A-Z0-9-]*)[ \t]+VARYING",
    re.IGNORECASE,
)
RE_GOTO = re.compile(
    r"\bGO[ \t]+TO[ \t]+([A-Z0-9][A-Z0-9-]+)",
    re.IGNORECASE,
)
RE_CALL = re.compile(
    r"\bCALL[ \t]+['\"]([A-Z0-9][A-Z0-9-]*)['\"] ",
    re.IGNORECASE,
)
RE_PROC_DIV = re.compile(
    r"^[ \t]*PROCEDURE[ \t]+DIVISION",
    re.MULTILINE | re.IGNORECASE,
)
RE_DATA_DIV = re.compile(
    r"^[ \t]*DATA[ \t]+DIVISION",
    re.MULTILINE | re.IGNORECASE,
)
# File I/O verbs
RE_IO_VERB = re.compile(
    r"\b(OPEN|CLOSE|READ|WRITE|REWRITE|DELETE|START)[ \t]+([A-Z0-9][A-Z0-9-]*)",
    re.IGNORECASE,
)
RE_OPEN_MODE = re.compile(
    r"\bOPEN[ \t]+(INPUT|OUTPUT|I-O|EXTEND)[ \t]+([A-Z0-9][A-Z0-9-]*)",
    re.IGNORECASE,
)
RE_SELECT = re.compile(
    r"\bSELECT[ \t]+([A-Z0-9][A-Z0-9-]*)[ \t]+ASSIGN[ \t]+TO[ \t]+([A-Z0-9][A-Z0-9-]*)",
    re.IGNORECASE,
)
RE_FD = re.compile(
    r"^[ \t]*FD[ \t]+([A-Z0-9][A-Z0-9-]*)",
    re.MULTILINE | re.IGNORECASE,
)
RE_COPY = re.compile(r"\bCOPY[ \t]+([A-Z0-9][A-Z0-9-]*)", re.IGNORECASE)
# CICS patterns
RE_EXEC_CICS      = re.compile(r"\bEXEC[ \t]+CICS[ \t]+([A-Z][A-Z0-9-]*)[ \t]+", re.IGNORECASE)
RE_CICS_MAP       = re.compile(r"\bMAP[ \t]*\([ \t]*['\"]?([A-Z0-9][A-Z0-9-]*)['\"]?[ \t]*\)", re.IGNORECASE)
RE_CICS_MAPSET    = re.compile(r"\bMAPSET[ \t]*\([ \t]*['\"]?([A-Z0-9][A-Z0-9-]*)['\"]?[ \t]*\)", re.IGNORECASE)
RE_CICS_SEND      = re.compile(r"EXEC[ \t]+CICS[ \t]+SEND[ \t]+MAP", re.IGNORECASE)
RE_CICS_RECEIVE   = re.compile(r"EXEC[ \t]+CICS[ \t]+RECEIVE[ \t]+MAP", re.IGNORECASE)
RE_EIBAID         = re.compile(r"EIBAID[ \t]*=[ \t]*DFHAID[ \t]*\.?([A-Z0-9]+)", re.IGNORECASE)
RE_DFHAID_FIELD   = re.compile(r"\bDFHAID\.([A-Z0-9]+)\b", re.IGNORECASE)
RE_COMMAREA       = re.compile(r"\bDFHCOMMAREA\b", re.IGNORECASE)
RE_EXEC_CICS_FULL = re.compile(r"EXEC[ \t]+CICS\b", re.IGNORECASE)
RE_EXEC_SQL       = re.compile(r"EXEC[ \t]+SQL\b", re.IGNORECASE)
# Action classifiers (applied per-paragraph body)
RE_DISPLAY        = re.compile(r"\bDISPLAY\b", re.IGNORECASE)
RE_MOVE           = re.compile(r"\bMOVE\b", re.IGNORECASE)
RE_IF             = re.compile(r"\bIF\b", re.IGNORECASE)
RE_EVALUATE       = re.compile(r"\bEVALUATE\b", re.IGNORECASE)
RE_ABEND_PARA     = re.compile(r"(ABEND|9999|ABORT|STORUN)", re.IGNORECASE)
RE_ERROR_PARA     = re.compile(r"(ERROR|STAT|STATUS|INVALID|EXCEPT)", re.IGNORECASE)
RE_STOP_RUN       = re.compile(r"\bSTOP[ \t]+RUN\b", re.IGNORECASE)
RE_GOBACK         = re.compile(r"\bGOBACK\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Source line utilities
# ---------------------------------------------------------------------------
def line_number_of_match(text: str, match_start: int) -> int:
    return text[:match_start].count("\n") + 1


def strip_comments(text: str) -> str:
    """Strip fixed-format COBOL comment lines (col 7 = * or /)."""
    out = []
    for line in text.splitlines():
        if len(line) >= 7 and line[6] in ("*", "/"):
            out.append("")
        else:
            out.append(line)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Paragraph extraction with noise filter and provenance
# Adapted from CardDemo extract_cfg_local.py analyze_flow()
# ---------------------------------------------------------------------------
def extract_paragraphs_defined(
    text: str,
    clean: str,
) -> list[dict]:
    """
    Returns list of {name, source_line, area_a} for real paragraph labels.
    Filters PARAGRAPH_NOISE, RESERVED_DIVISIONS, SECTION names, and -DIVISION.
    """
    sections: set[str] = {
        m.group(1).upper() for m in RE_SECTION.finditer(clean)
    }
    results = []
    seen: set[str] = set()
    for m in RE_PARA_LABEL.finditer(clean):
        name = m.group(2).upper()
        indent = len(m.group(1))
        if name in PARAGRAPH_NOISE:
            continue
        if name in RESERVED_DIVISIONS:
            continue
        if name.endswith("-DIVISION"):
            continue
        if name in sections:
            continue
        if name in seen:
            continue
        seen.add(name)
        lineno = line_number_of_match(text, m.start())
        results.append({"name": name, "source_line": lineno, "area_a": indent <= 3})
    return results


def extract_paragraphs_referenced(clean: str, defined: list[dict]) -> list[str]:
    """
    All paragraph names appearing in PERFORM targets that are in the defined set.
    """
    defined_names = {p["name"] for p in defined}
    referenced: set[str] = set()
    for m in re.finditer(r"\bPERFORM[ \t]+([A-Z0-9][A-Z0-9-]+)", clean, re.IGNORECASE):
        t = m.group(1).upper()
        if t in defined_names and t not in PERFORM_NON_TARGETS:
            referenced.add(t)
    for m in RE_GOTO.finditer(clean):
        t = m.group(1).upper()
        if t in defined_names:
            referenced.add(t)
    return sorted(referenced)


# ---------------------------------------------------------------------------
# Procedure division body splitter
# Splits text into {paragraph_name: body_text} mapping for per-para analysis.
# ---------------------------------------------------------------------------
def split_procedure_division(text: str, clean: str) -> dict[str, str]:
    """
    Returns {para_name: body_lines_str} for every defined paragraph.
    Body runs from the line after the paragraph label until the next label.
    """
    proc_m = RE_PROC_DIV.search(clean)
    if not proc_m:
        return {}
    proc_start = proc_m.end()
    proc_text = clean[proc_start:]
    proc_lines = proc_text.splitlines()

    para_map: dict[str, list[str]] = {}
    current: str | None = None
    label_re = re.compile(
        r"^([ ]{0,11})([A-Z0-9][A-Z0-9-]*)[ \t]*\.[ \t]*$",
        re.IGNORECASE,
    )
    for line in proc_lines:
        m = label_re.match(line)
        if m:
            name = m.group(2).upper()
            if name not in PARAGRAPH_NOISE and not name.endswith("-DIVISION"):
                current = name
                para_map.setdefault(current, [])
                continue
        if current is not None:
            para_map[current].append(line)
    return {k: "\n".join(v) for k, v in para_map.items()}


# ---------------------------------------------------------------------------
# Paragraph action classification
# Derived from CardDemo extract_paragraph_io.py
# ---------------------------------------------------------------------------
ACTION_FILE_VERBS = {
    "OPEN":    "open_file",
    "CLOSE":   "close_file",
    "READ":    "read_file",
    "WRITE":   "write_file",
    "REWRITE": "rewrite_file",
    "DELETE":  "delete_record",
    "START":   "start_browse",
}


def classify_paragraph_actions(name: str, body: str) -> list[str]:
    """Return sorted list of action tags for a paragraph body."""
    actions: set[str] = set()

    # File I/O verbs
    for m in RE_IO_VERB.finditer(body):
        verb = m.group(1).upper()
        if verb in ACTION_FILE_VERBS:
            actions.add(ACTION_FILE_VERBS[verb])

    # CALL
    if RE_CALL.search(body):
        actions.add("call_program")

    # CICS
    if RE_EXEC_CICS_FULL.search(body):
        actions.add("cics_command")
        if RE_CICS_SEND.search(body):
            actions.add("send_map")
        if RE_CICS_RECEIVE.search(body):
            actions.add("receive_map")

    # DISPLAY
    if RE_DISPLAY.search(body):
        actions.add("display_error" if RE_ERROR_PARA.search(name) else "display_output")

    # Branch logic
    if RE_IF.search(body) or RE_EVALUATE.search(body):
        actions.add("branch_logic")

    # MOVE without other I/O = transform
    if RE_MOVE.search(body) and not actions - {"branch_logic", "display_output", "display_error"}:
        actions.add("transform_data")

    # Abend / exit
    if RE_ABEND_PARA.search(name):
        actions.add("abend")
    if RE_STOP_RUN.search(body) or RE_GOBACK.search(body):
        actions.add("program_exit")

    # Error / status check
    if RE_ERROR_PARA.search(name) and "abend" not in actions:
        actions.add("display_error")

    return sorted(actions) if actions else ["no_action_detected"]


# ---------------------------------------------------------------------------
# File operations per paragraph
# ---------------------------------------------------------------------------
def extract_file_operations(
    para_bodies: dict[str, str],
    file_names: set[str],
) -> dict[str, list[dict]]:
    """
    Returns {file_name: [{paragraph, operation, source_line}]} mapping.
    Adapted from CardDemo extract_paragraph_io.py.
    """
    result: dict[str, list[dict]] = {}

    for para, body in para_bodies.items():
        for m in RE_OPEN_MODE.finditer(body):
            mode = m.group(1).upper()
            fname = m.group(2).upper()
            if fname in file_names or not file_names:
                result.setdefault(fname, []).append({
                    "paragraph": para,
                    "operation": f"open_{mode.lower()}",
                    "source_line": None,
                })
        for m in RE_IO_VERB.finditer(body):
            verb = m.group(1).upper()
            fname = m.group(2).upper()
            if verb == "OPEN":
                continue  # handled above
            if fname in file_names or not file_names:
                result.setdefault(fname, []).append({
                    "paragraph": para,
                    "operation": verb.lower(),
                    "source_line": None,
                })
    return result


# ---------------------------------------------------------------------------
# CFG: text-scan fallback (PERFORM graph)
# Adapted from CardDemo extract_cfg_local.py analyze_flow()
# Reachability walk from entry paragraph.
# ---------------------------------------------------------------------------
def build_cfg_text_scan(
    clean: str,
    defined: list[dict],
) -> dict:
    """
    Build control_flow dict using text scan only.
    cfg_source = "text_scan".
    Lower fidelity than REKT: no conditional branch distinction, no fallthrough.
    """
    para_names = {p["name"] for p in defined}
    para_order = [p["name"] for p in defined]

    # per-paragraph outbound edges
    edges: list[dict] = []
    unresolved: list[str] = []

    para_bodies = split_procedure_division("\n".join(clean.splitlines()), clean)

    for para in para_order:
        body = para_bodies.get(para, "")

        # PERFORM THRU
        for m in RE_PERFORM_THRU.finditer(body):
            t_from = m.group(1).upper()
            t_to   = m.group(2).upper()
            edges.append({"from": para, "to": t_from, "type": "perform_thru",
                          "thru": t_to, "source_lines": None})
            if t_from not in para_names:
                unresolved.append(t_from)

        # PERFORM UNTIL
        for m in RE_PERFORM_UNTIL.finditer(body):
            t = m.group(1).upper()
            if t and t not in PERFORM_NON_TARGETS:
                edges.append({"from": para, "to": t, "type": "perform",
                              "source_lines": None})
                if t not in para_names:
                    unresolved.append(t)

        # PERFORM VARYING
        for m in RE_PERFORM_VARYING.finditer(body):
            t = m.group(1).upper()
            if t and t not in PERFORM_NON_TARGETS:
                edges.append({"from": para, "to": t, "type": "perform",
                              "source_lines": None})
                if t not in para_names:
                    unresolved.append(t)

        # PERFORM simple
        for m in RE_PERFORM_SIMPLE.finditer(body):
            t = m.group(1).upper()
            if t not in PERFORM_NON_TARGETS:
                edges.append({"from": para, "to": t, "type": "perform",
                              "source_lines": None})
                if t not in para_names:
                    unresolved.append(t)

        # GO TO
        for m in RE_GOTO.finditer(body):
            t = m.group(1).upper()
            edges.append({"from": para, "to": t, "type": "goto",
                          "source_lines": None})
            if t not in para_names:
                unresolved.append(t)

        # CALL
        for m in RE_CALL.finditer(body):
            t = m.group(1).upper()
            edges.append({"from": para, "to": t, "type": "call",
                          "source_lines": None})

    # Fallthrough edges: sequential paragraphs with no explicit transfer at end
    for i, para in enumerate(para_order[:-1]):
        body = para_bodies.get(para, "")
        has_goto = bool(RE_GOTO.search(body))
        has_stop = bool(RE_STOP_RUN.search(body)) or bool(RE_GOBACK.search(body))
        if not has_goto and not has_stop:
            nxt = para_order[i + 1]
            edges.append({"from": para, "to": nxt, "type": "fallthrough",
                          "source_lines": None})

    # Entry / exit points
    entry_points = [para_order[0]] if para_order else []
    exit_points: list[str] = []
    for para in para_order:
        body = para_bodies.get(para, "")
        if RE_STOP_RUN.search(body) or RE_GOBACK.search(body):
            exit_points.append(para)
        if RE_ABEND_PARA.search(para):
            exit_points.append(para)
    exit_points = sorted(set(exit_points))

    # Deduplicate edges
    seen_edges: set[tuple] = set()
    deduped: list[dict] = []
    for e in edges:
        key = (e["from"], e["to"], e["type"])
        if key not in seen_edges:
            seen_edges.add(key)
            deduped.append(e)

    return {
        "cfg_source":   "text_scan",
        "entry_points": entry_points,
        "exit_points":  exit_points,
        "edges":        deduped,
        "unresolved":   sorted(set(unresolved)),
    }


# ---------------------------------------------------------------------------
# CFG: REKT JSON adapter
# ---------------------------------------------------------------------------
def build_cfg_from_rekt(rekt_dir: Path, program: str) -> dict | None:
    """
    Attempt to read REKT JSON report and build control_flow dict.
    Returns None if no REKT output found.
    cfg_source = "rekt".
    """
    candidates = list(rekt_dir.glob(f"{program}.cbl.report*"))
    if not candidates:
        return None

    report_dir = sorted(candidates)[0]
    edges: list[dict] = []
    unresolved: list[str] = []
    entry_points: list[str] = []
    exit_points:  list[str] = []

    for jf in sorted(report_dir.rglob("*.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            continue

        if isinstance(data, dict):
            # Absorb edges in smojol format: {"from": ..., "to": ..., "type": ...}
            for e in data.get("edges", []):
                if isinstance(e, dict) and "from" in e and "to" in e:
                    edges.append({
                        "from":        str(e.get("from", "")),
                        "to":          str(e.get("to", "")),
                        "type":        str(e.get("type", "unknown")),
                        "source_lines": e.get("source_lines"),
                    })
            for u in data.get("unresolved", []):
                if isinstance(u, str):
                    unresolved.append(u)
            for ep in data.get("entry_points", []):
                if isinstance(ep, str):
                    entry_points.append(ep)
            for xp in data.get("exit_points", []):
                if isinstance(xp, str):
                    exit_points.append(xp)

    if not edges:
        return None  # REKT present but empty — fall back to text_scan

    return {
        "cfg_source":   "rekt",
        "entry_points": entry_points,
        "exit_points":  exit_points,
        "edges":        edges,
        "unresolved":   sorted(set(unresolved)),
    }


# ---------------------------------------------------------------------------
# CICS subtree extractor
# ---------------------------------------------------------------------------
def extract_cics(
    text: str,
    clean: str,
    para_bodies: dict[str, str],
) -> dict:
    """
    Extract CICS-specific semantic facts.
    Only called when cics_present == True.
    """
    # All EXEC CICS command verbs
    commands: set[str] = set()
    for m in RE_EXEC_CICS.finditer(clean):
        commands.add(m.group(1).upper())

    # Maps and mapsets
    maps_used:    set[str] = set()
    mapsets_used: set[str] = set()
    for m in RE_CICS_MAP.finditer(clean):
        maps_used.add(m.group(1).upper())
    for m in RE_CICS_MAPSET.finditer(clean):
        mapsets_used.add(m.group(1).upper())

    # AID keys from DFHAID comparisons
    aid_keys: set[str] = set()
    for m in RE_EIBAID.finditer(clean):
        aid_keys.add(m.group(1).upper())
    for m in RE_DFHAID_FIELD.finditer(clean):
        aid_keys.add(m.group(1).upper())

    # COMMAREA
    commarea_used = bool(RE_COMMAREA.search(clean))

    # Screen flow: per-paragraph SEND/RECEIVE MAP actions
    screen_flow: list[dict] = []
    for para, body in para_bodies.items():
        if RE_CICS_SEND.search(body):
            map_m = RE_CICS_MAP.search(body)
            screen_flow.append({
                "paragraph": para,
                "action":    "send_map",
                "map":       map_m.group(1).upper() if map_m else None,
            })
        if RE_CICS_RECEIVE.search(body):
            map_m = RE_CICS_MAP.search(body)
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


# ---------------------------------------------------------------------------
# File lineage: SELECT + FD + COPY linkage
# ---------------------------------------------------------------------------
def extract_file_lineage(clean: str) -> list[dict]:
    """
    Build enriched file list: {name, ddname, fd_record, copybooks}.
    Extends v1.0 data_files with FD linkage.
    """
    # SELECT ... ASSIGN TO
    selects: dict[str, str] = {}
    for m in RE_SELECT.finditer(clean):
        selects[m.group(1).upper()] = m.group(2).upper()

    # FD records
    fds: set[str] = {m.group(1).upper() for m in RE_FD.finditer(clean)}

    result = []
    for fname, ddname in selects.items():
        fd_match = None
        for fd in fds:
            if fd.startswith(fname[:4]):
                fd_match = fd
                break
        result.append({
            "name":    fname,
            "ddname":  ddname,
            "fd_record": fd_match,
        })
    return result


# ---------------------------------------------------------------------------
# Top-level enrichment entry point
# ---------------------------------------------------------------------------
def enrich(
    cbl_path: Path,
    rekt_dir: Path | None = None,
    cics_present: bool = False,
) -> dict[str, Any]:
    """
    Main entry point. Returns schema v1.1 semantic additions dict:
      paragraphs_defined, paragraphs_referenced,
      paragraph_actions, file_operations,
      control_flow, cics (or None)

    Caller merges this dict into the v1.0 facts base.
    """
    raw  = cbl_path.read_text(encoding="utf-8", errors="replace")
    clean = strip_comments(raw)

    # Paragraph extraction with noise filter
    defined   = extract_paragraphs_defined(raw, clean)
    referenced = extract_paragraphs_referenced(clean, defined)

    # Procedure division body split
    para_bodies = split_procedure_division(raw, clean)

    # Paragraph actions
    paragraph_actions: dict[str, list[str]] = {}
    for p in defined:
        name = p["name"]
        body = para_bodies.get(name, "")
        paragraph_actions[name] = classify_paragraph_actions(name, body)

    # File lineage
    file_lineage = extract_file_lineage(clean)
    file_names = {f["name"] for f in file_lineage}

    # File operations per paragraph
    file_ops = extract_file_operations(para_bodies, file_names)

    # Control flow: try REKT first, fall back to text_scan
    control_flow: dict | None = None
    if rekt_dir and not cics_present:
        prog = cbl_path.stem.upper()
        control_flow = build_cfg_from_rekt(rekt_dir, prog)
    if control_flow is None:
        control_flow = build_cfg_text_scan(clean, defined)
        if cics_present:
            control_flow["cfg_note"] = (
                "CICS program: text_scan CFG has lower fidelity; "
                "conditional branches not resolved without CICS translator."
            )

    # CICS subtree
    cics_facts: dict | None = None
    if cics_present:
        cics_facts = extract_cics(raw, clean, para_bodies)

    return {
        "paragraphs_defined":   defined,
        "paragraphs_referenced": referenced,
        "paragraph_actions":    paragraph_actions,
        "file_lineage":         file_lineage,
        "file_operations":      file_ops,
        "control_flow":         control_flow,
        "cics":                 cics_facts,
    }

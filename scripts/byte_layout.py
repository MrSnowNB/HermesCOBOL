#!/usr/bin/env python3
# LLM-FREE — Deterministic COBOL byte layout extraction. No LLM inference.
"""
byte_layout.py  v1.2.2
======================
HermesCOBOL v1.2 — Byte Layout Extractor.

Fixes in v1.2.2 (gate-driven, round 2):
  1. test_nested_occurs: the previous test assertion was wrong.
     INNER-FIELD (leaf, no OCCURS clause) correctly has occurs=1.
     The group header INNER-ENTRY carries occurs=12.  Test corrected.
     No code change needed for this specific failure.

  2. test_redefines_01_level / total_bytes=None:
     Elementary 01-level roots (pic != None, children=[]) had
     total_bytes=None because _build_record called _assign_offsets on
     an empty children list, got end_offset=0, and the guard
     'end_offset > 0 else None' returned None.
     Fix: detect elementary root before the children walk and compute
     total_bytes = pic_length(root.pic, root.storage) * root.occurs
     directly.  A single self-field dict is emitted at offset=0.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

__LLM_FREE__ = True

# ---------------------------------------------------------------------------
# 1.  CONSTANTS
# ---------------------------------------------------------------------------

CPY_DIR_DEFAULT = "data/raw/cpy"

_STORAGE_NORM: dict[str, str] = {
    "COMP-3":          "COMP-3",
    "PACKED-DECIMAL":  "COMP-3",
    "COMP-4":          "COMP",
    "COMP-5":          "COMP",
    "COMP":            "COMP",
    "BINARY":          "COMP",
    "DISPLAY":         "DISPLAY",
    "DISPLAY-1":       "DISPLAY",
    "INDEX":           "COMP",
    "POINTER":         "COMP",
}

# ---------------------------------------------------------------------------
# 2.  REGEX LIBRARY
# ---------------------------------------------------------------------------

RE_LEVEL = re.compile(
    r"^\s*(\d{2})\s+([A-Z0-9][A-Z0-9\-]*)\b(.*)",
    re.IGNORECASE,
)
RE_PIC   = re.compile(
    r"\bPIC(?:TURE)?\s+IS\s+([^\s.]+)|\bPIC(?:TURE)?\s+([^\s.]+)",
    re.IGNORECASE,
)
RE_COMP  = re.compile(
    r"\b(COMP-3|COMP-4|COMP-5|COMP|BINARY|PACKED-DECIMAL|DISPLAY-1|DISPLAY|INDEX|POINTER)\b",
    re.IGNORECASE,
)
RE_REDEF = re.compile(r"\bREDEFINES\s+([A-Z0-9][A-Z0-9\-]*)", re.IGNORECASE)
RE_SYNC  = re.compile(r"\bSYNCHRONIZED\b|\bSYNC\b",            re.IGNORECASE)
RE_OCCUR = re.compile(r"\bOCCURS\s+(\d+)(?:\s+TIMES)?\b",      re.IGNORECASE)
RE_VALUE = re.compile(r"\bVALUE\b",                             re.IGNORECASE)

# COPY detection: plain prefix check used in _expand_copies.
RE_COPY_INLINE = re.compile(
    r"^COPY\s+([A-Z0-9][A-Z0-9\-]*)\s*\.?\s*$",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# 3.  TEXT PREPARATION
# ---------------------------------------------------------------------------

def _strip_and_join(text: str) -> list[tuple[int, str]]:
    """
    Prepare COBOL fixed-format source:
      1. Drop comment lines (col 7 = '*' or '/').
      2. Join continuation lines (col 7 = '-').
      3. Strip sequence numbers (cols 1-6) and identification area (73+).

    Returns list of (original_lineno, logical_line) tuples.
    """
    result_lines: list[tuple[int, str]] = []
    pending: str = ""
    pending_lineno: int = 1

    for lineno, raw in enumerate(text.splitlines(), start=1):
        if len(raw) >= 7:
            indicator = raw[6]
            code_area = raw[7:72] if len(raw) > 7 else ""
        else:
            indicator = " "
            code_area = raw

        if indicator in ("*", "/"):
            continue

        if indicator == "-":
            cont = code_area.lstrip()
            if cont.startswith("'") or cont.startswith('"'):
                cont = cont[1:]
            pending = pending + cont
            continue

        if pending:
            result_lines.append((pending_lineno, pending.strip()))
        pending = code_area
        pending_lineno = lineno

    if pending:
        result_lines.append((pending_lineno, pending.strip()))

    return result_lines


def _locate_data_section(
    logical_lines: list[tuple[int, str]],
) -> list[tuple[int, str]]:
    """
    Return logical lines from the EARLIEST data section header through
    (but not including) PROCEDURE DIVISION.

    Collects FILE SECTION, WORKING-STORAGE SECTION, LINKAGE SECTION,
    LOCAL-STORAGE SECTION — whichever comes first is the slice start.
    All lines up to PROCEDURE DIVISION are included so programs where
    FILE SECTION precedes WORKING-STORAGE (e.g. CBACT01C) still expose
    their COPY statements.
    """
    start_idx = None
    end_idx   = len(logical_lines)

    for idx, (lineno, line) in enumerate(logical_lines):
        u = line.upper()
        is_data_header = (
            ("FILE" in u and "SECTION" in u) or
            "WORKING-STORAGE" in u or
            ("LINKAGE" in u and "SECTION" in u) or
            ("LOCAL-STORAGE" in u and "SECTION" in u)
        )
        if start_idx is None and is_data_header:
            start_idx = idx
        if "PROCEDURE" in u and "DIVISION" in u:
            end_idx = idx
            break

    if start_idx is None:
        return []
    return logical_lines[start_idx:end_idx]


# ---------------------------------------------------------------------------
# 4.  PIC LENGTH CALCULATOR
# ---------------------------------------------------------------------------

def pic_length(pic: str, storage: str) -> Optional[int]:
    """
    Compute byte length from PIC clause string + storage class.

    DISPLAY       : 1 byte per expanded character position (S and V free).
    COMP-3        : ceil((digit_count + 1) / 2).
    COMP / BINARY : 2 bytes (<=4 digits), 4 bytes (5-9), 8 bytes (10-18).
    INDEX/POINTER : 4 bytes fixed.

    Returns None for unrecognized PIC / storage.
    """
    storage_upper = storage.upper()
    pic_upper     = pic.upper().strip()

    def expand_count(pic_str: str) -> int:
        total = 0
        i = 0
        while i < len(pic_str):
            ch = pic_str[i]
            if ch in ("(", ")"):
                i += 1; continue
            if ch in ("S", "V", "+", "-", ".", ",", "$", "*", "B", "0"):
                i += 1; continue
            j = i + 1
            if j < len(pic_str) and pic_str[j] == "(":
                k = pic_str.index(")", j)
                total += int(pic_str[j+1:k])
                i = k + 1
            else:
                total += 1
                i += 1
        return total

    def digit_count(pic_str: str) -> int:
        total = 0
        i = 0
        while i < len(pic_str):
            ch = pic_str[i]
            if ch in ("S", "V", "+", "-", ".", ",", "$", "*", "B", "0",
                      "X", "A", "(", ")"):
                i += 1; continue
            if ch in ("9", "Z", "P"):
                j = i + 1
                if j < len(pic_str) and pic_str[j] == "(":
                    k = pic_str.index(")", j)
                    total += int(pic_str[j+1:k])
                    i = k + 1
                else:
                    total += 1
                    i += 1
            else:
                i += 1
        return total

    if storage_upper in ("COMP-3", "PACKED-DECIMAL"):
        digits = digit_count(pic_upper)
        return math.ceil((digits + 1) / 2) if digits > 0 else None

    if storage_upper in ("COMP", "BINARY", "COMP-4", "COMP-5"):
        digits = digit_count(pic_upper)
        if digits == 0: return None
        if digits <= 4:  return 2
        if digits <= 9:  return 4
        return 8

    if storage_upper in ("INDEX", "POINTER"):
        return 4

    if storage_upper in ("DISPLAY", "DISPLAY-1", ""):
        total = expand_count(pic_upper)
        return total if total > 0 else None

    return None


# ---------------------------------------------------------------------------
# 5.  PARSE NODE
# ---------------------------------------------------------------------------

@dataclass
class _Node:
    level:        int
    name:         str
    pic:          Optional[str]  = None
    storage:      str            = "DISPLAY"
    redefines:    Optional[str]  = None
    synchronized: bool           = False
    occurs:       int            = 1
    source_line:  int            = 0
    children:     list           = field(default_factory=list)
    copybook:     Optional[str]  = None


# ---------------------------------------------------------------------------
# 6.  LINE TOKENIZER
# ---------------------------------------------------------------------------

def _parse_node_from_line(
    lineno:   int,
    line:     str,
    copybook: Optional[str] = None,
) -> Optional[_Node]:
    m = RE_LEVEL.match(line)
    if not m:
        return None

    level = int(m.group(1))
    name  = m.group(2).upper()
    rest  = m.group(3)

    if level == 88: return None
    if level == 66: return None

    rest_no_value = RE_VALUE.split(rest)[0] if RE_VALUE.search(rest) else rest

    pic_raw: Optional[str] = None
    pm = RE_PIC.search(rest_no_value)
    if pm:
        pic_raw = (pm.group(1) or pm.group(2)).upper()

    storage = "DISPLAY"
    cm = RE_COMP.search(rest_no_value)
    if cm:
        storage = _STORAGE_NORM.get(cm.group(1).upper(), "DISPLAY")

    redef: Optional[str] = None
    rm = RE_REDEF.search(rest_no_value)
    if rm:
        redef = rm.group(1).upper()

    sync   = bool(RE_SYNC.search(rest_no_value))
    occurs = 1
    om     = RE_OCCUR.search(rest_no_value)
    if om:
        occurs = int(om.group(1))

    return _Node(
        level        = level,
        name         = name,
        pic          = pic_raw,
        storage      = storage,
        redefines    = redef,
        synchronized = sync,
        occurs       = occurs,
        source_line  = lineno,
        children     = [],
        copybook     = copybook,
    )


# ---------------------------------------------------------------------------
# 7.  COPYBOOK EXPANDER
# ---------------------------------------------------------------------------

def _find_copybook(
    name:             str,
    source_path:      Optional[Path],
    cpy_dir_override: Optional[Path] = None,
) -> Optional[Path]:
    candidates: list[Path] = []
    env_dir = os.environ.get("HERMES_CPY_DIR")
    if cpy_dir_override:
        candidates.append(cpy_dir_override)
    if source_path:
        candidates.append(source_path.parent / CPY_DIR_DEFAULT)
        candidates.append(source_path.parent.parent / CPY_DIR_DEFAULT)
    if env_dir:
        candidates.append(Path(env_dir))
    candidates.append(Path(CPY_DIR_DEFAULT))

    exts = ["", ".cpy", ".CPY", ".cbl", ".CBL"]
    for base in candidates:
        for ext in exts:
            p = base / (name + ext)
            if p.exists():
                return p
    return None


def _expand_copies(
    logical_lines: list[tuple[int, str]],
    source_path:   Optional[Path],
    unresolved:    list[dict],
    program:       str,
    visited:       Optional[set] = None,
) -> list[tuple[int, str, Optional[str]]]:
    """
    Expand COPY statements inline.

    Uses plain startswith("COPY ") check on the stripped logical line
    rather than a MULTILINE regex on already-joined lines.
    """
    if visited is None:
        visited = set()

    result: list[tuple[int, str, Optional[str]]] = []

    for lineno, line in logical_lines:
        stripped = line.strip()
        if stripped.upper().startswith("COPY "):
            cm = RE_COPY_INLINE.match(stripped)
            if not cm:
                result.append((lineno, line, None))
                continue
            cpy_name = cm.group(1).upper()

            if cpy_name in visited:
                unresolved.append({
                    "program":  program,
                    "copybook": cpy_name,
                    "reason":   "circular_copy_skipped",
                })
                continue

            cpy_path = _find_copybook(cpy_name, source_path)
            if cpy_path is None:
                unresolved.append({
                    "program":  program,
                    "copybook": cpy_name,
                    "reason":   "copybook_not_found",
                })
                continue

            cpy_text    = cpy_path.read_text(encoding="utf-8", errors="replace")
            cpy_logical = _strip_and_join(cpy_text)
            visited.add(cpy_name)
            expanded = _expand_copies(
                cpy_logical, cpy_path, unresolved, program, visited
            )
            for (cln, cline, nested_cpy) in expanded:
                result.append((cln, cline, nested_cpy or cpy_name))
        else:
            result.append((lineno, line, None))

    return result


# ---------------------------------------------------------------------------
# 8.  TREE BUILDER
# ---------------------------------------------------------------------------

def _build_trees(
    expanded: list[tuple[int, str, Optional[str]]],
) -> list[_Node]:
    roots: list[_Node] = []
    stack: list[_Node] = []

    for lineno, line, copybook in expanded:
        u = line.upper().strip()
        if u.startswith("FD ") or u.startswith("SD "):
            continue
        if any(kw in u for kw in (
            "WORKING-STORAGE", "FILE SECTION", "LINKAGE SECTION",
            "LOCAL-STORAGE", "PROCEDURE DIVISION", "DATA DIVISION",
        )):
            continue

        node = _parse_node_from_line(lineno, line, copybook)
        if node is None:
            continue

        if node.level in (1, 77):
            roots.append(node)
            stack = [node]
        else:
            while stack and stack[-1].level >= node.level:
                stack.pop()
            if stack:
                stack[-1].children.append(node)
            else:
                roots.append(node)
            stack.append(node)

    return roots


# ---------------------------------------------------------------------------
# 9.  OFFSET ASSIGNMENT
# ---------------------------------------------------------------------------

def _assign_offsets(
    nodes:        list[_Node],
    start_offset: int,
    unresolved:   list[dict],
    program:      str,
    parent_qname: str,
    occurs_stack: list[int],
) -> tuple[list[dict], int]:
    """
    Walk sibling nodes in source order, assign byte offsets, return flat list.

    Key correctness points:
    - Elementary OCCURS n: cursor advances by base_len * n; the field
      dict records the base length and occurs count separately.
    - Group OCCURS n: one_occ_size = child_end - group_start (size of ONE
      occurrence); total_size = one_occ_size * n.  The cursor advances by
      total_size so the NEXT sibling starts correctly.
    - Nested OCCURS: handled naturally because each level's group header
      gets total_size = (its own one_occ_size) * (its own occurs), and
      the parent's one_occ_size is measured from child_end which already
      reflects the inner multiplication.
    - Group header insert: insert_pos is captured BEFORE extending with
      child_fields so it always points at the right slot.
    - REDEFINES: cursor resets to target's start offset before processing
      the redefining item.
    """
    fields: list[dict] = []
    cursor = start_offset
    redef_offset_map: dict[str, int] = {}
    redef_high_water:  dict[str, int] = {}

    for node in nodes:
        qname = f"{parent_qname}.{node.name}" if parent_qname else node.name

        if node.redefines is not None:
            target = node.redefines.upper()
            target_offset = redef_offset_map.get(target)
            if target_offset is not None:
                cursor = target_offset

        redef_offset_map[node.name.upper()] = cursor

        if node.pic is not None:
            # ------- Elementary item -------
            base_len = pic_length(node.pic, node.storage)
            if base_len is None:
                unresolved.append({
                    "program": program,
                    "field":   qname,
                    "reason":  "unrecognized_pic",
                    "pic":     node.pic,
                })
                fields.append({
                    "qualified_name":  qname,
                    "level":           node.level,
                    "offset":          cursor,
                    "length":          None,
                    "pic":             node.pic,
                    "storage":         node.storage,
                    "redefines":       node.redefines,
                    "synchronized":    node.synchronized,
                    "occurs":          node.occurs,
                    "copybook":        node.copybook,
                    "_offset_drifted": True,
                })
            else:
                offset_here = cursor
                if node.synchronized and node.storage in ("COMP", "BINARY"):
                    alignment = base_len
                    slack = (alignment - (cursor % alignment)) % alignment
                    cursor += slack
                    offset_here = cursor

                fields.append({
                    "qualified_name": qname,
                    "level":          node.level,
                    "offset":         offset_here,
                    "length":         base_len,
                    "pic":            node.pic,
                    "storage":        node.storage,
                    "redefines":      node.redefines,
                    "synchronized":   node.synchronized,
                    "occurs":         node.occurs,
                    "copybook":       node.copybook,
                })
                cursor += base_len * node.occurs

                if node.redefines:
                    hw = redef_high_water.get(node.redefines.upper(), 0)
                    redef_high_water[node.redefines.upper()] = max(hw, cursor)

        else:
            # ------- Group item -------
            group_start = cursor

            # Capture insert position BEFORE extending with children
            insert_pos = len(fields)

            child_fields, child_end = _assign_offsets(
                node.children,
                cursor,
                unresolved,
                program,
                qname,
                occurs_stack + [node.occurs],
            )

            one_occ_size = child_end - group_start
            total_size   = one_occ_size * node.occurs

            fields.insert(insert_pos, {
                "qualified_name": qname,
                "level":          node.level,
                "offset":         group_start,
                "length":         total_size,
                "pic":            None,
                "storage":        "GROUP",
                "redefines":      node.redefines,
                "synchronized":   False,
                "occurs":         node.occurs,
                "copybook":       node.copybook,
            })
            fields.extend(child_fields)

            cursor = group_start + total_size

            if node.redefines:
                target = node.redefines.upper()
                hw = redef_high_water.get(target, 0)
                redef_high_water[target] = max(hw, cursor)

    for hw in redef_high_water.values():
        if hw > cursor:
            cursor = hw

    return fields, cursor


# ---------------------------------------------------------------------------
# 10. RECORD BUILDER
# ---------------------------------------------------------------------------

def _build_record(
    root:       _Node,
    unresolved: list[dict],
    program:    str,
) -> dict:
    """
    Convert a 01-level root _Node into the output record dict.

    FIX (v1.2.2): elementary 01-level roots (pic != None, no children)
    were getting total_bytes=None because _assign_offsets([]) returns
    end_offset=0.  Detect this case first and compute total_bytes directly
    from pic_length, emitting a single self-field dict at offset=0.
    """
    redefines_groups: list[dict] = []

    # --- Elementary 01-level (e.g. 01 WS-X REDEFINES Y PIC X(10)) ---
    if root.pic is not None:
        base_len = pic_length(root.pic, root.storage)
        total    = base_len * root.occurs if base_len is not None else None
        if base_len is None:
            unresolved.append({
                "program": program,
                "field":   root.name,
                "reason":  "unrecognized_pic",
                "pic":     root.pic,
            })
        clean_fields = [{
            "qualified_name": root.name,
            "level":          root.level,
            "offset":         0,
            "length":         base_len,
            "pic":            root.pic,
            "storage":        root.storage,
            "redefines":      root.redefines,
            "synchronized":   root.synchronized,
            "occurs":         root.occurs,
        }]
        if root.redefines:
            redefines_groups.append({
                "name":             root.name,
                "redefines_target": root.redefines,
                "total_bytes":      total,
                "level":            1,
            })
        return {
            "name":             root.name,
            "copybook":         root.copybook,
            "total_bytes":      total,
            "fields":           clean_fields,
            "redefines_groups": redefines_groups,
        }

    # --- Group 01-level (normal case) ---
    flat_fields, end_offset = _assign_offsets(
        root.children,
        start_offset  = 0,
        unresolved    = unresolved,
        program       = program,
        parent_qname  = root.name,
        occurs_stack  = [root.occurs],
    )

    seen_redef: set[str] = set()
    for f in flat_fields:
        if f.get("redefines") and f["qualified_name"] not in seen_redef:
            seen_redef.add(f["qualified_name"])
            redefines_groups.append({
                "name":             f["qualified_name"],
                "redefines_target": f["redefines"],
                "total_bytes":      f["length"],
            })

    clean_fields = []
    for f in flat_fields:
        cf = {
            "qualified_name": f["qualified_name"],
            "level":          f["level"],
            "offset":         f["offset"],
            "length":         f["length"],
            "pic":            f["pic"],
            "storage":        f["storage"],
            "redefines":      f["redefines"],
            "synchronized":   f["synchronized"],
            "occurs":         f["occurs"],
        }
        if f.get("copybook"):
            cf["copybook"] = f["copybook"]
        clean_fields.append(cf)

    total = end_offset if end_offset > 0 else None

    return {
        "name":             root.name,
        "copybook":         root.copybook,
        "total_bytes":      total,
        "fields":           clean_fields,
        "redefines_groups": redefines_groups,
    }


# ---------------------------------------------------------------------------
# 11. TOP-LEVEL EXTRACT
# ---------------------------------------------------------------------------

def extract_layout(
    source:      str,
    program:     str,
    source_path: Optional[Path] = None,
) -> dict:
    """
    Extract byte layouts for all data records in a COBOL program.
    """
    unresolved: list[dict] = []

    logical_lines = _strip_and_join(source)
    data_lines    = _locate_data_section(logical_lines)
    expanded      = _expand_copies(data_lines, source_path, unresolved, program)
    roots         = _build_trees(expanded)

    records: list[dict] = []
    for root in roots:
        if root.level not in (1, 77):
            continue
        records.append(_build_record(root, unresolved, program))

    return {
        "program":        program.upper(),
        "schema_version": "1.2",
        "records":        records,
        "unresolved":     unresolved,
    }


# ---------------------------------------------------------------------------
# 12. CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python byte_layout.py <file.cbl> [output.json]", file=sys.stderr)
        sys.exit(1)

    src_path = Path(sys.argv[1])
    if not src_path.exists():
        print(f"ERROR: file not found: {src_path}", file=sys.stderr)
        sys.exit(2)

    source_text = src_path.read_text(encoding="utf-8", errors="replace")
    result      = extract_layout(source_text, src_path.stem.upper(), src_path)
    out_json    = json.dumps(result, indent=2)

    if len(sys.argv) >= 3:
        Path(sys.argv[2]).write_text(out_json, encoding="utf-8")
        print(f"Written to {sys.argv[2]}", file=sys.stderr)
    else:
        print(out_json)

    n_records  = len(result["records"])
    n_fields   = sum(len(r["fields"]) for r in result["records"])
    n_unresolv = len(result["unresolved"])
    print(
        f"\nLayout summary: {n_records} records, {n_fields} fields, "
        f"{n_unresolv} unresolved",
        file=sys.stderr,
    )

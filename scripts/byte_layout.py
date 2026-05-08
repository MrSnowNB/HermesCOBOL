#!/usr/bin/env python3
# LLM-FREE — Deterministic COBOL byte layout extraction. No LLM inference.
"""
byte_layout.py
==============
HermesCOBOL v1.2 — Byte Layout Extractor.

Emits exact byte offsets, widths, storage class, SYNCHRONIZED slack, and
REDEFINES overlays for every data item in every record (01-level) found in
WORKING-STORAGE, FILE SECTION, and LINKAGE SECTION of a COBOL program,
including records pulled in via COPY statements.

This is the prerequisite for Section 2 (data flow) and all 1:1 translation
validation claims.

Ported and simplified from CardDemo extract_byte_layout.py.
Deterministic. No LLM. Standard library only.

Key design decisions
--------------------
1. Unrecognized PIC clause:
   - Appended to the top-level unresolved[] list as
     {"program": P, "field": F, "reason": "unrecognized_pic", "pic": raw}.
   - A placeholder field record is still emitted with length=null so that
     the running offset cursor is explicitly marked as drifted rather than
     silently wrong.  Downstream consumers must check for null lengths.

2. Copybook expansion:
   - COPY <name> statements are resolved against CPY_DIR (default:
     data/raw/cpy relative to the program file's directory).
   - If the copybook file is not found, a record
     {"program": P, "copybook": name, "reason": "copybook_not_found"}
     is appended to unresolved[] and parsing continues.

3. OCCURS multiplier:
   - OCCURS n TIMES multiplies the full subtree byte size of the group it
     decorates, not just the immediate PIC.  This is computed during the
     post-walk offset assignment pass, not during parsing.
   - Nested OCCURS (e.g. OCCURS 12 inside OCCURS 50) multiply correctly:
     the inner group size is multiplied by its own occurs count, and then
     the outer group size (which includes the inner subtree) is multiplied
     by the outer occurs count.

4. REDEFINES:
   - The offset cursor resets to the start offset of the field being
     redefined.  All fields in the redefines group share the same start
     offset.
   - redefines_groups[] on the record lists {name, redefines_target,
     total_bytes} for each REDEFINES chain.

5. SYNCHRONIZED:
   - COMP (BINARY) fields with SYNCHRONIZED are padded to a 2-byte boundary
     for fields up to 4 digits, 4-byte boundary for 5–9 digits, 8-byte
     boundary for 10–18 digits.  The slack bytes are not represented as
     fields but are accounted for in the running offset.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

__LLM_FREE__ = True

# ---------------------------------------------------------------------------
# 1.  CONSTANTS
# ---------------------------------------------------------------------------

# Default copybook search directory (relative to the .cbl file being parsed).
# Override by setting env var HERMES_CPY_DIR to an absolute path.
CPY_DIR_DEFAULT = "data/raw/cpy"

# Storage class normalisation map.
# Maps PIC clause modifiers -> canonical storage name used in output.
_STORAGE_NORM: dict[str, str] = {
    "COMP-3":          "COMP-3",
    "PACKED-DECIMAL":  "COMP-3",   # IBM synonym
    "COMP-4":          "COMP",
    "COMP-5":          "COMP",
    "COMP":            "COMP",
    "BINARY":          "COMP",     # IBM synonym
    "DISPLAY":         "DISPLAY",
    "DISPLAY-1":       "DISPLAY",  # DBCS -- treat as DISPLAY for byte count
    "INDEX":           "COMP",     # treated as 4-byte COMP
    "POINTER":         "COMP",     # 4 or 8 bytes; assume 4
}

# ---------------------------------------------------------------------------
# 2.  REGEX LIBRARY
# ---------------------------------------------------------------------------

# Any two-digit level number at Area A/B, followed by an identifier.
# Group 1 = level (zero-padded 2-digit string)
# Group 2 = data name or FILLER
# Group 3 = remainder of the logical line (PIC, COMP, REDEFINES, etc.)
RE_LEVEL = re.compile(
    r"^\s*(\d{2})\s+([A-Z0-9][A-Z0-9\-]*)\b(.*)",
    re.IGNORECASE,
)

# PIC / PICTURE clause: captures the picture string (everything up to the
# next whitespace or period, after optional whitespace).
RE_PIC = re.compile(r"\bPIC(?:TURE)?\s+IS\s+([^\s.]+)|\bPIC(?:TURE)?\s+([^\s.]+)", re.IGNORECASE)

# Storage class keyword anywhere on the logical line.
RE_COMP = re.compile(
    r"\b(COMP-3|COMP-4|COMP-5|COMP|BINARY|PACKED-DECIMAL|DISPLAY-1|DISPLAY|INDEX|POINTER)\b",
    re.IGNORECASE,
)

# REDEFINES <target-name>
RE_REDEF = re.compile(r"\bREDEFINES\s+([A-Z0-9][A-Z0-9\-]*)", re.IGNORECASE)

# SYNCHRONIZED (or SYNC)
RE_SYNC = re.compile(r"\bSYNCHRONIZED\b|\bSYNC\b", re.IGNORECASE)

# OCCURS <n> [TIMES]
RE_OCCUR = re.compile(r"\bOCCURS\s+(\d+)(?:\s+TIMES)?\b", re.IGNORECASE)

# VALUE clause start (skip to avoid treating VALUE literals as field names)
RE_VALUE = re.compile(r"\bVALUE\b", re.IGNORECASE)

# COPY <copybook-name>
RE_COPY = re.compile(r"^\s*COPY\s+([A-Z0-9][A-Z0-9\-]*)\s*\.?\s*$", re.IGNORECASE | re.MULTILINE)

# Division / section headers that delimit data areas.
RE_WORKING_STORAGE  = re.compile(r"^\s*WORKING-STORAGE\s+SECTION", re.I | re.M)
RE_FILE_SECTION     = re.compile(r"^\s*FILE\s+SECTION", re.I | re.M)
RE_LINKAGE_SECTION  = re.compile(r"^\s*LINKAGE\s+SECTION", re.I | re.M)
RE_PROCEDURE_DIV    = re.compile(r"^\s*PROCEDURE\s+DIVISION", re.I | re.M)

# Fixed-format comment line indicator (col 7, 0-based index 6).
# Also catches continuation lines (col 7 = '-').

# ---------------------------------------------------------------------------
# 3.  TEXT PREPARATION
# ---------------------------------------------------------------------------

def _strip_and_join(text: str) -> str:
    """
    Prepare COBOL fixed-format source for parsing:
      1. Strip comment lines (col 7 = '*' or '/').
      2. Join continuation lines (col 7 = '-') by appending the continuation
         area (cols 8-72) to the previous logical line.
      3. Strip identification area (cols 73+) and sequence numbers (cols 1-6).
      4. Replace COPY statements with inline expansion markers handled later.

    Returns a list of (original_lineno, logical_line) tuples where
    logical_line is the joined, stripped text of each logical COBOL line.
    """
    result_lines: list[tuple[int, str]] = []
    pending: str = ""
    pending_lineno: int = 1

    for lineno, raw in enumerate(text.splitlines(), start=1):
        # Extract indicator and code area for fixed-format (80-col) lines.
        if len(raw) >= 7:
            indicator = raw[6]        # col 7 (0-based index 6)
            code_area = raw[7:72] if len(raw) > 7 else ""
        else:
            # Short line: no indicator column, treat as code
            indicator = " "
            code_area = raw

        if indicator in ("*", "/"):
            # Comment line: discard
            continue

        if indicator == "-":
            # Continuation: append to pending (strip leading whitespace/quote)
            cont = code_area.lstrip()
            # Remove leading quote if this is a literal continuation
            if cont.startswith("'") or cont.startswith('"'):
                cont = cont[1:]
            pending = pending + cont
            continue

        # Normal line: flush pending if any, start new logical line
        if pending:
            result_lines.append((pending_lineno, pending.strip()))
        pending = code_area
        pending_lineno = lineno

    if pending:
        result_lines.append((pending_lineno, pending.strip()))

    return result_lines


def _locate_data_section(logical_lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """
    Return only the logical lines between the first data section header
    (WORKING-STORAGE, FILE SECTION, LINKAGE SECTION) and PROCEDURE DIVISION.

    We want all data declarations; sections are included in order.
    Returns the full slice so the caller can scan for 01-level roots.
    """
    start_idx = None
    end_idx   = len(logical_lines)

    for idx, (lineno, line) in enumerate(logical_lines):
        u = line.upper()
        if start_idx is None and (
            "WORKING-STORAGE" in u or
            ("FILE" in u and "SECTION" in u) or
            ("LINKAGE" in u and "SECTION" in u)
        ):
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

    Rules (derived from IBM COBOL Language Reference, same algorithm as
    CardDemo extract_byte_layout.py pic_size()):

    DISPLAY (default when no COMP clause):
      One byte per character position in the expanded PIC string.
      S (sign) adds 1 byte only in SIGN IS SEPARATE clause -- we do NOT
      add a sign byte for embedded sign (the default); the sign nibble is
      part of the last digit in DISPLAY numeric.  However, for byte-length
      purposes DISPLAY S9(n) == n bytes (sign is embedded).
      V (implicit decimal point) adds 0 bytes.
      Repetition factor: 9(5) expands to 5 digit positions.

    COMP-3 / PACKED-DECIMAL:
      Total digits = sum of all 9/Z/P positions (ignore V and S).
      Byte length = ceil((digits + 1) / 2).
      The +1 accounts for the sign nibble stored in the last half-byte.

    COMP / BINARY (including COMP-4, COMP-5, INDEX, POINTER):
      Total digits = sum of all 9 positions.
      <= 4 digits  -> 2 bytes
      5-9 digits   -> 4 bytes
      10-18 digits -> 8 bytes
      (Standard IBM COBOL sizing per ILE/VSAM rules.)

    Returns None for unrecognized PIC strings so callers can add to
    unresolved[] and emit a length=null placeholder.
    """
    storage_upper = storage.upper()
    pic_upper     = pic.upper().strip()

    # Count digit positions by expanding repetition factors:
    # 9(5) -> 5 nines, X(10) -> 10 X's, A(3) -> 3 A's, etc.
    def expand_count(pic_str: str) -> int:
        """Return total character positions in the PIC string."""
        total = 0
        i = 0
        while i < len(pic_str):
            ch = pic_str[i]
            if ch in ("(",):
                i += 1
                continue
            if ch == ")":
                i += 1
                continue
            if ch in ("S", "V", "+", "-", ".", ",", "$", "*", "B", "0"):
                # non-byte-contributing characters for length purposes
                i += 1
                continue
            # Look ahead for repetition factor (n)
            j = i + 1
            if j < len(pic_str) and pic_str[j] == "(":
                k = pic_str.index(")", j)
                count = int(pic_str[j+1:k])
                total += count
                i = k + 1
            else:
                total += 1
                i += 1
        return total

    # Count only numeric digit positions (9, Z, P) for COMP-3 / COMP
    def digit_count(pic_str: str) -> int:
        """Count only 9/Z/P positions (ignore X, A, S, V, etc.)."""
        total = 0
        i = 0
        while i < len(pic_str):
            ch = pic_str[i]
            if ch in ("S", "V", "+", "-", ".", ",", "$", "*", "B", "0", "X", "A"):
                i += 1
                continue
            if ch == "(":
                i += 1
                continue
            if ch == ")":
                i += 1
                continue
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
                # Unknown character: skip
                i += 1
        return total

    # COMP-3 / PACKED-DECIMAL
    if storage_upper in ("COMP-3", "PACKED-DECIMAL"):
        digits = digit_count(pic_upper)
        if digits == 0:
            return None  # unrecognized
        return math.ceil((digits + 1) / 2)

    # COMP / BINARY variants
    if storage_upper in ("COMP", "BINARY", "COMP-4", "COMP-5"):
        digits = digit_count(pic_upper)
        if digits == 0:
            return None
        if digits <= 4:
            return 2
        if digits <= 9:
            return 4
        return 8  # up to 18 digits

    # INDEX and POINTER: fixed 4 bytes
    if storage_upper in ("INDEX", "POINTER"):
        return 4

    # DISPLAY (default): one byte per expanded character position
    if storage_upper in ("DISPLAY", "DISPLAY-1", ""):
        total = expand_count(pic_upper)
        return total if total > 0 else None

    return None  # unknown storage class


# ---------------------------------------------------------------------------
# 5.  PARSE NODE (internal tree representation)
# ---------------------------------------------------------------------------

@dataclass
class _Node:
    """
    Internal tree node for one data item during the walk.

    level        : COBOL level number (01-49, 66, 77, 88)
    name         : data name (upper-cased) or FILLER
    pic          : raw PIC string or None (group items have no PIC)
    storage      : normalised storage class (DISPLAY, COMP-3, COMP, etc.)
    redefines    : name of item being redefined, or None
    synchronized : True if SYNCHRONIZED clause present
    occurs       : repetition count from OCCURS n clause, or 1
    source_line  : 1-based line number in original source
    children     : child nodes (subordinate levels)
    copybook     : copybook name if this node came from a COPY expansion
    """
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
# 6.  LOGICAL LINE TOKENIZER
# ---------------------------------------------------------------------------

def _parse_node_from_line(
    lineno: int,
    line:   str,
    copybook: Optional[str] = None,
) -> Optional[_Node]:
    """
    Parse one logical COBOL data-definition line into a _Node.

    Returns None if the line does not match a level-number pattern
    (e.g. section headers, FD statements, blank lines).
    """
    m = RE_LEVEL.match(line)
    if not m:
        return None

    level_str = m.group(1)
    name      = m.group(2).upper()
    rest      = m.group(3)  # everything after the data name

    # Skip level 66 (RENAMES), 77 (independent items treated as 01),
    # 88 (condition names -- no storage).
    # We parse 77 as a standalone field (treat like level 01).
    level = int(level_str)
    if level == 88:
        return None   # condition name, no storage
    if level == 66:
        return None   # RENAMES -- complex alias, skip for now

    # --- Extract clauses from remainder ---

    # Chop off VALUE clause to avoid false hits (e.g. VALUE SPACES matching
    # storage keywords).
    rest_no_value = RE_VALUE.split(rest)[0] if RE_VALUE.search(rest) else rest

    # PIC / PICTURE
    pic_raw: Optional[str] = None
    pm = RE_PIC.search(rest_no_value)
    if pm:
        pic_raw = (pm.group(1) or pm.group(2)).upper()

    # Storage class
    storage = "DISPLAY"
    cm = RE_COMP.search(rest_no_value)
    if cm:
        storage = _STORAGE_NORM.get(cm.group(1).upper(), "DISPLAY")

    # REDEFINES
    redef: Optional[str] = None
    rm = RE_REDEF.search(rest_no_value)
    if rm:
        redef = rm.group(1).upper()

    # SYNCHRONIZED
    sync = bool(RE_SYNC.search(rest_no_value))

    # OCCURS
    occurs = 1
    om = RE_OCCUR.search(rest_no_value)
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
    name: str,
    source_path: Optional[Path],
    cpy_dir_override: Optional[Path] = None,
) -> Optional[Path]:
    """
    Locate copybook file for COPY <name>.

    Search order:
      1. cpy_dir_override (if provided)
      2. data/raw/cpy relative to source_path's parent
      3. data/raw/cpy relative to CWD
      4. Env var HERMES_CPY_DIR

    Tries extensions: (none), .cpy, .CPY, .cbl, .CBL
    """
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
    source_path: Optional[Path],
    unresolved: list[dict],
    program: str,
    visited: Optional[set] = None,
) -> list[tuple[int, str, Optional[str]]]:
    """
    Expand COPY statements inline.

    Returns a list of (lineno, logical_line, copybook_name) tuples where
    copybook_name is None for lines from the main program.

    visited: set of already-expanded copybook names (prevents infinite loops
    from circular COPY chains, which are illegal in COBOL but defensive).
    """
    if visited is None:
        visited = set()

    result: list[tuple[int, str, Optional[str]]] = []

    for lineno, line in logical_lines:
        cm = RE_COPY.match(line)
        if cm:
            cpy_name = cm.group(1).upper()
            if cpy_name in visited:
                # Circular copy guard
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
            # Recurse: expand nested COPYs inside copybooks
            cpy_text    = cpy_path.read_text(encoding="utf-8", errors="replace")
            cpy_logical = _strip_and_join(cpy_text)
            visited.add(cpy_name)
            expanded = _expand_copies(
                cpy_logical, cpy_path, unresolved, program, visited
            )
            # Tag every line from this copybook with the copybook name
            for (cln, cline, nested_cpy) in expanded:
                result.append((cln, cline, nested_cpy or cpy_name))
        else:
            result.append((lineno, line, None))

    return result


# ---------------------------------------------------------------------------
# 8.  TREE BUILDER
#     Converts a flat list of (lineno, line, copybook) into a tree of _Nodes
#     rooted at 01-level items.
# ---------------------------------------------------------------------------

def _build_trees(
    expanded: list[tuple[int, str, Optional[str]]],
) -> list[_Node]:
    """
    Parse lines in order and build a list of 01-level (root) _Node trees.

    Uses a level-stack approach:
      - Push each new node onto a stack keyed by level number.
      - When a new node appears, find the deepest stack entry with a lower
        level number -- that is the parent.  Add the new node as a child.
      - Level 01 and 77 nodes are always roots.

    FD / SD lines are not 01-level data, so they are skipped.
    """
    roots: list[_Node]              = []
    stack: list[_Node]              = []   # stack[0] = most recent 01-root

    for lineno, line, copybook in expanded:
        # Skip FD / SD lines (file descriptors -- their 01 sub-items follow)
        u = line.upper().strip()
        if u.startswith("FD ") or u.startswith("SD "):
            continue
        # Skip section headers
        if any(kw in u for kw in (
            "WORKING-STORAGE", "FILE SECTION", "LINKAGE SECTION",
            "PROCEDURE DIVISION", "DATA DIVISION",
        )):
            continue

        node = _parse_node_from_line(lineno, line, copybook)
        if node is None:
            continue

        if node.level in (1, 77):
            # New root
            roots.append(node)
            stack = [node]
        else:
            # Find parent: deepest stack entry with level < current level
            while stack and stack[-1].level >= node.level:
                stack.pop()
            if stack:
                stack[-1].children.append(node)
            else:
                # Orphan (malformed source): treat as root
                roots.append(node)
            stack.append(node)

    return roots


# ---------------------------------------------------------------------------
# 9.  OFFSET ASSIGNMENT
#     Walk the tree and compute byte offsets. This is the core algorithm.
# ---------------------------------------------------------------------------

def _node_byte_size(
    node:       _Node,
    unresolved: list[dict],
    program:    str,
    parent_qname: str = "",
) -> Optional[int]:
    """
    Recursively compute the total byte size of a node (group or elementary).

    For group items (no PIC): size = sum of children sizes.
    For elementary items (has PIC): size = pic_length(pic, storage).
    Both are then multiplied by the node's own OCCURS count.

    REDEFINES: a node that redefines another item takes the MAX of its own
    subtree size and the target's size; however, for layout purposes we
    record only the node's own size and let the REDEFINES offset reset
    handle the overlap.  This function returns the node's OWN size.

    Returns None if any PIC is unrecognized (placeholder, offset drifted).
    """
    qname = f"{parent_qname}.{node.name}" if parent_qname else node.name

    if node.pic is not None:
        # Elementary item
        own_size = pic_length(node.pic, node.storage)
        if own_size is None:
            unresolved.append({
                "program": program,
                "field":   qname,
                "reason":  "unrecognized_pic",
                "pic":     node.pic,
            })
            return None
        # SYNCHRONIZED alignment (only for COMP/BINARY)
        if node.synchronized and node.storage in ("COMP", "BINARY"):
            boundary = own_size  # 2, 4, or 8 based on pic_length result
            # Slack handled externally during offset walk; size is unchanged
        return own_size * node.occurs
    else:
        # Group item: sum children
        total = 0
        for child in node.children:
            csz = _node_byte_size(child, unresolved, program, qname)
            if csz is None:
                return None   # propagate null: offsets are drifted
            total += csz
        return total * node.occurs


def _assign_offsets(
    nodes:       list[_Node],
    start_offset: int,
    unresolved:  list[dict],
    program:     str,
    parent_qname: str,
    occurs_stack: list[int],   # current multiplicative OCCURS context
) -> tuple[list[dict], int]:
    """
    Walk a list of sibling nodes in source order, assigning byte offsets.

    Returns (flat_fields_list, next_offset_after_siblings).

    flat_fields_list: list of field dicts in the output JSON schema:
      {qualified_name, level, offset, length, pic, storage,
       redefines, synchronized, copybook}

    REDEFINES handling:
      When a node has redefines != None, we look up the offset of the
      redefined field in the sibling list (redef_offset_map) and reset
      the cursor to that offset before walking the redefining item.
      The maximum of (cursor_after_redef_item, cursor_at_start_of_redef)
      is used as the cursor for the next non-redefines sibling.

    SYNCHRONIZED handling:
      After computing a COMP/BINARY field's length, if SYNCHRONIZED is set,
      advance the offset to the next multiple of the field's alignment
      boundary (i.e., add slack bytes between this field and the next).

    nested OCCURS:
      The occurs_stack tracks the cumulative OCCURS multiplier from all
      ancestor groups.  Each elementary field's effective length in the
      flat output is its own pic_length (NOT multiplied by ancestor occurs)
      because the flat list enumerates every logical field at its base
      position within one occurrence.  The total_bytes at the record level
      captures the full multiplied size.
    """
    fields: list[dict] = []
    cursor = start_offset

    # Map from data-name -> offset at which it starts (for REDEFINES lookup)
    redef_offset_map: dict[str, int] = {}

    for node in nodes:
        qname = f"{parent_qname}.{node.name}" if parent_qname else node.name

        # REDEFINES: reset cursor to the offset of the target
        if node.redefines is not None:
            target_offset = redef_offset_map.get(node.redefines.upper())
            if target_offset is not None:
                cursor = target_offset
            # else: target not found in siblings (malformed source); keep cursor

        # Record this node's start offset in the redef map (after reset)
        redef_offset_map[node.name.upper()] = cursor

        if node.pic is not None:
            # ---------- Elementary item ----------
            base_len = pic_length(node.pic, node.storage)
            if base_len is None:
                # Unrecognized PIC: emit placeholder, do NOT advance cursor
                unresolved.append({
                    "program": program,
                    "field":   qname,
                    "reason":  "unrecognized_pic",
                    "pic":     node.pic,
                })
                fields.append({
                    "qualified_name": qname,
                    "level":          node.level,
                    "offset":         cursor,
                    "length":         None,     # explicit null: offsets drifted
                    "pic":            node.pic,
                    "storage":        node.storage,
                    "redefines":      node.redefines,
                    "synchronized":   node.synchronized,
                    "occurs":         node.occurs,
                    "copybook":       node.copybook,
                    "_offset_drifted": True,
                })
                # cursor intentionally NOT advanced so error is visible
            else:
                # SYNCHRONIZED alignment: advance cursor to alignment boundary
                # before placing this field.
                offset_here = cursor
                if node.synchronized and node.storage in ("COMP", "BINARY"):
                    alignment = base_len  # 2, 4, or 8
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
        else:
            # ---------- Group item ----------
            group_start = cursor
            # Recurse into children with this node's OCCURS on the stack
            child_fields, child_end = _assign_offsets(
                node.children,
                cursor,
                unresolved,
                program,
                qname,
                occurs_stack + [node.occurs],
            )
            fields.extend(child_fields)

            # Size of one occurrence of this group
            one_occ_size = child_end - group_start
            # Total size including all occurrences
            total_size = one_occ_size * node.occurs

            # Emit the group header field itself
            fields.insert(
                # Insert group header before its children in flat list.
                # Find the insertion index: position just before the first
                # child we added.
                len(fields) - len(child_fields),
                {
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
                },
            )
            cursor = group_start + total_size

    return fields, cursor


# ---------------------------------------------------------------------------
# 10. RECORD BUILDER
#     Turns 01-level trees into the output records[] shape.
# ---------------------------------------------------------------------------

def _build_record(root: _Node, unresolved: list[dict], program: str) -> dict:
    """
    Convert a 01-level root _Node tree into the output record dict.

    record shape:
      {
        "name":             str,
        "copybook":         str | None,  (copybook name if record came from COPY)
        "total_bytes":      int | None,
        "fields":           [Field...],
        "redefines_groups": [{name, redefines_target, total_bytes}, ...]
      }
    """
    flat_fields, end_offset = _assign_offsets(
        root.children,
        start_offset  = 0,
        unresolved    = unresolved,
        program       = program,
        parent_qname  = root.name,
        occurs_stack  = [root.occurs],
    )

    # Collect redefines groups: all fields with a non-null redefines clause
    redefines_groups: list[dict] = []
    seen_redef: set[str] = set()
    for f in flat_fields:
        if f.get("redefines") and f["qualified_name"] not in seen_redef:
            seen_redef.add(f["qualified_name"])
            redefines_groups.append({
                "name":             f["qualified_name"],
                "redefines_target": f["redefines"],
                "total_bytes":      f["length"],
            })

    # Strip internal-only keys from field output
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

    # Total bytes is the end offset of the last child (covers all occurrences)
    total = end_offset if end_offset > 0 else None

    return {
        "name":             root.name,
        "copybook":         root.copybook,
        "total_bytes":      total,
        "fields":           clean_fields,
        "redefines_groups": redefines_groups,
    }


# ---------------------------------------------------------------------------
# 11. TOP-LEVEL EXTRACT FUNCTION
# ---------------------------------------------------------------------------

def extract_layout(
    source:      str,
    program:     str,
    source_path: Optional[Path] = None,
) -> dict:
    """
    Extract byte layouts for all data records in a COBOL program.

    Parameters
    ----------
    source      : raw COBOL source text.
    program     : program name (used in unresolved[] entries).
    source_path : Path object for the .cbl file (used to locate copybooks).

    Returns
    -------
    {
      "program":        str,
      "schema_version": "1.2",
      "records":        [record...],
      "unresolved":     [unresolved_entry...]
    }
    """
    unresolved: list[dict] = []

    # Step 1: strip comments and join continuation lines
    logical_lines = _strip_and_join(source)

    # Step 2: slice to data section only (before PROCEDURE DIVISION)
    data_lines = _locate_data_section(logical_lines)

    # Step 3: expand COPY statements
    expanded = _expand_copies(
        data_lines, source_path, unresolved, program
    )

    # Step 4: build node trees
    roots = _build_trees(expanded)

    # Step 5: build record dicts from 01-level roots
    records: list[dict] = []
    for root in roots:
        if root.level not in (1, 77):
            continue  # should not happen after _build_trees, defensive
        records.append(_build_record(root, unresolved, program))

    return {
        "program":        program.upper(),
        "schema_version": "1.2",
        "records":        records,
        "unresolved":     unresolved,
    }


# ---------------------------------------------------------------------------
# 12. CLI ENTRY POINT
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
    result = extract_layout(source_text, src_path.stem.upper(), src_path)

    out_json = json.dumps(result, indent=2)

    if len(sys.argv) >= 3:
        Path(sys.argv[2]).write_text(out_json, encoding="utf-8")
        print(f"Written to {sys.argv[2]}", file=sys.stderr)
    else:
        print(out_json)

    # Summary to stderr
    n_records  = len(result["records"])
    n_fields   = sum(len(r["fields"]) for r in result["records"])
    n_unresolv = len(result["unresolved"])
    print(
        f"\nLayout summary: {n_records} records, {n_fields} fields, "
        f"{n_unresolv} unresolved",
        file=sys.stderr,
    )

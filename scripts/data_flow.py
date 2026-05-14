#!/usr/bin/env python3
"""
data_flow.py  --  Section 2/3: deterministic per-paragraph reads[]/mutates[] extractor.

Usage:
    single program : python scripts/data_flow.py data/raw/cbl/CBACT01C.cbl
    corpus batch   : python scripts/data_flow.py --all

Output is written to stdout (single) or data/data_flow/<PROGRAM>.json (batch).
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SCHEMA_VERSION = "1.3"
BYTE_LAYOUTS_DIR = Path("data/byte_layouts")
CBL_DIR          = Path("data/raw/cbl")
OUT_DIR          = Path("data/data_flow")
FACTS_DIR        = Path("data/facts")

_SEQ_RE = re.compile(r'^\d{6}(.*)$')   # kept for backward compat; NOT used in _normalise_source
_LITERAL_RE = re.compile(
    r"^(?:'[^']*'|\"[^\"]*\"|[-+]?\d+\.?\d*"
    r"|ZERO|ZEROS|ZEROES|SPACES|SPACE|HIGH-VALUES|LOW-VALUES"
    r"|ALL\s+'[^']+'|TRUE|FALSE)$",
    re.IGNORECASE
)

_NOT_PARA = frozenset({
    'END-PERFORM', 'END-IF', 'END-EVALUATE', 'END-READ', 'END-WRITE',
    'END-COMPUTE', 'END-ADD', 'END-SUBTRACT', 'END-MULTIPLY', 'END-DIVIDE',
    'END-STRING', 'END-UNSTRING', 'END-EXEC', 'END-CALL',
    'GOBACK', 'STOP', 'EXIT', 'CONTINUE', 'NEXT',
    'ELSE', 'THEN', 'WHEN', 'OTHER',
})

_NOT_HEADER_KEYWORDS = frozenset({
    'IDENTIFICATION', 'ENVIRONMENT', 'DATA', 'PROCEDURE',
    'WORKING-STORAGE', 'LINKAGE', 'FILE', 'LOCAL-STORAGE',
    'INPUT-OUTPUT', 'CONFIGURATION', 'COMMUNICATION', 'REPORT',
    'FILE-CONTROL', 'SPECIAL-NAMES', 'SOURCE-COMPUTER', 'OBJECT-COMPUTER',
    'REPOSITORY', 'CLASS-CONTROL',
})

_LEVEL_NUM_RE = re.compile(r'^\d{2}\s')

_PARA_HEADER_RE = re.compile(
    r'^([A-Z0-9][A-Z0-9\-]*)\s*\.\s*$',
    re.IGNORECASE
)

_SECTION_HEADER_RE = re.compile(
    r'^([A-Z0-9][A-Z0-9\-]*)\s+SECTION\b',
    re.IGNORECASE
)

_CALL_TARGET_RE = re.compile(
    r'^CALL\s+(?:\'([^\']+)\'|"([^"]+)"|([A-Z0-9][A-Z0-9\-]*))',
    re.IGNORECASE
)

# ---------------------------------------------------------------------------
# Intrinsic and connective skip sets (STEP 2: Patch 2)
# ---------------------------------------------------------------------------

_INTRINSICS = frozenset({
    "FUNCTION",
    "UPPER-CASE",
    "LOWER-CASE",
    "TRIM",
    "LENGTH",
    "NUMVAL",
    "NUMVAL-C",
    "CURRENT-DATE",
    "INTEGER",
    "INTEGER-OF-DATE",
    "DATE-OF-INTEGER",
    "WHEN-COMPILED",
    "RANDOM",
    "MOD",
})

_CONNECTIVES = frozenset({
    "TO",
    "FROM",
    "BY",
    "INTO",
    "USING",
    "GIVING",
    "UPON",
    "THRU",
    "THROUGH",
    "TIMES",
    "UNTIL",
    "VARYING",
    "IS",
    "ARE",
    "NOT",
    "AND",
    "OR",
    "OF",
    "IN",
    "THEN",
    "ELSE",
    "WHEN",
    "ON",
    "SIZE",
    "ERROR",
    "AT",
    "END",
    "KEY",
    "EQUAL",
    "GREATER",
    "LESS",
    "THAN",
    "ZERO",
    "ZEROS",
    "ZEROES",
    "SPACE",
    "SPACES",
    "HIGH-VALUE",
    "HIGH-VALUES",
    "LOW-VALUE",
    "LOW-VALUES",
    "ALL",
    "FIRST",
    "LAST",
    "ANY",
    "EACH",
    "WITH",
    "BEFORE",
    "AFTER",
    "INPUT",
    "OUTPUT",
    "I-O",
    "EXTEND",
    "REVERSED",
    "NO",
    "REWIND",
    "RECORD",
    "CORRESPONDING",
    "CORR",
})


def _should_skip_operand(tok: str) -> bool:
    """Return True if *tok* is a COBOL keyword/syntax token that should never
    be resolved as a data-field operand."""
    if not tok:
        return True
    u = tok.upper()
    if u in _INTRINSICS or u in _CONNECTIVES:
        return True
    if u in {"(", ")", ",", ".", ":", ";"}:
        return True
    if u.startswith("'") or u.startswith('"'):
        return True
    if u.isdigit():
        return True
    return False


def _canonical_operand(tokens, i):
    """Canonicalize COBOL qualified-name syntax: FIELD OF RECORD or FIELD IN RECORD
    becomes RECORD.FIELD for resolution. Also handles dot-qualified names like
    GROUP.FIELD by extracting the short name."""
    tok = tokens[i]
    
    # Handle dot-qualified operand (GROUP.FIELD)
    if '.' in tok:
        parts = tok.split('.')
        if len(parts) == 2:
            owner = parts[0]
            field = parts[1]
            if not _should_skip_operand(field) and not _should_skip_operand(owner):
                return field
    
    if i + 2 < len(tokens) and tokens[i + 1].upper() in {"OF", "IN"}:
        owner = tokens[i + 2]
        if not _should_skip_operand(tok) and not _should_skip_operand(owner):
            return f"{owner}.{tok}"
    return tok


# ---------------------------------------------------------------------------
# Source normalisation  --  FIXED COLUMN POSITIONS (COBOL fixed format)
# ---------------------------------------------------------------------------

def _strip_seq(line: str) -> str:
    """Legacy helper kept for backward compatibility. Not used internally."""
    m = _SEQ_RE.match(line)
    return m.group(1) if m else line


def _normalise_source(raw: str) -> list:
    """
    Convert raw COBOL fixed-format source text into a list of (lineno, text)
    pairs where `text` is the code area (columns 8-72) of each non-comment,
    non-blank line.

    COBOL fixed-format column layout (1-based):
      Cols  1- 6  Sequence area   -- ignored
      Col   7     Indicator area  -- '*' or '/' = comment
      Cols  8-72  Code area
      Cols 73-80  Identification  -- ignored

    In 0-based Python indexing:
      raw[0:6]  sequence area
      raw[6]    indicator
      raw[7:72] code area

    FIXED COLUMN POSITIONS -- no _strip_seq, no regex for indicator.
    Lines shorter than 7 characters are silently skipped.
    """
    result = []
    for lineno, raw_line in enumerate(raw.splitlines(), start=1):
        line = raw_line.rstrip('\r\n')
        if len(line) < 7:
            continue
        indicator = line[6]
        if indicator in ('*', '/', '$'):
            continue
        code = line[7:72].rstrip()
        if code.strip():
            result.append((lineno, code))
    return result


# ---------------------------------------------------------------------------
# Period-aware helpers
# ---------------------------------------------------------------------------

def _ends_statement(text: str) -> bool:
    in_sq = in_dq = False
    last = ''
    for ch in text:
        if ch == "'" and not in_dq:
            in_sq = not in_sq
        elif ch == '"' and not in_sq:
            in_dq = not in_dq
        if not in_sq and not in_dq and ch != ' ':
            last = ch
    return last == '.'


def _is_para_header_line(text: str) -> bool:
    stripped = text.strip()
    m = _PARA_HEADER_RE.match(stripped)
    if not m:
        return False
    candidate = m.group(1).upper()
    return candidate not in _NOT_PARA


def _is_area_a_paragraph(text: str) -> bool:
    """
    Return True if this code-area text (raw[7:72] from _normalise_source)
    is a paragraph header.

    Rules (ALL must hold):
      1. text[0] != ' '  (Area A)
      2. NOT _LEVEL_NUM_RE
      3. NOT _SECTION_HEADER_RE
      4. Matches _PARA_HEADER_RE
      5. Candidate NOT in _NOT_PARA
      6. Candidate NOT in _NOT_HEADER_KEYWORDS
    """
    if not text or text[0] == ' ':
        return False
    stripped = text.strip()
    if _LEVEL_NUM_RE.match(stripped):
        return False
    if _SECTION_HEADER_RE.match(stripped):
        return False
    m = _PARA_HEADER_RE.match(stripped)
    if not m:
        return False
    candidate = m.group(1).upper()
    if candidate in _NOT_PARA or candidate in _NOT_HEADER_KEYWORDS:
        return False
    return True


# ---------------------------------------------------------------------------
# Continuation joiner
# ---------------------------------------------------------------------------

def _join_source_lines(lines: list) -> list:
    if not lines:
        return []
    joined = [[lines[0][0], lines[0][1]]]
    for lineno, text in lines[1:]:
        prev_ends    = _ends_statement(joined[-1][1])
        cand_is_para = _is_area_a_paragraph(text)
        if not prev_ends and not cand_is_para:
            joined[-1][1] = joined[-1][1] + ' ' + text.strip()
        else:
            joined.append([lineno, text])
    return [(ln, txt) for ln, txt in joined]


# ---------------------------------------------------------------------------
# qmap builder
# ---------------------------------------------------------------------------

def build_qmap(layout_path: Path):
    if not layout_path.exists():
        return {}, set()
    with open(layout_path, encoding='utf-8') as fh:
        layout = json.load(fh)

    qmap = defaultdict(list)
    record_names = set()

    for rec in layout.get('records', []):
        rec_name = rec['name']
        record_names.add(rec_name.upper())
        copybook = rec.get('copybook')
        for field in rec.get('fields', []):
            qn = field['qualified_name']
            parts = qn.split('.')
            short = parts[-1].upper()
            entry = {
                'field':    qn,
                'record':   rec_name,
                'copybook': field.get('copybook') or copybook,
                'offset':   field.get('offset', 0),
                'length':   field.get('length', 0),
            }
            qmap[short].append(entry)
            for i in range(len(parts)):
                key = '.'.join(parts[i:]).upper()
                if key != short:
                    qmap[key].append(entry)

    for rec in layout.get('records', []):
        rec_name = rec['name']
        key = rec_name.upper()
        if key not in qmap:
            qmap[key].append({
                'field':    rec_name,
                'record':   rec_name,
                'copybook': rec.get('copybook'),
                'offset':   0,
                'length':   rec.get('total_bytes', 0),
            })

    return dict(qmap), record_names


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------

def resolve(name: str, qmap: dict, context_records: set) -> list:
    bare = re.sub(r'\s*\([^)]*\)', '', name).strip().upper()
    matches = qmap.get(bare, [])
    if not matches:
        return []
    if len(matches) == 1:
        return matches
    if context_records:
        filtered = [m for m in matches
                    if m['record'].upper() in {r.upper() for r in context_records}]
        if filtered:
            return filtered
    # Ambiguous: no context to disambiguate multiple matches
    return []


def is_literal(token: str) -> bool:
    return bool(_LITERAL_RE.match(token.strip()))


# ---------------------------------------------------------------------------
# Tokeniser
# ---------------------------------------------------------------------------

def _tokens(text: str) -> list:
    cleaned = re.sub(r"'[^']*'", '__LIT__', text)
    cleaned = re.sub(r'"[^"]*"', '__LIT__', cleaned)
    return cleaned.strip().split()


# ---------------------------------------------------------------------------
# Literal masker
# ---------------------------------------------------------------------------

def _mask_literals(text: str) -> str:
    result = list(text)
    i = 0
    while i < len(text):
        if text[i] in ("'", '"'):
            quote = text[i]
            result[i] = '_'
            i += 1
            while i < len(text) and text[i] != quote:
                result[i] = '_'
                i += 1
            if i < len(text):
                result[i] = '_'
        i += 1
    return ''.join(result)


# ---------------------------------------------------------------------------
# Period splitter
# ---------------------------------------------------------------------------

def _split_on_period(text: str) -> list:
    parts = []
    current = []
    in_sq = in_dq = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "'" and not in_dq:
            in_sq = not in_sq
            current.append(ch)
        elif ch == '"' and not in_sq:
            in_dq = not in_dq
            current.append(ch)
        elif ch == '.' and not in_sq and not in_dq:
            rest = text[i+1:]
            if not rest or rest[0] in (' ', '\t', '\r', '\n'):
                segment = ''.join(current).strip()
                if segment:
                    parts.append(segment)
                current = []
            else:
                current.append(ch)
        else:
            current.append(ch)
        i += 1
    tail = ''.join(current).strip()
    if tail:
        parts.append(tail)
    return parts


# ---------------------------------------------------------------------------
# Paragraph extractor  (Section 3.4: per-name occurrences list)
# ---------------------------------------------------------------------------

def extract_paragraphs(lines: list) -> dict:
    """
    Return a dict mapping paragraph names to their occurrence data.
    Public signature: dict[str, entry]  --  FROZEN (Sections 3.1-3.3).

    Special key '__MAIN__' maps to a plain list[(lineno, text)] for lines
    that appear before the first named paragraph.

    For every real paragraph name the value is:
        {
            'name': str,           # paragraph name (uppercased)
            'occurrences': [       # one entry per encounter, never merged
                {
                    'section_name': str | None,
                    'lines': [(lineno, text), ...]
                },
                ...
            ]
        }

    When the same paragraph name appears under two different SECTION headers
    a second occurrence is appended rather than merging into the first.
    len(occurrences) == 1 for unique names; 2+ for cross-section duplicates.

    Section-name canonicalization:
      - Full identifier before the SECTION keyword
      - Trailing period stripped
      - Whitespace collapsed
      - Digit prefix and hyphen preserved verbatim
      - Uppercased
    """
    paragraphs = {}
    current = '__MAIN__'
    paragraphs[current] = []          # plain list; callers skip __MAIN__
    current_section = None            # None = no SECTION header seen yet

    proc_lines_raw = []
    in_procedure = False
    for entry in lines:
        lineno, text = entry
        stripped = text.strip()
        if stripped.upper().startswith('PROCEDURE DIVISION'):
            in_procedure = True
            continue
        if in_procedure:
            proc_lines_raw.append(entry)

    proc_lines = _join_source_lines(proc_lines_raw)

    for lineno, text in proc_lines:
        stripped = text.strip()
        # --- SECTION header? ---
        sm = _SECTION_HEADER_RE.match(stripped)
        if sm and not text[0:1] == ' ':   # must be Area A (no leading space)
            # canonicalize: group 1 is the identifier before SECTION
            current_section = sm.group(1).rstrip('.').strip().upper()
            # do NOT emit a paragraph entry for the section header
            continue

        if _is_area_a_paragraph(text):
            candidate = _PARA_HEADER_RE.match(stripped).group(1).upper()
            current = candidate
            if current not in paragraphs:
                # First encounter: create the per-name entry
                paragraphs[current] = {'name': current, 'occurrences': []}
            # Always append a fresh occurrence for this encounter
            paragraphs[current]['occurrences'].append(
                {'section_name': current_section, 'lines': []}
            )
        else:
            entry_val = paragraphs[current]
            if isinstance(entry_val, list):
                # __MAIN__ path: plain list
                entry_val.append((lineno, text))
            else:
                # Real paragraph: append to the most recent occurrence
                entry_val['occurrences'][-1]['lines'].append((lineno, text))

    return paragraphs


# ---------------------------------------------------------------------------
# Statement continuation joiner (paragraph body level)
# ---------------------------------------------------------------------------

def _join_lines(lines: list) -> list:
    joined = []
    for lineno, text in lines:
        if joined and not _ends_statement(joined[-1][1]):
            prev_ln, prev_text = joined[-1]
            joined[-1] = (prev_ln, prev_text + ' ' + text.strip())
        else:
            joined.append((lineno, text))
    return joined


# ---------------------------------------------------------------------------
# CALL USING parser  (Section 3.2)
# ---------------------------------------------------------------------------

_CALL_STOP_KEYWORDS = frozenset({
    'ON', 'NOT', 'EXCEPTION', 'END-CALL', 'OVERFLOW', 'ERROR',
})


def _parse_call(
    lineno: int,
    raw_text: str,
    tokens: list,
    qmap: dict,
    context_records: set,
    reads: list,
    mutates: list,
    unresolved: list,
    call_targets: list,
):
    """
    Classify a CALL statement with a single forward-scanning cursor.

    Grammar handled:
      CALL target
           [USING [BY REFERENCE | BY CONTENT | BY VALUE]
                  operand ...
                  [BY REFERENCE | BY CONTENT | BY VALUE] operand ...]
           [RETURNING identifier]
           [ON EXCEPTION ...]
           [NOT ON EXCEPTION ...]
           [END-CALL]

    Mode semantics:
      BY REFERENCE (default inside USING)  ->  read + mutate
      BY CONTENT                           ->  read only
      BY VALUE                             ->  read only
      RETURNING (anywhere after target)    ->  next identifier is mutate only;
                                               scanning stops after that.

    The scan starts at token index 2 (first token after CALL target),
    so RETURNING without a preceding USING clause is handled correctly.
    Single-pass cursor CALL classifier (Section 3.2).
    RETURNING is handled unconditionally regardless of whether USING is present.
    """
    # --- extract static target ---
    target = None
    if len(tokens) >= 2:
        raw_target = tokens[1]
        if raw_target == '__LIT__':
            m = _CALL_TARGET_RE.match(raw_text.strip())
            if m:
                target = (m.group(1) or m.group(2) or m.group(3) or '').upper()
        elif not is_literal(raw_target):
            target = raw_target.upper()
        else:
            m = re.match(r"^['\"]([^'\"]+)['\"]$", raw_target)
            if m:
                target = m.group(1).upper()

    if target:
        call_targets.append(target)

    # --- single-pass cursor from token 2 ---
    in_using       = False
    mode           = 'REFERENCE'
    returning_next = False

    ut = [t.upper() for t in tokens]
    i  = 2

    while i < len(ut):
        tok = ut[i]

        if tok in _CALL_STOP_KEYWORDS:
            break

        if tok == 'USING':
            in_using = True
            mode = 'REFERENCE'
            i += 1
            continue

        if tok == 'RETURNING':
            returning_next = True
            in_using = False
            i += 1
            continue

        if tok == 'BY':
            if i + 1 < len(ut) and ut[i + 1] in ('REFERENCE', 'CONTENT', 'VALUE'):
                mode = ut[i + 1]
                i += 2
            else:
                i += 1
            continue

        if tok in ('REFERENCE', 'CONTENT', 'VALUE'):
            mode = tok
            i += 1
            continue

        operand = tokens[i]
        if operand == '__LIT__' or is_literal(operand):
            i += 1
            continue

        if returning_next:
            hits = resolve(operand, qmap, context_records)
            if not hits:
                unresolved.append({
                    'verb': 'CALL', 'line_no': lineno, 'raw_text': raw_text,
                    'reason': f'unresolved CALL RETURNING operand: {operand}'
                })
            else:
                for h in hits:
                    if h not in mutates:
                        mutates.append(h)
                        context_records.add(h['record'])
            break

        if in_using:
            if mode in ('REFERENCE',):
                hits = resolve(operand, qmap, context_records)
                if not hits:
                    unresolved.append({
                        'verb': 'CALL', 'line_no': lineno, 'raw_text': raw_text,
                        'reason': f'unresolved CALL USING operand: {operand}'
                    })
                else:
                    for h in hits:
                        if h not in reads:
                            reads.append(h)
                            context_records.add(h['record'])
                        if h not in mutates:
                            mutates.append(h)
                            context_records.add(h['record'])
            elif mode in ('CONTENT', 'VALUE'):
                hits = resolve(operand, qmap, context_records)
                if not hits:
                    unresolved.append({
                        'verb': 'CALL', 'line_no': lineno, 'raw_text': raw_text,
                        'reason': f'unresolved CALL USING operand: {operand}'
                    })
                else:
                    for h in hits:
                        if h not in reads:
                            reads.append(h)
                            context_records.add(h['record'])

        i += 1


# ---------------------------------------------------------------------------
# Verb classifier
# ---------------------------------------------------------------------------

def classify_statement(
    lineno: int,
    text: str,
    qmap: dict,
    context_records: set,
    reads: list,
    mutates: list,
    unresolved: list,
    call_targets: list = None,
):
    if call_targets is None:
        call_targets = []
    raw_text = text.strip().rstrip('.')
    tokens = _tokens(raw_text)
    if not tokens:
        return
    verb = tokens[0].upper()

    def _add_read(name):
        if _should_skip_operand(name):
            return
        if name == '__LIT__' or is_literal(name):
            return
        # Extract owner from dot-qualified operand (GROUP.FIELD) before canonicalization
        owner = None
        owner_upper = None
        if '.' in name:
            parts = name.split('.')
            if len(parts) == 2:
                owner = parts[0]
                owner_upper = owner.upper()
        # Apply OF/IN qualifier canonicalization before resolution
        for i, tok in enumerate(tokens):
            if tok == name:
                name = _canonical_operand(tokens, i)
                break
        bare = name.upper()
        hits = resolve(name, qmap, context_records)
        # If owner is specified and hits is empty due to ambiguity, return matches
        # to allow filtering by owner (V09 case: dot-qualified operand)
        if owner_upper and not hits:
            matches = qmap.get(bare, [])
            if matches and len(matches) > 1:
                hits = matches
        # Filter hits by owner if dot-qualified operand was provided
        if owner_upper and hits:
            hits = [h for h in hits if h['record'].upper() == owner_upper]
        if not hits:
            reason = (
                f'ambiguous field (no context): {name}'
                if bare in qmap and len(qmap[bare]) > 1
                else f'unresolved read operand: {name}'
            )
            unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                               'reason': reason, 'name': name})
        else:
            for h in hits:
                if h not in reads:
                    reads.append(h)
                    context_records.add(h['record'])

    def _add_mutate(name):
        if _should_skip_operand(name):
            return
        if name == '__LIT__' or is_literal(name):
            unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                               'reason': f'literal as mutate target (ignored): {name}'})
            return
        # Apply OF/IN qualifier canonicalization before resolution
        for i, tok in enumerate(tokens):
            if tok == name:
                name = _canonical_operand(tokens, i)
                break
        hits = resolve(name, qmap, context_records)
        if not hits:
            unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                               'reason': f'unresolved mutate operand: {name}'})
        else:
            for h in hits:
                if h not in mutates:
                    mutates.append(h)
                    context_records.add(h['record'])

    if verb == 'MOVE':
        if len(tokens) >= 2 and tokens[1].upper() == 'CORRESPONDING':
            try:
                to_idx = [t.upper() for t in tokens].index('TO')
                src_group = tokens[2] if to_idx > 2 else None
                dst_group = tokens[to_idx + 1] if to_idx + 1 < len(tokens) else None
                src_upper = (src_group or '').upper()
                dst_upper = (dst_group or '').upper()
                
                # Handle MOVE CORRESPONDING with qmap children arrays (V08 style)
                # qmap[src_group] = {"children": [{"name": "CHILD-X", ...}, ...]}
                src_children_list = []
                dst_children_list = []
                use_children_style = False
                
                if src_group and src_group.upper() in qmap:
                    src_obj = qmap[src_group.upper()]
                    if isinstance(src_obj, dict) and 'children' in src_obj:
                        src_children_list = src_obj['children']
                        use_children_style = True
                    elif isinstance(src_obj, list):
                        # Check if this is the "field" style (entries have "field" keys)
                        # or the "children" style (entries have "name" keys)
                        if src_obj and isinstance(src_obj[0], dict) and 'name' in src_obj[0]:
                            src_children_list = src_obj
                            use_children_style = True
                
                if dst_group and dst_group.upper() in qmap:
                    dst_obj = qmap[dst_group.upper()]
                    if isinstance(dst_obj, dict) and 'children' in dst_obj:
                        dst_children_list = dst_obj['children']
                        use_children_style = True
                    elif isinstance(dst_obj, list):
                        if dst_obj and isinstance(dst_obj[0], dict) and 'name' in dst_obj[0]:
                            dst_children_list = dst_obj
                            use_children_style = True
                
                if use_children_style:
                    # V08 style: extract matching child names from children arrays
                    src_names = {c.get('name', '').upper() for c in src_children_list if c.get('name', '').upper() != 'FILLER'}
                    dst_names = {c.get('name', '').upper() for c in dst_children_list if c.get('name', '').upper() != 'FILLER'}
                    matching_names = src_names & dst_names
                    
                    # Add matching child names to reads (from src) and mutates (from dst)
                    for name in matching_names:
                        if name and name != 'FILLER':
                            # First try qmap-lookup for normal structure (child name as key)
                            child_hits = qmap.get(name.upper(), [])
                            if child_hits and isinstance(child_hits, list) and len(child_hits) > 0:
                                # Normal qmap structure: entries are dicts with 'field', 'record', etc.
                                for h in child_hits:
                                    if h not in reads:   reads.append(h)
                                    if h not in mutates: mutates.append(h)
                            else:
                                # Children array structure: build entry from children data
                                # First check if we have source children data
                                src_entry = None
                                for c in src_children_list:
                                    if c.get('name', '').upper() == name:
                                        src_entry = c
                                        break
                                # Build proper dict entry
                                if src_entry:
                                    entry = {
                                        'field':    name,
                                        'record':   src_entry.get('record', name),
                                        'copybook': src_entry.get('copybook'),
                                        'offset':   src_entry.get('offset', 0),
                                        'length':   src_entry.get('length', 0),
                                    }
                                else:
                                    entry = {
                                        'field':    name,
                                        'record':   name,
                                        'copybook': None,
                                        'offset':   0,
                                        'length':   0,
                                    }
                                if entry not in reads:   reads.append(entry)
                                if entry not in mutates: mutates.append(entry)
                else:
                    # Legacy style: add group name to reads and mutates
                    # Find existing entry for src_group in qmap to get the full entry
                    src_entries = qmap.get(src_upper, [])
                    dst_entries = qmap.get(dst_upper, [])
                    
                    if src_entries and isinstance(src_entries[0], dict) and 'field' in src_entries[0]:
                        # Legacy structure: add entry with 'field' key
                        for e in src_entries:
                            if e not in reads:
                                reads.append(e)
                    elif src_group and src_group not in reads:
                        # Fallback: add as plain string
                        reads.append(src_group)
                    
                    if dst_entries and isinstance(dst_entries[0], dict) and 'field' in dst_entries[0]:
                        # Legacy structure: add entry with 'field' key
                        for e in dst_entries:
                            if e not in mutates:
                                mutates.append(e)
                    elif dst_group and dst_group not in mutates:
                        # Fallback: add as plain string
                        mutates.append(dst_group)
            except (ValueError, IndexError):
                unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                                   'reason': 'could not parse MOVE CORRESPONDING operands'})
        else:
            try:
                to_idx = [t.upper() for t in tokens].index('TO')
                for s in tokens[1:to_idx]: _add_read(s)
                for d in tokens[to_idx + 1:]: _add_mutate(d)
            except ValueError:
                unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                                   'reason': 'MOVE missing TO keyword'})

    elif verb == 'ADD':
        ut = [t.upper() for t in tokens]
        if 'GIVING' in ut:
            gi = ut.index('GIVING')
            ti = ut.index('TO') if 'TO' in ut else gi
            for o in tokens[1:ti]: _add_read(o)
            for r in tokens[gi + 1:]: _add_mutate(r)
        elif 'TO' in ut:
            ti = ut.index('TO')
            for o in tokens[1:ti]: _add_read(o)
            for d in tokens[ti + 1:]:
                _add_read(d); _add_mutate(d)
        else:
            unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                               'reason': 'ADD missing TO or GIVING'})

    elif verb == 'SUBTRACT':
        ut = [t.upper() for t in tokens]
        if 'GIVING' in ut:
            gi = ut.index('GIVING')
            fi = ut.index('FROM') if 'FROM' in ut else gi
            for o in tokens[1:fi] + tokens[fi + 1:gi]: _add_read(o)
            for r in tokens[gi + 1:]: _add_mutate(r)
        elif 'FROM' in ut:
            fi = ut.index('FROM')
            for o in tokens[1:fi]: _add_read(o)
            for d in tokens[fi + 1:]:
                _add_read(d); _add_mutate(d)
        else:
            unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                               'reason': 'SUBTRACT missing FROM'})

    elif verb == 'MULTIPLY':
        ut = [t.upper() for t in tokens]
        if 'GIVING' in ut:
            bi = ut.index('BY') if 'BY' in ut else 2
            gi = ut.index('GIVING')
            for o in tokens[1:bi] + tokens[bi + 1:gi]: _add_read(o)
            for r in tokens[gi + 1:]: _add_mutate(r)
        elif 'BY' in ut:
            bi = ut.index('BY')
            for o in tokens[1:bi]: _add_read(o)
            for d in tokens[bi + 1:]:
                _add_read(d); _add_mutate(d)
        else:
            unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                               'reason': 'MULTIPLY missing BY'})

    elif verb == 'DIVIDE':
        ut = [t.upper() for t in tokens]
        if 'GIVING' in ut:
            ibi = next((i for i, t in enumerate(ut) if t in ('INTO', 'BY')), 2)
            gi  = ut.index('GIVING')
            ri  = ut.index('REMAINDER') if 'REMAINDER' in ut else None
            results = tokens[gi + 1:ri] if ri else tokens[gi + 1:]
            for o in tokens[1:ibi] + tokens[ibi + 1:gi]: _add_read(o)
            for r in results: _add_mutate(r)
            if ri and ri + 1 < len(tokens): _add_mutate(tokens[ri + 1])
        elif 'INTO' in ut or 'BY' in ut:
            si = next((i for i, t in enumerate(ut) if t in ('INTO', 'BY')), 2)
            for o in tokens[1:si]: _add_read(o)
            for d in tokens[si + 1:]:
                _add_read(d); _add_mutate(d)
        else:
            unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                               'reason': 'DIVIDE missing INTO/BY'})

    elif verb == 'COMPUTE':
        ut = [t.upper() for t in tokens]
        if '=' in ut:
            ei = ut.index('=')
            for l in tokens[1:ei]: _add_mutate(l)
            for r in tokens[ei + 1:]:
                # Strip parentheses from token before checking
                rt = r.strip('()')
                if r != '__LIT__' and not is_literal(r) and r not in ('+','-','*','/','**','(',')'):  
                    _add_read(rt)
        else:
            unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                               'reason': 'COMPUTE missing = sign'})

    elif verb == 'INITIALIZE':
        for t in tokens[1:]:
            if t.upper() in ('REPLACING','BY','ALPHABETIC','ALPHANUMERIC',
                             'NUMERIC','ALPHANUMERIC-EDITED','NUMERIC-EDITED','ALL'):
                break
            _add_mutate(t)

    elif verb == 'READ':
        ut = [t.upper() for t in tokens]
        file_name = tokens[1] if len(tokens) > 1 else None
        if file_name: _add_mutate(file_name)
        if 'INTO' in ut:
            ii = ut.index('INTO')
            dst = tokens[ii + 1] if ii + 1 < len(tokens) else None
            if dst: _add_mutate(dst)

    elif verb == 'WRITE':
        ut = [t.upper() for t in tokens]
        record_name = tokens[1] if len(tokens) > 1 else None
        if record_name: _add_mutate(record_name)
        if 'FROM' in ut:
            fi = ut.index('FROM')
            src = tokens[fi + 1] if fi + 1 < len(tokens) else None
            if src: _add_read(src)

    elif verb == 'STRING':
        ut = [t.upper() for t in tokens]
        ii = ut.index('INTO')    if 'INTO'    in ut else None
        pi = ut.index('POINTER') if 'POINTER' in ut else None
        if ii is not None:
            for t in tokens[1:ii]:
                if t.upper() not in ('DELIMITED','BY','SIZE') and t != '__LIT__':
                    _add_read(t)
            dst = tokens[ii + 1] if ii + 1 < len(tokens) else None
            if dst: _add_mutate(dst)
        if pi is not None:
            ptr = tokens[pi + 1] if pi + 1 < len(tokens) else None
            if ptr: _add_read(ptr); _add_mutate(ptr)

    elif verb == 'UNSTRING':
        ut = [t.upper() for t in tokens]
        src = tokens[1] if len(tokens) > 1 else None
        if src: _add_read(src)
        # Capture delimiter if DELIMITED BY is present
        di = ut.index('DELIMITED') if 'DELIMITED' in ut else None
        if di is not None and di + 2 < len(tokens) and ut[di + 1] == 'BY':
            delim = tokens[di + 2]
            if delim != '__LIT__' and not is_literal(delim):
                _add_read(delim)
        ii = ut.index('INTO')     if 'INTO'     in ut else None
        pi = ut.index('POINTER')  if 'POINTER'  in ut else None
        ti = ut.index('TALLYING') if 'TALLYING' in ut else None
        end = min(x for x in [pi, ti, len(tokens)] if x is not None)
        if ii is not None:
            for t in tokens[ii + 1:end]:
                if t.upper() not in ('DELIMITED','BY','ALL','DELIMITER','COUNT','IN') and t != '__LIT__':
                    _add_mutate(t)
        if pi is not None:
            ptr = tokens[pi + 1] if pi + 1 < len(tokens) else None
            if ptr: _add_read(ptr); _add_mutate(ptr)
        if ti is not None:
            tv = tokens[ti + 2] if ti + 2 < len(tokens) else None
            if tv: _add_read(tv); _add_mutate(tv)

    elif verb == 'ACCEPT':
        dst = tokens[1] if len(tokens) > 1 else None
        if dst and dst != '__LIT__': _add_mutate(dst)

    elif verb == 'DISPLAY':
        for t in tokens[1:]:
            if t.upper() in ('UPON','WITH','NO','ADVANCING'):
                break
            if t != '__LIT__':
                _add_read(t)

    elif verb in ('IF', 'EVALUATE', 'WHEN'):
        skip = {'IF','EVALUATE','WHEN','THEN','ELSE','END-IF',
                'AND','OR','NOT','TRUE','FALSE','OTHER',
                'EQUAL','TO','THAN','GREATER','LESS','THROUGH',
                'THRU','ALSO','=','>','<','>=','<='}
        for t in tokens[1:]:
            if t.upper() in skip or t == '__LIT__' or is_literal(t):
                continue
            _add_read(t)

    elif verb == 'SET':
        ut = [t.upper() for t in tokens]
        if 'TO' in ut:
            ti = ut.index('TO')
            for tgt in tokens[1:ti]: _add_mutate(tgt)
            for src in tokens[ti + 1:]:
                if src.upper() not in ('TRUE','FALSE','ON','OFF','UP','DOWN') and src != '__LIT__':
                    _add_read(src)
        else:
            unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                               'reason': 'SET missing TO'})

    elif verb == 'EXEC':
        # EXEC CICS block: extract INTO/RESP/RESP2 → mutates, FROM/RIDFLD → reads
        # Discard: command verb, string literals, DATASET/QUEUE/FILE/PROGRAM keywords
        cics_r = {'FROM', 'LENGTH', 'RESP', 'RESP2'}
        cics_m = {'INTO', 'RESP', 'RESP2'}
        skip_keywords = {'DATASET', 'QUEUE', 'FILE', 'PROGRAM', 'READ', 'WRITE',
                        'LINK', 'RETURN', 'SEND', 'RECEIVE', 'START', 'READNEXT',
                        'READPREV', 'STARTBR', 'READBR', 'RESTART', 'DELETE', 'REWRITE',
                        'MERGE', 'UPDATE', 'LOCK', 'UNLOCK', 'INQUIRE', 'SET', 'TERM',
                        'TRACE', 'SYNCPOINT', 'ABEND', 'CANCEL', 'RELEASE', 'WAIT',
                        'TIME', 'COMMINFO', 'EIB', 'REQID', 'USERID'}
        
        def _extract_arg(token):
            """Extract argument from token like 'INTO(arg)' or return token if it's a standalone arg."""
            if '(' in token and token.endswith(')'):
                # Token is like 'INTO(arg)' - extract the argument part
                inner = token[token.index('(')+1:-1]
                return inner
            return None
        
        i = 0
        while i < len(tokens):
            t = tokens[i]
            tu = t.upper()
            
            # Skip END-EXEC and stop processing
            if tu == 'END-EXEC':
                break
            
            # Skip command verb (first token after EXEC CICS) and known skip keywords
            if tu in skip_keywords:
                i += 1
                continue
            
            # Check if this token contains a keyword like INTO(...), RESP(...), etc.
            matched_keyword = None
            arg = None
            
            for kw in cics_r | cics_m:
                if tu.startswith(kw + '(') and tu.endswith(')'):
                    # Token is like 'INTO(arg)' - extract keyword and argument
                    matched_keyword = kw
                    arg = tu[len(kw)+1:-1]  # Extract from '(...)'
                    break
            
            if matched_keyword:
                if matched_keyword in cics_r:
                    _add_read(arg)
                if matched_keyword in cics_m:
                    _add_mutate(arg)
                i += 1
                continue
            
            # Handle standalone keyword + argument pattern
            if tu in cics_r | cics_m:
                # Keyword followed by argument
                if i + 1 < len(tokens):
                    next_t = tokens[i + 1]
                    if next_t != '__LIT__' and not is_literal(next_t):
                        if tu in cics_r:
                            _add_read(next_t)
                        if tu in cics_m:
                            _add_mutate(next_t)
                i += 2
                continue
            
            i += 1

    elif verb == 'CALL':
        _parse_call(lineno, raw_text, tokens, qmap, context_records,
                    reads, mutates, unresolved, call_targets)

    elif verb == 'INSPECT':
        # INSPECT source [TALLYING tally-name FOR ...]
        #                [REPLACING ... BY ...]
        # source -> read; tally names after TALLYING ... FOR -> mutate;
        # replacement targets after REPLACING -> mutate
        ut = [t.upper() for t in tokens]
        src = tokens[1] if len(tokens) > 1 else None
        if src and src != '__LIT__':
            _add_read(src)
        _INSPECT_MUTATE_TRIGGERS = frozenset({'TALLYING', 'REPLACING'})
        _INSPECT_SKIP = frozenset({
            'TALLYING','REPLACING','FOR','ALL','LEADING','TRAILING',
            'CHARACTERS','BY','FIRST','BEFORE','AFTER','INITIAL',
            'CONVERTING','TO',
        })
        i = 2
        in_mutate = False
        while i < len(ut):
            tok = ut[i]
            if tok in _INSPECT_MUTATE_TRIGGERS:
                in_mutate = True
                i += 1
                continue
            if tok in _INSPECT_SKIP or tokens[i] == '__LIT__' or is_literal(tokens[i]):
                i += 1
                continue
            if in_mutate:
                _add_mutate(tokens[i])
            i += 1

    elif verb == 'SORT':
        # SORT file-name ON ASCENDING/DESCENDING KEY key ...
        #      [USING input-file ...] [GIVING output-file ...]
        ut = [t.upper() for t in tokens]
        file_name = tokens[1] if len(tokens) > 1 else None
        if file_name and file_name != '__LIT__':
            _add_mutate(file_name)
        _SORT_SKIP = frozenset({
            'ON','ASCENDING','DESCENDING','KEY','WITH','DUPLICATES',
            'IN','ORDER','COLLATING','SEQUENCE',
        })
        mode = None
        i = 2
        while i < len(ut):
            tok = ut[i]
            if tok == 'USING':
                mode = 'read'
                i += 1
                continue
            if tok == 'GIVING':
                mode = 'mutate'
                i += 1
                continue
            if tok in _SORT_SKIP or tokens[i] == '__LIT__' or is_literal(tokens[i]):
                i += 1
                continue
            if mode == 'read':
                _add_read(tokens[i])
            elif mode == 'mutate':
                _add_mutate(tokens[i])
            i += 1

    elif verb == 'MERGE':
        # MERGE file-name ON ASCENDING/DESCENDING KEY key ...
        #       USING input-files ... GIVING output-files ...
        ut = [t.upper() for t in tokens]
        file_name = tokens[1] if len(tokens) > 1 else None
        if file_name and file_name != '__LIT__':
            _add_mutate(file_name)
        _MERGE_SKIP = frozenset({
            'ON','ASCENDING','DESCENDING','KEY','WITH','DUPLICATES',
            'IN','ORDER','COLLATING','SEQUENCE',
        })
        mode = None
        i = 2
        while i < len(ut):
            tok = ut[i]
            if tok == 'USING':
                mode = 'read'
                i += 1
                continue
            if tok == 'GIVING':
                mode = 'mutate'
                i += 1
                continue
            if tok in _MERGE_SKIP or tokens[i] == '__LIT__' or is_literal(tokens[i]):
                i += 1
                continue
            if mode == 'read':
                _add_read(tokens[i])
            elif mode == 'mutate':
                _add_mutate(tokens[i])
            i += 1

    elif verb == 'RELEASE':
        # RELEASE record-name [FROM source]
        ut = [t.upper() for t in tokens]
        rec = tokens[1] if len(tokens) > 1 else None
        if rec and rec != '__LIT__':
            _add_mutate(rec)
        if 'FROM' in ut:
            fi = ut.index('FROM')
            src = tokens[fi + 1] if fi + 1 < len(tokens) else None
            if src and src != '__LIT__':
                _add_read(src)

    elif verb == 'RETURN':
        # RETURN file-name [INTO target]
        ut = [t.upper() for t in tokens]
        file_name = tokens[1] if len(tokens) > 1 else None
        if file_name and file_name != '__LIT__':
            _add_mutate(file_name)
        if 'INTO' in ut:
            ii = ut.index('INTO')
            tgt = tokens[ii + 1] if ii + 1 < len(tokens) else None
            if tgt and tgt != '__LIT__':
                _add_mutate(tgt)

    elif verb == 'PERFORM':
        pass

    elif verb in ('OPEN','CLOSE','STOP','GOBACK','CONTINUE','EXIT',
                  'GO','NEXT','END-READ','END-WRITE','END-IF',
                  'END-EVALUATE','END-PERFORM','END-STRING','END-UNSTRING',
                  'END-COMPUTE','END-ADD','END-SUBTRACT','END-MULTIPLY',
                  'END-DIVIDE','END-EXEC','END-CALL'):
        pass


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------

def extract_data_flow(cbl_path: Path, layout_path: Path) -> dict:
    program_name = cbl_path.stem.upper()
    raw   = cbl_path.read_text(encoding='utf-8', errors='replace')
    lines = _normalise_source(raw)

    qmap, record_names = build_qmap(layout_path)
    paragraphs = extract_paragraphs(lines)

    program_unresolved = []
    facts_path = FACTS_DIR / f"{program_name}.json"

    # Build flat occurrence list: (name, section_name, lines) per occurrence
    # Used for: actual_para count, collision detection, and per-occurrence emit.
    all_occurrences = [
        (name, occ['section_name'], occ['lines'])
        for name, entry in paragraphs.items()
        if name != '__MAIN__'
        for occ in entry['occurrences']
    ]

    if facts_path.exists():
        try:
            with open(facts_path, encoding='utf-8') as fh:
                facts = json.load(fh)
            raw_val = facts.get('paragraphs_defined', None)
            if isinstance(raw_val, list):
                expected_para = len(raw_val)
            elif isinstance(raw_val, int):
                expected_para = raw_val
            else:
                expected_para = None

            # actual_para = total occurrence count (not unique name count)
            actual_para = len(all_occurrences)
            if expected_para is not None and abs(actual_para - expected_para) > 1:
                msg = (f"paragraph count mismatch: local={actual_para} "
                       f"facts={expected_para}")
                print(f"WARNING [{program_name}]: {msg}", file=sys.stderr)
                program_unresolved.append({'issue': msg})
        except Exception as exc:
            print(f"WARNING [{program_name}]: could not read facts: {exc}", file=sys.stderr)

    call_graph_set = []

    # --- Collision detection: names that appear under 2+ distinct section values ---
    name_section_sets = defaultdict(set)
    for name, sname, _ in all_occurrences:
        name_section_sets[name].add(sname)
    colliding_names = {
        name for name, snames in name_section_sets.items() if len(snames) > 1
    }

    # --- Emit paragraph_data_flow: one entry per occurrence ---
    paragraph_data_flow = {}

    for para_name, section_name, para_lines in all_occurrences:
        reads = []; mutates = []; unresolved_list = []
        para_call_targets = []
        context_records: set = set()

        for lineno, text in _join_lines(para_lines):
            for part in _split_on_period(text):
                if part:
                    _dispatch_inline(lineno, part, qmap, context_records,
                                     reads, mutates, unresolved_list,
                                     para_call_targets)

        for t in para_call_targets:
            if t not in call_graph_set:
                call_graph_set.append(t)

        entry_data = {
            'section_name': section_name,
            'reads':        reads,
            'mutates':      mutates,
            'unresolved':   unresolved_list,
        }

        # Apply compound key only for cross-section name collisions
        if para_name in colliding_names:
            emit_key = f"{section_name}::{para_name}"
        else:
            emit_key = para_name

        paragraph_data_flow[emit_key] = entry_data

    return {
        'program':             program_name,
        'schema_version':      SCHEMA_VERSION,
        'paragraph_data_flow': paragraph_data_flow,
        'call_graph':          {program_name: call_graph_set},
        'program_unresolved':  program_unresolved,
    }


def _dispatch_inline(lineno, text, qmap, context_records, reads, mutates, unresolved,
                     call_targets=None):
    if call_targets is None:
        call_targets = []
    _VERB_SPLIT_RE = re.compile(
        r'(?:^|(?<=\s))(?=(?:MOVE|ADD|SUBTRACT|MULTIPLY|DIVIDE|COMPUTE|INITIALIZE|'
        r'READ|WRITE|STRING|UNSTRING|ACCEPT|DISPLAY|IF|EVALUATE|WHEN|SET|EXEC|'
        r'PERFORM|CALL|INSPECT|SORT|MERGE|RELEASE|RETURN|'
        r'OPEN|CLOSE|STOP|GOBACK|CONTINUE|EXIT|GO|END-IF|'
        r'END-EVALUATE|END-PERFORM|END-READ|END-WRITE|END-EXEC|'
        r'END-COMPUTE|END-ADD|END-SUBTRACT|END-MULTIPLY|END-DIVIDE|'
        r'END-STRING|END-UNSTRING|END-CALL)(?:\s|$))',
        re.IGNORECASE,
    )
    masked = _mask_literals(text)
    positions = [m.start() for m in _VERB_SPLIT_RE.finditer(masked)]
    if not positions:
        part = text.strip()
        if part:
            classify_statement(lineno, part, qmap, context_records,
                               reads, mutates, unresolved, call_targets)
        return
    positions.append(len(text))
    for i, start in enumerate(positions[:-1]):
        end = positions[i + 1]
        part = text[start:end].strip()
        if part:
            classify_statement(lineno, part, qmap, context_records,
                               reads, mutates, unresolved, call_targets)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def run_single(cbl_path: Path, out_fh=None):
    program_name = cbl_path.stem.upper()
    layout_path  = BYTE_LAYOUTS_DIR / f"{program_name}.json"
    result = extract_data_flow(cbl_path, layout_path)
    n = sum(len(p['unresolved']) for p in result['paragraph_data_flow'].values()) \
        + len(result['program_unresolved'])
    if n:
        print(f"[{program_name}] unresolved_count={n}", file=sys.stderr)
    output = json.dumps(result, indent=2)
    if out_fh:
        out_fh.write(output)
    else:
        print(output)


def run_all():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    seen = set()
    unique = []
    for f in sorted(CBL_DIR.glob('*.cbl')) + sorted(CBL_DIR.glob('*.CBL')):
        if f.stem.upper() not in seen:
            seen.add(f.stem.upper())
            unique.append(f)
    print(f"[corpus] processing {len(unique)} programs...", file=sys.stderr)
    for cbl_path in unique:
        out_path = OUT_DIR / f"{cbl_path.stem.upper()}.json"
        try:
            with open(out_path, 'w', encoding='utf-8') as fh:
                run_single(cbl_path, out_fh=fh)
        except Exception as exc:
            print(f"[{cbl_path.stem.upper()}] ERROR: {exc}", file=sys.stderr)
    print(f"[corpus] done. wrote {len(unique)} files to {OUT_DIR}/", file=sys.stderr)


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == '--all':
        run_all()
    elif len(sys.argv) == 2:
        cbl = Path(sys.argv[1])
        if not cbl.exists():
            print(f"ERROR: file not found: {cbl}", file=sys.stderr)
            sys.exit(1)
        run_single(cbl)
    else:
        print("Usage:", file=sys.stderr)
        print("  python scripts/data_flow.py <path/to/PROGRAM.cbl>", file=sys.stderr)
        print("  python scripts/data_flow.py --all", file=sys.stderr)
        sys.exit(1)

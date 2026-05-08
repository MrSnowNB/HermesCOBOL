#!/usr/bin/env python3
"""
data_flow.py  --  Section 2: deterministic per-paragraph reads[]/mutates[] extractor.

Usage:
    single program : python scripts/data_flow.py data/raw/cbl/CBACT01C.cbl
    corpus batch   : python scripts/data_flow.py --all

Output is written to stdout (single) or data/data_flow/<PROGRAM>.json (batch).
"""

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

SCHEMA_VERSION = "1.2"
BYTE_LAYOUTS_DIR = Path("data/byte_layouts")
CBL_DIR          = Path("data/raw/cbl")
OUT_DIR          = Path("data/data_flow")
FACTS_DIR        = Path("data/facts")

# ---------------------------------------------------------------------------
# Paragraph boundary regex  (same pattern used in v1.1 extractor)
# ---------------------------------------------------------------------------
_PARA_RE = re.compile(
    r'^[ ]{0,7}([A-Z0-9][A-Z0-9\-]*)\s*\.\s*$',
    re.IGNORECASE | re.MULTILINE
)
# Sequence-number area stripped lines (columns 1-6 are sequence numbers, 7 is
# indicator). We normalise by stripping the leading 6-digit seq number if present.
_SEQ_RE = re.compile(r'^\d{6}(.*)$')

# Literals (quoted strings or numeric)
_LITERAL_RE = re.compile(r"^(?:'[^']*'|\"[^\"]*\"|[-+]?\d+\.?\d*|ZERO|ZEROS|ZEROES|SPACES|SPACE|HIGH-VALUES|LOW-VALUES|ALL\s+'[^']+'|TRUE|FALSE)$", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Source normalisation helpers
# ---------------------------------------------------------------------------

def _strip_seq(line: str) -> str:
    """Remove 6-digit sequence number prefix if present."""
    m = _SEQ_RE.match(line)
    return m.group(1) if m else line


def _normalise_source(raw: str) -> list[tuple[int, str]]:
    """
    Return list of (1-based-line-no, normalised-text) tuples.
    - Strips sequence numbers.
    - Discards full-line comments (indicator = '*' or '/').
    - Discards blank lines.
    - Keeps inline text (columns 8-72).
    """
    result = []
    for lineno, raw_line in enumerate(raw.splitlines(), start=1):
        line = _strip_seq(raw_line)
        if len(line) < 1:
            continue
        indicator = line[0] if len(line) > 0 else ' '
        if indicator in ('*', '/', '$'):
            continue
        # keep columns 7-71 (0-indexed: 6-71) but since seq already stripped,
        # column 0 is now the indicator column
        text = line[1:72].rstrip() if len(line) > 1 else ''
        if text.strip():
            result.append((lineno, text))
    return result


# ---------------------------------------------------------------------------
# qmap builder
# ---------------------------------------------------------------------------

def build_qmap(layout_path: Path) -> dict:
    """
    Returns dict: short_name -> list of field-dicts from byte_layout.
    Each field-dict contains: qualified_name, record, copybook, offset, length.
    """
    if not layout_path.exists():
        return {}
    with open(layout_path, encoding='utf-8') as fh:
        layout = json.load(fh)

    qmap = defaultdict(list)  # short_name -> [entry, ...]
    # Also track record-level names -> record name for group disambiguation
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
            # Also index by every suffix (for CORR group matching)
            for i in range(len(parts)):
                key = '.'.join(parts[i:]).upper()
                if key != short:
                    qmap[key].append(entry)

    # Also add record-level entries (for READ INTO record, INITIALIZE record, etc.)
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
    """
    Return list of matching field entries for `name`.
    1. Strip subscripts like (1), (N).
    2. Exact match on qualified name suffix.
    3. If multiple matches and context_records is non-empty, filter to those
       whose record is in context_records (nearest-enclosing group rule).
    4. If still ambiguous, return all matches (caller decides unresolved).
    """
    # Strip subscript
    bare = re.sub(r'\s*\(.*?\)', '', name).strip().upper()
    # Strip reference modification  :start:len
    bare = re.sub(r'\s*\(\d+:\d*\)', '', bare).strip()
    
    matches = qmap.get(bare, [])
    if not matches:
        return []
    if len(matches) == 1:
        return matches
    # disambiguation by context
    if context_records:
        filtered = [m for m in matches if m['record'].upper() in {r.upper() for r in context_records}]
        if filtered:
            return filtered
    return matches


def is_literal(token: str) -> bool:
    return bool(_LITERAL_RE.match(token.strip()))


# ---------------------------------------------------------------------------
# Paragraph extractor
# ---------------------------------------------------------------------------

_PARA_HEADER_RE = re.compile(
    r'^([A-Z0-9][A-Z0-9\-]*)\s*\.\s*$',
    re.IGNORECASE
)

def extract_paragraphs(lines: list[tuple[int, str]]) -> dict[str, list[tuple[int, str]]]:
    """
    Returns ordered dict: para_name -> [(lineno, text), ...]
    Lines before the first paragraph header are stored under key '__MAIN__'.
    """
    paragraphs = {}
    current = '__MAIN__'
    paragraphs[current] = []
    in_procedure = False

    for lineno, text in lines:
        stripped = text.strip()
        upper = stripped.upper()
        if upper.startswith('PROCEDURE DIVISION'):
            in_procedure = True
            continue
        if not in_procedure:
            continue
        m = _PARA_HEADER_RE.match(stripped)
        if m:
            name = m.group(1).upper()
            current = name
            if current not in paragraphs:
                paragraphs[current] = []
        else:
            paragraphs[current].append((lineno, text))
    return paragraphs


# ---------------------------------------------------------------------------
# Statement tokeniser  (simple: join continuation lines, split on verb)
# ---------------------------------------------------------------------------

def _join_lines(lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """
    Very light continuation: if a line ends mid-token (no period, no verb start)
    join to previous. Returns list of (first_lineno, joined_text).
    This is best-effort; COBOL continuation is complex.
    """
    joined = []
    for lineno, text in lines:
        if joined and not joined[-1][1].rstrip().endswith('.'):
            prev_ln, prev_text = joined[-1]
            joined[-1] = (prev_ln, prev_text + ' ' + text.strip())
        else:
            joined.append((lineno, text))
    return joined


# ---------------------------------------------------------------------------
# Verb classifier
# ---------------------------------------------------------------------------

def _tokens(text: str) -> list[str]:
    return text.strip().split()


def _collect_to_keyword(tokens: list[str], start: int, keywords: set) -> tuple[list[str], int]:
    """Collect tokens from start until a keyword in `keywords` or end. Returns (collected, new_idx)."""
    out = []
    i = start
    while i < len(tokens) and tokens[i].upper() not in keywords:
        out.append(tokens[i])
        i += 1
    return out, i


def classify_statement(
    lineno: int,
    text: str,
    qmap: dict,
    context_records: set,
    reads: list,
    mutates: list,
    unresolved: list,
):
    """Classify a single COBOL statement text and append to reads/mutates/unresolved."""
    raw_text = text.strip().rstrip('.')
    tokens = _tokens(raw_text)
    if not tokens:
        return
    verb = tokens[0].upper()

    def _add_read(name):
        if is_literal(name):
            return
        hits = resolve(name, qmap, context_records)
        if not hits:
            unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                               'reason': f'unresolved read operand: {name}'})
        else:
            for h in hits:
                if h not in reads:
                    reads.append(h)
                    context_records.add(h['record'])

    def _add_mutate(name):
        if is_literal(name):
            unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                               'reason': f'literal as mutate target (ignored): {name}'})
            return
        hits = resolve(name, qmap, context_records)
        if not hits:
            unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                               'reason': f'unresolved mutate operand: {name}'})
        else:
            for h in hits:
                if h not in mutates:
                    mutates.append(h)
                    context_records.add(h['record'])

    # -----------------------------------------------------------------------
    # MOVE
    # -----------------------------------------------------------------------
    if verb == 'MOVE':
        if len(tokens) >= 2 and tokens[1].upper() == 'CORRESPONDING':
            # MOVE CORRESPONDING group1 TO group2
            # Best-effort: record both group names as read/mutate respectively
            try:
                to_idx = [t.upper() for t in tokens].index('TO')
                src_group = tokens[2] if to_idx > 2 else None
                dst_group = tokens[to_idx + 1] if to_idx + 1 < len(tokens) else None
                if src_group:
                    _add_read(src_group)
                if dst_group:
                    _add_mutate(dst_group)
                # Enumerate leaves from qmap if groups are known
                src_upper = (src_group or '').upper()
                dst_upper = (dst_group or '').upper()
                src_leaves = {e['field'].split('.')[-1].upper() for e in qmap.get(src_upper, []) if e}
                dst_entries = qmap.get(dst_upper, [])
                for de in dst_entries:
                    leaf = de['field'].split('.')[-1].upper()
                    if leaf in src_leaves:
                        if de not in mutates:
                            mutates.append(de)
            except (ValueError, IndexError):
                unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                                   'reason': 'could not parse MOVE CORRESPONDING operands'})
        else:
            try:
                to_idx = [t.upper() for t in tokens].index('TO')
                src_tokens = tokens[1:to_idx]
                dst_tokens = tokens[to_idx + 1:]
                for s in src_tokens:
                    _add_read(s)
                for d in dst_tokens:
                    _add_mutate(d)
            except ValueError:
                unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                                   'reason': 'MOVE missing TO keyword'})

    # -----------------------------------------------------------------------
    # ADD
    # -----------------------------------------------------------------------
    elif verb == 'ADD':
        upper_tokens = [t.upper() for t in tokens]
        if 'GIVING' in upper_tokens:
            giving_idx = upper_tokens.index('GIVING')
            to_idx = upper_tokens.index('TO') if 'TO' in upper_tokens else giving_idx
            operands = tokens[1:to_idx]
            results  = tokens[giving_idx + 1:]
            for o in operands:
                _add_read(o)
            for r in results:
                _add_mutate(r)
        elif 'TO' in upper_tokens:
            to_idx = upper_tokens.index('TO')
            operands = tokens[1:to_idx]
            dsts     = tokens[to_idx + 1:]
            for o in operands:
                _add_read(o)
            for d in dsts:
                _add_read(d)   # prior value is read
                _add_mutate(d)
        else:
            unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                               'reason': 'ADD missing TO or GIVING'})

    # -----------------------------------------------------------------------
    # SUBTRACT
    # -----------------------------------------------------------------------
    elif verb == 'SUBTRACT':
        upper_tokens = [t.upper() for t in tokens]
        if 'GIVING' in upper_tokens:
            giving_idx = upper_tokens.index('GIVING')
            from_idx = upper_tokens.index('FROM') if 'FROM' in upper_tokens else giving_idx
            operands = tokens[1:from_idx]
            minuend  = tokens[from_idx + 1:giving_idx]
            results  = tokens[giving_idx + 1:]
            for o in operands + minuend:
                _add_read(o)
            for r in results:
                _add_mutate(r)
        elif 'FROM' in upper_tokens:
            from_idx = upper_tokens.index('FROM')
            operands = tokens[1:from_idx]
            dsts     = tokens[from_idx + 1:]
            for o in operands:
                _add_read(o)
            for d in dsts:
                _add_read(d)
                _add_mutate(d)
        else:
            unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                               'reason': 'SUBTRACT missing FROM'})

    # -----------------------------------------------------------------------
    # MULTIPLY
    # -----------------------------------------------------------------------
    elif verb == 'MULTIPLY':
        upper_tokens = [t.upper() for t in tokens]
        if 'GIVING' in upper_tokens:
            by_idx     = upper_tokens.index('BY')     if 'BY'     in upper_tokens else 2
            giving_idx = upper_tokens.index('GIVING')
            operands = tokens[1:by_idx] + tokens[by_idx + 1:giving_idx]
            results  = tokens[giving_idx + 1:]
            for o in operands:
                _add_read(o)
            for r in results:
                _add_mutate(r)
        elif 'BY' in upper_tokens:
            by_idx = upper_tokens.index('BY')
            operands = tokens[1:by_idx]
            dsts     = tokens[by_idx + 1:]
            for o in operands:
                _add_read(o)
            for d in dsts:
                _add_read(d)
                _add_mutate(d)
        else:
            unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                               'reason': 'MULTIPLY missing BY'})

    # -----------------------------------------------------------------------
    # DIVIDE
    # -----------------------------------------------------------------------
    elif verb == 'DIVIDE':
        upper_tokens = [t.upper() for t in tokens]
        if 'GIVING' in upper_tokens:
            into_by_idx = next((i for i, t in enumerate(upper_tokens) if t in ('INTO', 'BY')), 2)
            giving_idx  = upper_tokens.index('GIVING')
            operands = tokens[1:into_by_idx] + tokens[into_by_idx + 1:giving_idx]
            results  = tokens[giving_idx + 1:]
            rem_idx  = upper_tokens.index('REMAINDER') if 'REMAINDER' in upper_tokens else None
            if rem_idx:
                results = tokens[giving_idx + 1:rem_idx]
                _add_mutate(tokens[rem_idx + 1])
            for o in operands:
                _add_read(o)
            for r in results:
                _add_mutate(r)
        elif 'INTO' in upper_tokens or 'BY' in upper_tokens:
            split_idx = next((i for i, t in enumerate(upper_tokens) if t in ('INTO', 'BY')), 2)
            operands  = tokens[1:split_idx]
            dsts      = tokens[split_idx + 1:]
            for o in operands:
                _add_read(o)
            for d in dsts:
                _add_read(d)
                _add_mutate(d)
        else:
            unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                               'reason': 'DIVIDE missing INTO/BY'})

    # -----------------------------------------------------------------------
    # COMPUTE
    # -----------------------------------------------------------------------
    elif verb == 'COMPUTE':
        upper_tokens = [t.upper() for t in tokens]
        if '=' in upper_tokens:
            eq_idx = upper_tokens.index('=')
            lhs_tokens = tokens[1:eq_idx]
            rhs_tokens = tokens[eq_idx + 1:]
            for l in lhs_tokens:
                _add_mutate(l)
            for r in rhs_tokens:
                if not is_literal(r) and r not in ('+', '-', '*', '/', '**', '(', ')'):
                    _add_read(r)
        else:
            unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                               'reason': 'COMPUTE missing = sign'})

    # -----------------------------------------------------------------------
    # INITIALIZE
    # -----------------------------------------------------------------------
    elif verb == 'INITIALIZE':
        for t in tokens[1:]:
            if t.upper() in ('REPLACING', 'BY', 'ALPHABETIC', 'ALPHANUMERIC',
                             'NUMERIC', 'ALPHANUMERIC-EDITED', 'NUMERIC-EDITED', 'ALL'):
                break
            _add_mutate(t)

    # -----------------------------------------------------------------------
    # READ
    # -----------------------------------------------------------------------
    elif verb == 'READ':
        upper_tokens = [t.upper() for t in tokens]
        file_name = tokens[1] if len(tokens) > 1 else None
        # Map file name to FD record name via qmap
        if file_name:
            _add_mutate(file_name)  # file record itself
        if 'INTO' in upper_tokens:
            into_idx = upper_tokens.index('INTO')
            dst = tokens[into_idx + 1] if into_idx + 1 < len(tokens) else None
            if dst:
                _add_mutate(dst)

    # -----------------------------------------------------------------------
    # WRITE
    # -----------------------------------------------------------------------
    elif verb == 'WRITE':
        upper_tokens = [t.upper() for t in tokens]
        record_name = tokens[1] if len(tokens) > 1 else None
        if record_name:
            _add_mutate(record_name)
        if 'FROM' in upper_tokens:
            from_idx = upper_tokens.index('FROM')
            src = tokens[from_idx + 1] if from_idx + 1 < len(tokens) else None
            if src:
                _add_read(src)

    # -----------------------------------------------------------------------
    # STRING
    # -----------------------------------------------------------------------
    elif verb == 'STRING':
        upper_tokens = [t.upper() for t in tokens]
        into_idx    = upper_tokens.index('INTO')    if 'INTO'    in upper_tokens else None
        pointer_idx = upper_tokens.index('POINTER') if 'POINTER' in upper_tokens else None
        if into_idx is not None:
            for t in tokens[1:into_idx]:
                if t.upper() not in ('DELIMITED', 'BY', 'SIZE'):
                    _add_read(t)
            dst = tokens[into_idx + 1] if into_idx + 1 < len(tokens) else None
            if dst:
                _add_mutate(dst)
        if pointer_idx is not None:
            ptr = tokens[pointer_idx + 1] if pointer_idx + 1 < len(tokens) else None
            if ptr:
                _add_read(ptr)
                _add_mutate(ptr)

    # -----------------------------------------------------------------------
    # UNSTRING
    # -----------------------------------------------------------------------
    elif verb == 'UNSTRING':
        upper_tokens = [t.upper() for t in tokens]
        src = tokens[1] if len(tokens) > 1 else None
        if src:
            _add_read(src)
        into_idx     = upper_tokens.index('INTO')      if 'INTO'      in upper_tokens else None
        pointer_idx  = upper_tokens.index('POINTER')   if 'POINTER'   in upper_tokens else None
        tallying_idx = upper_tokens.index('TALLYING')  if 'TALLYING'  in upper_tokens else None
        end_idx = min(x for x in [pointer_idx, tallying_idx, len(tokens)] if x is not None)
        if into_idx is not None:
            for t in tokens[into_idx + 1:end_idx]:
                if t.upper() not in ('DELIMITED', 'BY', 'ALL', 'DELIMITER', 'COUNT', 'IN'):
                    _add_mutate(t)
        if pointer_idx is not None:
            ptr = tokens[pointer_idx + 1] if pointer_idx + 1 < len(tokens) else None
            if ptr:
                _add_read(ptr)
                _add_mutate(ptr)
        if tallying_idx is not None:
            t_var = tokens[tallying_idx + 2] if tallying_idx + 2 < len(tokens) else None
            if t_var:
                _add_mutate(t_var)

    # -----------------------------------------------------------------------
    # ACCEPT
    # -----------------------------------------------------------------------
    elif verb == 'ACCEPT':
        dst = tokens[1] if len(tokens) > 1 else None
        if dst:
            _add_mutate(dst)

    # -----------------------------------------------------------------------
    # DISPLAY
    # -----------------------------------------------------------------------
    elif verb == 'DISPLAY':
        for t in tokens[1:]:
            if t.upper() in ('UPON', 'WITH', 'NO', 'ADVANCING'):
                break
            _add_read(t)

    # -----------------------------------------------------------------------
    # IF / EVALUATE / WHEN
    # -----------------------------------------------------------------------
    elif verb in ('IF', 'EVALUATE', 'WHEN'):
        skip_keywords = {'IF', 'EVALUATE', 'WHEN', 'THEN', 'ELSE', 'END-IF',
                         'AND', 'OR', 'NOT', 'TRUE', 'FALSE', 'OTHER',
                         'EQUAL', 'TO', 'THAN', 'GREATER', 'LESS', 'THROUGH',
                         'THRU', 'ALSO', '=', '>', '<', '>=', '<='}
        for t in tokens[1:]:
            if t.upper() in skip_keywords or is_literal(t):
                continue
            _add_read(t)

    # -----------------------------------------------------------------------
    # SET
    # -----------------------------------------------------------------------
    elif verb == 'SET':
        upper_tokens = [t.upper() for t in tokens]
        if 'TO' in upper_tokens:
            to_idx = upper_tokens.index('TO')
            targets = tokens[1:to_idx]
            sources = tokens[to_idx + 1:]
            for tgt in targets:
                _add_mutate(tgt)
            for src in sources:
                if src.upper() not in ('TRUE', 'FALSE', 'ON', 'OFF', 'UP', 'DOWN'):
                    _add_read(src)
        else:
            unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                               'reason': 'SET missing TO'})

    # -----------------------------------------------------------------------
    # EXEC CICS
    # -----------------------------------------------------------------------
    elif verb == 'EXEC':
        upper_tokens = [t.upper() for t in tokens]
        cics_clauses_read   = {'FROM', 'LENGTH', 'RESP', 'RESP2'}
        cics_clauses_mutate = {'INTO', 'RESP', 'RESP2'}
        i = 0
        while i < len(tokens):
            t_upper = tokens[i].upper()
            if t_upper in cics_clauses_read and i + 1 < len(tokens):
                _add_read(tokens[i + 1])
            if t_upper in cics_clauses_mutate and i + 1 < len(tokens):
                _add_mutate(tokens[i + 1])
            i += 1

    # -----------------------------------------------------------------------
    # PERFORM - not a data-flow event
    # -----------------------------------------------------------------------
    elif verb == 'PERFORM':
        pass

    # -----------------------------------------------------------------------
    # CALL - log as unresolved (known mutator not yet fully implemented)
    # -----------------------------------------------------------------------
    elif verb == 'CALL':
        unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                           'reason': 'CALL USING not yet classified (TODO Section 3)'})

    # -----------------------------------------------------------------------
    # OPEN / CLOSE / STOP / GOBACK / CONTINUE / EXIT
    # -----------------------------------------------------------------------
    elif verb in ('OPEN', 'CLOSE', 'STOP', 'GOBACK', 'CONTINUE', 'EXIT',
                  'GO', 'NEXT', 'END-READ', 'END-WRITE', 'END-IF',
                  'END-EVALUATE', 'END-PERFORM', 'END-STRING', 'END-UNSTRING',
                  'END-COMPUTE', 'END-ADD', 'END-SUBTRACT', 'END-MULTIPLY',
                  'END-DIVIDE', 'END-EXEC'):
        pass  # control-flow or scope terminators

    # -----------------------------------------------------------------------
    # Anything else - ignore silently (no-op per spec)
    # -----------------------------------------------------------------------
    # Known future verbs that are mutators go to unresolved
    _future_mutators = {'INSPECT', 'SORT', 'MERGE', 'RELEASE', 'RETURN'}
    if verb in _future_mutators:
        unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                           'reason': f'{verb} not yet classified (TODO)'})


# ---------------------------------------------------------------------------
# Main extraction logic
# ---------------------------------------------------------------------------

def extract_data_flow(cbl_path: Path, layout_path: Path) -> dict:
    program_name = cbl_path.stem.upper()
    raw = cbl_path.read_text(encoding='utf-8', errors='replace')
    lines = _normalise_source(raw)

    qmap_result = build_qmap(layout_path)
    if isinstance(qmap_result, tuple):
        qmap, record_names = qmap_result
    else:
        qmap, record_names = qmap_result, set()

    paragraphs = extract_paragraphs(lines)

    # Check paragraph count against facts file
    program_unresolved = []
    facts_path = FACTS_DIR / f"{program_name}.json"
    if facts_path.exists():
        with open(facts_path, encoding='utf-8') as fh:
            facts = json.load(fh)
        expected_para = facts.get('paragraphs_defined', None)
        actual_para = len([k for k in paragraphs if k != '__MAIN__'])
        if expected_para is not None and abs(actual_para - expected_para) > 1:
            msg = (f"paragraph count mismatch: local={actual_para} "
                   f"facts={expected_para}")
            print(f"WARNING [{program_name}]: {msg}", file=sys.stderr)
            program_unresolved.append({'issue': msg})

    paragraph_data_flow = {}
    for para_name, para_lines in paragraphs.items():
        if para_name == '__MAIN__':
            continue
        reads    = []
        mutates  = []
        unresolved = []
        context_records: set = set()

        # Join continuation lines then classify each statement
        joined = _join_lines(para_lines)
        for lineno, text in joined:
            # Split on sentence boundaries (period) roughly
            parts = re.split(r'\.(?=\s|$)', text)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                # Tokenise and dispatch on each verb found in the part
                # (handles inline verb sequences like IF ... MOVE ... END-IF)
                _dispatch_inline(lineno, part, qmap, context_records,
                                 reads, mutates, unresolved)

        paragraph_data_flow[para_name] = {
            'reads':      reads,
            'mutates':    mutates,
            'unresolved': unresolved,
        }

    return {
        'program':             program_name,
        'schema_version':      SCHEMA_VERSION,
        'paragraph_data_flow': paragraph_data_flow,
        'program_unresolved':  program_unresolved,
    }


def _dispatch_inline(
    lineno: int,
    text: str,
    qmap: dict,
    context_records: set,
    reads: list,
    mutates: list,
    unresolved: list,
):
    """
    Split a text fragment on known verb boundaries and classify each sub-statement.
    Handles inline compound statements (IF cond MOVE a TO b END-IF).
    """
    _VERB_SPLIT_RE = re.compile(
        r'(?:^|\s)(?=(?:MOVE|ADD|SUBTRACT|MULTIPLY|DIVIDE|COMPUTE|INITIALIZE|'
        r'READ|WRITE|STRING|UNSTRING|ACCEPT|DISPLAY|IF|EVALUATE|WHEN|SET|EXEC|'
        r'PERFORM|CALL|OPEN|CLOSE|STOP|GOBACK|CONTINUE|EXIT|GO|END-IF|'
        r'END-EVALUATE|END-PERFORM|END-READ|END-WRITE|END-EXEC|'
        r'END-COMPUTE|END-ADD|END-SUBTRACT|END-MULTIPLY|END-DIVIDE|'
        r'END-STRING|END-UNSTRING)(?:\s|$))',
        re.IGNORECASE,
    )
    parts = _VERB_SPLIT_RE.split(text)
    for part in parts:
        part = part.strip()
        if part:
            classify_statement(lineno, part, qmap, context_records,
                               reads, mutates, unresolved)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def run_single(cbl_path: Path, out_fh=None):
    program_name = cbl_path.stem.upper()
    layout_path  = BYTE_LAYOUTS_DIR / f"{program_name}.json"
    result = extract_data_flow(cbl_path, layout_path)
    n_unresolved = sum(
        len(p['unresolved']) for p in result['paragraph_data_flow'].values()
    ) + len(result['program_unresolved'])
    if n_unresolved:
        print(f"[{program_name}] unresolved_count={n_unresolved}", file=sys.stderr)
    output = json.dumps(result, indent=2)
    if out_fh:
        out_fh.write(output)
    else:
        print(output)


def run_all():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cbl_files = sorted(CBL_DIR.glob('*.cbl')) + sorted(CBL_DIR.glob('*.CBL'))
    # Deduplicate by stem
    seen = set()
    unique = []
    for f in cbl_files:
        if f.stem.upper() not in seen:
            seen.add(f.stem.upper())
            unique.append(f)
    print(f"[corpus] processing {len(unique)} programs...", file=sys.stderr)
    for cbl_path in unique:
        program_name = cbl_path.stem.upper()
        out_path = OUT_DIR / f"{program_name}.json"
        try:
            with open(out_path, 'w', encoding='utf-8') as fh:
                run_single(cbl_path, out_fh=fh)
        except Exception as exc:
            print(f"[{program_name}] ERROR: {exc}", file=sys.stderr)
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

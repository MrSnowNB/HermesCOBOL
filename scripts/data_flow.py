#!/usr/bin/env python3
"""
data_flow.py  --  Section 2: deterministic per-paragraph reads[]/mutates[] extractor.

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

SCHEMA_VERSION = "1.2"
BYTE_LAYOUTS_DIR = Path("data/byte_layouts")
CBL_DIR          = Path("data/raw/cbl")
OUT_DIR          = Path("data/data_flow")
FACTS_DIR        = Path("data/facts")

_SEQ_RE = re.compile(r'^\d{6}(.*)$')
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

# CardDemo paragraph labels always start with a 4-digit numeric prefix.
_CARDEMO_PARA_PREFIX_RE = re.compile(r'^\d{4}-', re.IGNORECASE)

_PARA_HEADER_RE = re.compile(
    r'^([A-Z0-9][A-Z0-9\-]*)\s*\.\s*$',
    re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Source normalisation
# ---------------------------------------------------------------------------

def _strip_seq(line: str) -> str:
    m = _SEQ_RE.match(line)
    return m.group(1) if m else line


def _normalise_source(raw: str) -> list:
    result = []
    for lineno, raw_line in enumerate(raw.splitlines(), start=1):
        line = _strip_seq(raw_line)
        if not line:
            continue
        indicator = line[0]
        if indicator in ('*', '/', '$'):
            continue
        text = line[1:72].rstrip() if len(line) > 1 else ''
        if text.strip():
            result.append((lineno, text))
    return result


# ---------------------------------------------------------------------------
# Period-aware helpers
# ---------------------------------------------------------------------------

def _ends_statement(text: str) -> bool:
    """True if the last non-space character outside quotes is a period."""
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
    """True if the stripped text looks like a paragraph/section header label."""
    stripped = text.strip()
    m = _PARA_HEADER_RE.match(stripped)
    if not m:
        return False
    candidate = m.group(1).upper()
    return candidate not in _NOT_PARA


# ---------------------------------------------------------------------------
# Targeted continuation joiner for procedure-division source lines
# ---------------------------------------------------------------------------

def _join_source_lines(lines: list) -> list:
    """
    Fuse physical continuation lines back into their logical predecessor.

    A line is treated as a continuation candidate ONLY when ALL three
    conditions hold:
      1. The predecessor did NOT end with a statement-terminating period.
      2. The candidate line is NOT a paragraph/section header
         (i.e. does not match _PARA_HEADER_RE or is in _NOT_PARA).
      3. The candidate does NOT start with the CardDemo 4-digit prefix
         pattern (^\d{4}-)  -- extra guard to preserve real paragraph names
         that the regex alone might mis-classify.

    This targets exactly the two offending patterns:
        MOVE A TO B
                   WS-REISSUE-DATE.    <- continuation target, no prefix
        MOVE A TO B
                   VB2-ACCT-ID.        <- same
    while leaving all real paragraph headers (0000-, 1000-, ...) intact.
    """
    if not lines:
        return []
    joined = [[lines[0][0], lines[0][1]]]
    for lineno, text in lines[1:]:
        stripped = text.strip()
        prev_ends = _ends_statement(joined[-1][1])
        candidate_is_header = _is_para_header_line(text)
        candidate_has_prefix = bool(_CARDEMO_PARA_PREFIX_RE.match(stripped))

        if (not prev_ends
                and not candidate_is_header
                and not candidate_has_prefix):
            joined[-1][1] = joined[-1][1] + ' ' + stripped
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
    return matches


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
# Period splitter that respects quoted strings
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
# Paragraph extractor
# ---------------------------------------------------------------------------

def extract_paragraphs(lines: list) -> dict:
    """
    Extract paragraphs from normalised source lines.

    Procedure-division lines are first passed through _join_source_lines()
    so that MOVE continuation targets sitting alone on their own line
    (e.g. WS-REISSUE-DATE.) are fused back into their statement and never
    mistaken for paragraph headers.
    """
    paragraphs = {}
    current = '__MAIN__'
    paragraphs[current] = []

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
        m = _PARA_HEADER_RE.match(stripped)
        if m:
            candidate = m.group(1).upper()
            if candidate in _NOT_PARA:
                paragraphs[current].append((lineno, text))
            else:
                current = candidate
                if current not in paragraphs:
                    paragraphs[current] = []
        else:
            paragraphs[current].append((lineno, text))
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
):
    raw_text = text.strip().rstrip('.')
    tokens = _tokens(raw_text)
    if not tokens:
        return
    verb = tokens[0].upper()

    def _add_read(name):
        if name == '__LIT__' or is_literal(name):
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
        if name == '__LIT__' or is_literal(name):
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

    if verb == 'MOVE':
        if len(tokens) >= 2 and tokens[1].upper() == 'CORRESPONDING':
            try:
                to_idx = [t.upper() for t in tokens].index('TO')
                src_group = tokens[2] if to_idx > 2 else None
                dst_group = tokens[to_idx + 1] if to_idx + 1 < len(tokens) else None
                if src_group: _add_read(src_group)
                if dst_group: _add_mutate(dst_group)
                src_upper = (src_group or '').upper()
                dst_upper = (dst_group or '').upper()
                src_leaves = {e['field'].split('.')[-1].upper() for e in qmap.get(src_upper, [])}
                for de in qmap.get(dst_upper, []):
                    if de['field'].split('.')[-1].upper() in src_leaves and de not in mutates:
                        mutates.append(de)
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
                if r != '__LIT__' and not is_literal(r) and r not in ('+','-','*','/','**','(',')'):  
                    _add_read(r)
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
            if tv: _add_mutate(tv)

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
        cics_r = {'FROM','LENGTH','RESP','RESP2'}
        cics_m = {'INTO','RESP','RESP2'}
        for i, t in enumerate(tokens):
            tu = t.upper()
            if tu in cics_r and i + 1 < len(tokens) and tokens[i+1] != '__LIT__':
                _add_read(tokens[i + 1])
            if tu in cics_m and i + 1 < len(tokens) and tokens[i+1] != '__LIT__':
                _add_mutate(tokens[i + 1])

    elif verb == 'PERFORM':
        pass

    elif verb == 'CALL':
        unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                           'reason': 'CALL USING not yet classified (TODO Section 3)'})

    elif verb in ('OPEN','CLOSE','STOP','GOBACK','CONTINUE','EXIT',
                  'GO','NEXT','END-READ','END-WRITE','END-IF',
                  'END-EVALUATE','END-PERFORM','END-STRING','END-UNSTRING',
                  'END-COMPUTE','END-ADD','END-SUBTRACT','END-MULTIPLY',
                  'END-DIVIDE','END-EXEC'):
        pass

    if verb in ('INSPECT','SORT','MERGE','RELEASE','RETURN'):
        unresolved.append({'verb': verb, 'line_no': lineno, 'raw_text': raw_text,
                           'reason': f'{verb} not yet classified (TODO)'})


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

            actual_para = len([k for k in paragraphs if k != '__MAIN__'])
            if expected_para is not None and abs(actual_para - expected_para) > 1:
                msg = (f"paragraph count mismatch: local={actual_para} "
                       f"facts={expected_para}")
                print(f"WARNING [{program_name}]: {msg}", file=sys.stderr)
                program_unresolved.append({'issue': msg})
        except Exception as exc:
            print(f"WARNING [{program_name}]: could not read facts: {exc}", file=sys.stderr)

    paragraph_data_flow = {}
    for para_name, para_lines in paragraphs.items():
        if para_name == '__MAIN__':
            continue
        reads = []; mutates = []; unresolved_list = []
        context_records: set = set()

        for lineno, text in _join_lines(para_lines):
            for part in _split_on_period(text):
                if part:
                    _dispatch_inline(lineno, part, qmap, context_records,
                                     reads, mutates, unresolved_list)

        paragraph_data_flow[para_name] = {
            'reads':      reads,
            'mutates':    mutates,
            'unresolved': unresolved_list,
        }

    return {
        'program':             program_name,
        'schema_version':      SCHEMA_VERSION,
        'paragraph_data_flow': paragraph_data_flow,
        'program_unresolved':  program_unresolved,
    }


def _dispatch_inline(lineno, text, qmap, context_records, reads, mutates, unresolved):
    _VERB_SPLIT_RE = re.compile(
        r'(?:^|\s)(?=(?:MOVE|ADD|SUBTRACT|MULTIPLY|DIVIDE|COMPUTE|INITIALIZE|'
        r'READ|WRITE|STRING|UNSTRING|ACCEPT|DISPLAY|IF|EVALUATE|WHEN|SET|EXEC|'
        r'PERFORM|CALL|OPEN|CLOSE|STOP|GOBACK|CONTINUE|EXIT|GO|END-IF|'
        r'END-EVALUATE|END-PERFORM|END-READ|END-WRITE|END-EXEC|'
        r'END-COMPUTE|END-ADD|END-SUBTRACT|END-MULTIPLY|END-DIVIDE|'
        r'END-STRING|END-UNSTRING)(?:\s|$))',
        re.IGNORECASE,
    )
    for part in _VERB_SPLIT_RE.split(text):
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

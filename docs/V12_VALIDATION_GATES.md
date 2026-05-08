# HermesCOBOL Validation Gates — Schema v1.2 / v1.3

## Section 2 Gate (FROZEN — commit `609922d` / `f8d1eaf`)

**Branch:** `feature/schema-v1.2-section2-dataflow` → merged to `main` 2026-05-08

### Passing criteria (verified locally and on CI)

| Criterion | Expected |
|---|---|
| `test_data_flow.py` | 18/18 PASS |
| `CBACT01C` paragraph_count | 16 |
| `CBACT01C` para_diff | local=16 facts=16, no delta |
| `1300_unresolved` | CALL `COBDATFT` USING — accepted Section 3 TODO |
| `1350_unresolved` | `[]` |
| `program_unresolved` | `[]` |
| `data_flow.py --all` | 31 files, 0 ERROR lines |

### Frozen contracts (must not change without re-gating)

- `_join_source_lines` — 4-digit prefix guard (Section 2 version, superseded in Section 3.1)
- `extract_paragraphs` — procedure-division only, `_join_source_lines` then `_PARA_HEADER_RE`
- `_mask_literals` — equal-length underscore replacement of quoted strings
- `_dispatch_inline` — verb-splits on masked copy, slices parts from original text

---

## Section 3.1 Gate (FROZEN — commit `e3aa8ae`, merged to `main` 2026-05-08)

**Branch:** `feature/schema-v1.3-section3-paradetect` → merged to `main`

### LOCKED: `_normalise_source` column contract

`_normalise_source` **must** use fixed COBOL column positions unconditionally:

```python
indicator = line[6]        # col 7 (0-based index 6) — always the indicator
code      = line[7:72]     # cols 8-72 (0-based 7:72) — always the code area
```

- **No** calls to `_strip_seq` inside `_normalise_source`.
- **No** regex used to locate the indicator column.
- Lines shorter than 7 characters are silently skipped.
- Lines with indicator `'*'`, `'/'`, or `'$'` are comment/directive lines and skipped.
- This applies to ALL input: real corpus files (digit sequence) and synthetic test
  source (blank sequence). The column positions are invariant.

`_strip_seq` is retained for backward compatibility but is **not** called from
`_normalise_source` or any other internal function.

### LOCKED: Inline test source format

Synthetic CBL source strings in `tests/test_data_flow.py` **must** use the
**blank-sequence-area** form:

```
"       PROCEDURE DIVISION.\n"   # 6 blank seq cols + 1 indicator space + code
"       MAIN-PARA.\n"
"           MOVE A TO B.\n"      # Area B: 11 leading spaces (or more)
```

- Do **not** use fabricated 6-digit sequence prefixes (`"000001 PROCEDURE DIVISION.\n"`).
- Blank-sequence form correctly simulates cols 1–6 = spaces, exactly what
  `_normalise_source` sees for source files without sequence numbers.
- The fixed-column implementation handles both digit and blank sequences identically.

### SECTION header policy

SECTION headers are NOT counted as paragraphs. See 3.1 branch notes for full rationale.

### Area-A paragraph detection rule (`_is_area_a_paragraph`)

After `_normalise_source` strips sequence (cols 1–6) and indicator (col 7),
**column 8** of the original source lands at `text[0]`. A line is a paragraph
header if and only if ALL of the following hold:

1. `text[0] != ' '` (Area A: not indented)
2. Does NOT match `_LEVEL_NUM_RE` (not a data item)
3. Does NOT match `_SECTION_HEADER_RE` (not a section header)
4. Matches `_PARA_HEADER_RE` (`^([A-Z0-9][A-Z0-9-]*)\s*\.\s*$`)
5. Candidate name NOT in `_NOT_PARA`
6. Candidate name NOT in `_NOT_HEADER_KEYWORDS`

### 3.1 Gate criteria (FROZEN — 37/37 PASS on `e3aa8ae`)

```powershell
python tests\test_data_flow.py
# -> 37/37 PASS

python scripts\data_flow.py data\raw\cbl\CBACT01C.cbl > data\data_flow\CBACT01C.json
python -c "..."
# -> paragraph_count=16, program_unresolved=[]

python scripts\para_diff.py CBACT01C
# -> local=16 facts=16, no delta

python scripts\data_flow.py --all
# -> 31 files, 0 ERROR, ZERO local=0, ZERO local=1
# -> Allowed: COACTUPC/COACTVWC/COCRDLIC close-mismatch WARNINGs (deferred to 3.4)
```

---

## Section 3.2 Gate (FROZEN — commit `e9f68d3`, merged to `main` 2026-05-08)

**Branch:** `feature/schema-v1.3-section3-call-using` → merged to `main`

### LOCKED: `_parse_call` single-pass cursor contract

`_parse_call` **must** use a single forward-scanning cursor starting at
token index 2 (immediately after `CALL` + target token). The cursor
processes all remaining tokens in one pass:

```python
in_using       = False
mode           = 'REFERENCE'   # default USING operand mode
returning_next = False         # True: next identifier -> mutate only, then stop

i = 2   # always start after CALL + target
while i < len(ut):
    tok = ut[i]
    if tok in _CALL_STOP_KEYWORDS: break
    if tok == 'USING':     in_using = True; mode = 'REFERENCE'; i+=1; continue
    if tok == 'RETURNING': returning_next = True; in_using = False; i+=1; continue
    if tok == 'BY': ...    # update mode from next token
    # operand: check returning_next first, then in_using + mode
```

**Why this matters:** `CALL 'X' RETURNING id` (no `USING`) must still produce
a mutate for `id`. An implementation that only enters the cursor loop after
finding `USING` silently drops RETURNING-without-USING operands.

### LOCKED: Mode semantics

| Mode | Reads | Mutates |
|---|---|---|
| `BY REFERENCE` (default inside USING) | ✓ | ✓ |
| `BY CONTENT` | ✓ | ✗ |
| `BY VALUE` | ✓ | ✗ |
| `RETURNING` (anywhere after target) | ✗ | ✓ |

### LOCKED: `call_graph` key

Every program output JSON **must** include a top-level `call_graph` key:

```json
"call_graph": {
  "CBACT01C": ["COBDATFT", "CEE3ABD"]
}
```

- Value is an ordered list of unique static call targets (string literals
  and bare identifiers after `CALL`).
- `CBACT01C.call_graph` MUST contain `'COBDATFT'` and MAY contain additional
  runtime targets (e.g. `'CEE3ABD'`) that are correct and expected.

### LOCKED: `unresolved_count` is informational only

`unresolved_count` (the per-program stderr line) is **not** a gate criterion.
Small ±1–4 shifts relative to prior gates are expected whenever a new verb
handler classifies previously-unclassified tokens. The gate criteria that
matter are:

- All tests PASS
- `1300_unresolved == []`
- `--all` zero `local=0` and zero `local=1` WARNINGs
- Only the three documented close-mismatch WARNINGs allowed
  (COACTUPC, COACTVWC, COCRDLIC)

### 3.2 Gate criteria (FROZEN — 47/47 PASS on `e9f68d3`)

```powershell
python tests\test_data_flow.py
# -> 47/47 PASS
#    Includes: TestCallUsingByReference (3), TestCallUsingByContent (1),
#              TestCallUsingByValue (1), TestCallReturning (3),
#              TestCallMixedModes (1), TestCallGraphCbact01c (1)

python scripts\data_flow.py data\raw\cbl\CBACT01C.cbl > data\data_flow\CBACT01C.json
python -c "import json; d=json.load(open(r'data\\data_flow\\CBACT01C.json')); \
           print('call_graph=', d['call_graph']); \
           print('1300_unresolved=', d['paragraph_data_flow']['1300-POPUL-ACCT-RECORD']['unresolved'])"
# -> call_graph={'CBACT01C': ['COBDATFT', 'CEE3ABD']}
# -> 1300_unresolved=[]

python scripts\data_flow.py --all
# -> 31 files, 0 ERROR
# -> ZERO local=0 WARNINGs, ZERO local=1 WARNINGs
# -> Allowed: COACTUPC / COACTVWC / COCRDLIC close-mismatch WARNINGs only
```

### Frozen contracts (do NOT touch in 3.3 or later without re-gating 3.2)

`_normalise_source`, `_join_source_lines`, `extract_paragraphs`,
`_is_area_a_paragraph`, `_mask_literals`, `_dispatch_inline`

---

## Section 3.3 Gate — Missing Verb Handlers

**Branch:** `feature/schema-v1.3-section3-verbs`  
**Prerequisite:** rebased onto post-3.2 main before merge.

### Specification

Add deterministic handlers for the five verbs currently emitting
`reason: 'VERB not yet classified (TODO)'` in the corpus:

| Verb | Operand semantics |
|---|---|
| `INSPECT` | source identifier (read); TALLYING/REPLACING targets (mutate) |
| `SORT` | file name (mutate); USING files (read); GIVING files (mutate) |
| `MERGE` | file name (mutate); USING files (read); GIVING files (mutate) |
| `RELEASE` | record name (mutate); FROM source (read) |
| `RETURN` | file name (mutate); INTO target (mutate) |

### 3.3 Gate criteria

```powershell
python tests\test_data_flow.py
# -> 52+ PASS (47 + at least 5 new verb handler tests, one per verb)

python scripts\data_flow.py --all
# -> 31 files, 0 ERROR
# -> ZERO local=0 WARNINGs, ZERO local=1 WARNINGs
# -> Zero corpus lines for INSPECT/SORT/MERGE/RELEASE/RETURN produce
#    an unresolved entry with reason 'UNKNOWN_VERB' or 'not yet classified'
# -> Only COACTUPC / COACTVWC / COCRDLIC close-mismatch WARNINGs allowed
```

### Frozen contracts (do NOT touch in 3.3)

All contracts locked in 3.1 and 3.2.

---

## Section 3.4 Gate — Schema v1.3 + `section_name` (planned)

- `SCHEMA_VERSION` bumped to `"1.3"`
- `section_name` field added to each paragraph entry
- Close-mismatch WARNINGs resolved: COACTUPC, COACTVWC, COCRDLIC, COCRDSLC, COCRDUPC

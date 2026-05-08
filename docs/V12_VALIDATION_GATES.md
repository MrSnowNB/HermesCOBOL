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

- Do **not** use fabricated 6-digit sequence prefixes.
- Blank-sequence form correctly simulates cols 1–6 = spaces, exactly what
  `_normalise_source` sees for source files without sequence numbers.

### SECTION header policy

**Decision: SECTION headers are NOT counted as paragraphs.**

### Division/section exclusion list (`_NOT_HEADER_KEYWORDS`)

The following tokens are structural COBOL keywords and **never** paragraph names:
`IDENTIFICATION, ENVIRONMENT, DATA, PROCEDURE, WORKING-STORAGE, LINKAGE, FILE,
LOCAL-STORAGE, INPUT-OUTPUT, CONFIGURATION, COMMUNICATION, REPORT, FILE-CONTROL,
SPECIAL-NAMES, SOURCE-COMPUTER, OBJECT-COMPUTER, REPOSITORY, CLASS-CONTROL`

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
python tests\test_data_flow.py        # 37/37 PASS
# CBACT01C paragraph_count=16, program_unresolved=[]
# para_diff: local=16 facts=16, no delta
# --all: 31 files, 0 ERROR, ZERO local=0 WARNINGs, ZERO local=1 WARNINGs
# Allowed: COACTUPC/COACTVWC/COCRDLIC close-mismatch (deferred to 3.4)
```

---

## Section 3.2 Gate (FROZEN — commit `e9f68d3`, merged to `main` 2026-05-08)

**Branch:** `feature/schema-v1.3-section3-call-using` → merged to `main`

### LOCKED: `_parse_call()` contract

`_parse_call()` **must** use a **single-pass forward cursor** starting at token
index 2 (the first token after `CALL target`), scanning unconditionally regardless
of whether `USING` appears:

```python
in_using       = False
mode           = 'REFERENCE'  # default when inside USING
returning_next = False        # next identifier after RETURNING -> mutate only, then stop

i = 2   # always skip CALL + target
while i < len(ut):
    if tok == 'USING':      in_using = True; mode = 'REFERENCE'
    if tok == 'RETURNING':  returning_next = True; in_using = False
    if tok == 'BY':         mode = ut[i+1] if ut[i+1] in (...)
    # operand: check returning_next first, then in_using + mode
```

- `RETURNING` sets mutate-only mode **unconditionally** (with or without a
  preceding `USING` clause). The next identifier token is added to mutates only,
  then the cursor stops.
- **Do NOT** use `ut.index('USING')` to gate entry into the operand loop.

### Mode semantics (LOCKED)

| Mode | Reads | Mutates |
|---|---|---|
| `BY REFERENCE` (default inside USING) | ✓ | ✓ |
| `BY CONTENT` | ✓ | ✗ |
| `BY VALUE` | ✓ | ✗ |
| `RETURNING` (anywhere after target) | ✗ | ✓ |

### LOCKED: `call_graph` key

Every output JSON **must** contain:

```json
"call_graph": {
  "PROGRAM_NAME": ["CALLED_PROG_1", "CALLED_PROG_2"]
}
```

- Keys are static call targets only (string literals and bare identifiers
  following `CALL`).
- `CBACT01C.call_graph` **MUST** contain `'COBDATFT'`.
- Additional runtime targets (e.g. `'CEE3ABD'`) **MAY** appear and are correct.

### Note on `unresolved_count` drift

`unresolved_count` is an **informational metric only** and is **not** a gate
criterion. Small ±1 to ±4 shifts between 3.1 and 3.2 are expected: `_parse_call()`
now classifies CALL operands, so some previously unclassified tokens now resolve
(count drops) and some Linkage-Section operands are correctly extracted as
unresolved (count rises). Both behaviors are correct.

### 3.2 Gate criteria (FROZEN — 47/47 PASS on `e9f68d3`)

```powershell
python tests\test_data_flow.py
# -> 47/47 PASS
#    Includes TestCallUsingByReference (3), TestCallUsingByContent (1),
#    TestCallUsingByValue (1), TestCallReturning (3 incl. no-USING case),
#    TestCallMixedModes (1), TestCallGraphCbact01c (1)

python scripts\data_flow.py data\raw\cbl\CBACT01C.cbl > data\data_flow\CBACT01C.json
python -c "import json; d=json.load(open(r'data\\data_flow\\CBACT01C.json')); \
           print('call_graph=', d['call_graph']); \
           print('1300_unresolved=', d['paragraph_data_flow']['1300-POPUL-ACCT-RECORD']['unresolved'])"
# -> call_graph={'CBACT01C': ['COBDATFT', 'CEE3ABD']}
# -> 1300_unresolved=[]

python scripts\data_flow.py --all
# -> 31 files, 0 ERROR
# -> ZERO WARNINGs with local=0
# -> ZERO WARNINGs with local=1
# -> Allowed: COACTUPC, COACTVWC, COCRDLIC close-mismatch (deferred to 3.4)
```

### Frozen contracts (must not change in 3.3 or later without re-gating)

`_normalise_source`, `_join_source_lines`, `extract_paragraphs`,
`_is_area_a_paragraph`, `_mask_literals`, `_dispatch_inline`

---

## Section 3.3 Gate — Missing Verb Handlers

**Branch:** `feature/schema-v1.3-section3-verbs`  
**Prerequisite:** 3.2 merged to main; branch rebased onto post-3.2 main.

### Specification

- Add handlers for: `INSPECT`, `SORT`, `MERGE`, `RELEASE`, `RETURN`
- After each handler: zero corpus lines for that verb may produce an
  unresolved entry with reason `UNKNOWN_VERB`
- Currently these verbs emit a `TODO` unresolved entry; the handler
  replaces that with proper read/mutate classification.

### Frozen contracts (must NOT touch in 3.3)

All contracts locked in 3.1 and 3.2, plus `_parse_call()`.

---

## Section 3.4 Gate — Schema v1.3 + `section_name` (planned)

- `SCHEMA_VERSION` bumped to `"1.3"`
- `section_name` field added to each paragraph entry
- Close-mismatch WARNINGs resolved: COACTUPC, COACTVWC, COCRDLIC, COCRDSLC, COCRDUPC

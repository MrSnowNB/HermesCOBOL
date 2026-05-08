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

**Decision: SECTION headers are NOT counted as paragraphs.**

Rationale:
- The CardDemo corpus does not use `PROCEDURE DIVISION SECTION` headers in
  programs with a 4-digit paragraph naming scheme.
- Section names are listed in `facts/PROGRAM.json` under `sections_defined`,
  not `paragraphs_defined`.
- Counting section headers as paragraphs would inflate `local` counts.
- If future programs require section-as-paragraph semantics, introduce a
  `count_sections_as_paragraphs: bool` flag rather than changing the default.

Implementation: `_SECTION_HEADER_RE` matches `NAME SECTION.` or
`NAME SECTION USING`. Any line matching this pattern is excluded by
`_is_area_a_paragraph()`.

### Division/section exclusion list (`_NOT_HEADER_KEYWORDS`)

The following tokens, when appearing as the first word of an Area-A line,
are structural COBOL keywords and **never** paragraph names:

```
IDENTIFICATION, ENVIRONMENT, DATA, PROCEDURE
WORKING-STORAGE, LINKAGE, FILE, LOCAL-STORAGE
INPUT-OUTPUT, CONFIGURATION, COMMUNICATION, REPORT
FILE-CONTROL, SPECIAL-NAMES, SOURCE-COMPUTER, OBJECT-COMPUTER
REPOSITORY, CLASS-CONTROL
```

Level-number data items (`01 NAME.`, `77 NAME.`, `05 FILLER.`) are excluded
via `_LEVEL_NUM_RE` (`^\d{2}\s`).

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

Consequences:
- 4-digit CardDemo paragraphs (`0000-ACCTFILE-OPEN.`) → detected ✓
- Free-form paragraphs (`MAIN-PARA.`, `PROCESS-ENTER-KEY.`) → detected ✓
- Indented MOVE targets (`    WS-REISSUE-DATE.`) → NOT detected (rule 1) ✓
- Division headers (`PROCEDURE DIVISION.`) → NOT detected (rule 6) ✓
- Section headers (`WORKING-STORAGE SECTION.`) → NOT detected (rule 3) ✓
- Level numbers (`01 WS-REC.`) → NOT detected (rule 2) ✓

### 3.1 Gate criteria (FROZEN — 37/37 PASS on `e3aa8ae`)

```powershell
python tests\test_data_flow.py
# -> 37/37 PASS
#    Includes: TestNormaliseSourceColumnLayout (5 cases)
#    Includes: TestCbact01cRealFileParagraphCount (1 case, reads real disk file)

python scripts\data_flow.py data\raw\cbl\CBACT01C.cbl > data\data_flow\CBACT01C.json
python -c "import json; d=json.load(open(r'data\\data_flow\\CBACT01C.json')); print('paragraph_count=', len(d['paragraph_data_flow'])); print('program_unresolved=', d['program_unresolved'])"
# -> paragraph_count=16
# -> program_unresolved=[]

python scripts\para_diff.py CBACT01C
# -> local=16  facts=16  (no delta)

python scripts\data_flow.py --all
# -> 31 files written
# -> 0 ERROR lines
# -> ZERO WARNINGs with local=0
# -> ZERO WARNINGs with local=1
# -> Allowed WARNINGs: COACTUPC, COACTVWC, COCRDLIC close-mismatch (deferred to 3.4)
```

---

## Section 3.2 Gate — CALL USING Classification

**Branch:** `feature/schema-v1.3-section3-call-using`

### Specification

**Mode-aware operand classification after `USING`:**

| Mode | Reads | Mutates |
|---|---|---|
| `BY REFERENCE` (default) | ✓ | ✓ |
| `BY CONTENT` | ✓ | ✗ |
| `BY VALUE` | ✓ | ✗ |
| `RETURNING` | ✗ | ✓ |

**Call graph emission:** Each program output must include a `call_graph` key:

```json
"call_graph": {
  "CBACT01C": ["COBDATFT"]
}
```

### Required tests

- `TestCallUsingByReference` — operand appears in both reads and mutates
- `TestCallUsingByContent` — operand appears in reads only
- `TestCallUsingByValue` — operand appears in reads only
- `TestCallReturning` — operand appears in mutates only
- `TestCallGraphCbact01c` — `CBACT01C.call_graph` contains `"COBDATFT"`

### 3.2 Gate criteria

```powershell
python tests\test_data_flow.py
# -> 42+ PASS (37 + 5 new CALL tests)

# CBACT01C 1300-POPUL-ACCT-RECORD unresolved == []
# CBACT01C.call_graph contains "COBDATFT"
# --all: zero local=0 WARNINGs, zero local=1 WARNINGs
# Only COACTUPC / COACTVWC / COCRDLIC close-mismatch WARNINGs allowed
```

### Frozen contracts (do NOT touch in 3.2)

`_normalise_source`, `_join_source_lines`, `extract_paragraphs`,
`_is_area_a_paragraph`, `_mask_literals`, `_dispatch_inline`

---

## Section 3.3 Gate — Missing Verb Handlers (planned)

**Branch:** `feature/schema-v1.3-section3-verbs`  
**Prerequisite:** 3.2 merged to main; rebase 3.3 onto post-3.2 main before merge.

### Specification

- Add handlers for: `INSPECT`, `SORT`, `MERGE`, `RELEASE`, `RETURN`
- After each handler: zero corpus lines for that verb may produce an
  unresolved entry with reason `UNKNOWN_VERB`

### Frozen contracts (do NOT touch in 3.3)

All contracts locked in 3.1 and 3.2.

---

## Section 3.4 Gate — Schema v1.3 + `section_name` (planned)

- `SCHEMA_VERSION` bumped to `"1.3"`
- `section_name` field added to each paragraph entry
- Close-mismatch WARNINGs resolved: COACTUPC, COACTVWC, COCRDLIC, COCRDSLC, COCRDUPC

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

- `_join_source_lines` — 4-digit prefix guard (Section 2 version, now superseded in Section 3.1)
- `extract_paragraphs` — procedure-division only, `_join_source_lines` then `_PARA_HEADER_RE`
- `_mask_literals` — equal-length underscore replacement of quoted strings
- `_dispatch_inline` — verb-splits on masked copy, slices parts from original text

---

## Section 3.1 Gate — Generalized Paragraph Detection

**Branch:** `feature/schema-v1.3-section3-paradetect`  
**Target merge:** `main` after all criteria below pass simultaneously

### SECTION header policy

**Decision: SECTION headers are NOT counted as paragraphs by the local extractor.**

Rationale:
- The CardDemo corpus does not use `PROCEDURE DIVISION SECTION` headers in any
  program with a 4-digit paragraph naming scheme.
- Programs that do use section headers (if any) would have their section names
  listed in `facts/PROGRAM.json` under a separate `sections_defined` key, not
  under `paragraphs_defined`.
- Counting section headers as paragraphs would inflate `local` counts and produce
  false-positive para_diff deltas.
- If a future program requires section-as-paragraph semantics, introduce a
  `count_sections_as_paragraphs: bool` flag in the extractor rather than changing
  the default policy.

Implementation: `_SECTION_HEADER_RE` matches `NAME SECTION.` or `NAME SECTION USING`.
Any line matching this pattern is excluded from paragraph detection in
`_is_area_a_paragraph()`.

### Division/section exclusion list (`_NOT_HEADER_KEYWORDS`)

The following tokens, when appearing as the first word of an Area-A line,
are structural COBOL keywords and never paragraph names:

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

After `_normalise_source` strips the 6-character sequence field and the
1-character indicator column, **column 8** of the original source lands at
`text[0]`. A line is a paragraph header if and only if ALL of the following
hold:

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

### 3.1 Gate criteria

```powershell
python tests\test_data_flow.py
# -> 23/23 PASS (18 Section 2 + 5 new Section 3.1 test classes)

python scripts\data_flow.py data\raw\cbl\CBACT01C.cbl > data\data_flow\CBACT01C.json
python -c "
import json; d=json.load(open(r'data\\data_flow\\CBACT01C.json'))
print('paragraph_count=', len(d['paragraph_data_flow']))
print('program_unresolved=', d['program_unresolved'])
"
# -> paragraph_count=16, program_unresolved=[]

python scripts\para_diff.py CBACT01C
# -> local=16 facts=16, no delta

python scripts\data_flow.py --all
# -> 31 files, 0 ERROR lines
# -> ZERO WARNINGs of the form: paragraph count mismatch: local=1 facts=N
# -> Close-mismatch WARNINGs (COACTUPC, COACTVWC, COCRDLIC etc.) MAY remain
#    and are deferred to Section 3.4
```

---

## Section 3.2 Gate — CALL USING Classification (planned)

- Mode-aware: BY REFERENCE → read+mutate; BY CONTENT/VALUE → read only; RETURNING → mutate only
- Emits `call_graph: { program → [called_programs] }` in output
- `CBACT01C` `1300_unresolved` becomes `[]`
- `CBACT01C.call_graph` includes `"COBDATFT"`

## Section 3.3 Gate — Missing Verb Handlers (planned)

- INSPECT, SORT, MERGE, RELEASE, RETURN
- After each handler: zero lines containing that verb in the corpus may produce
  an unresolved entry whose reason is `UNKNOWN_VERB`

## Section 3.4 Gate — Schema v1.3 + section_name (planned)

- `SCHEMA_VERSION` bumped to `"1.3"`
- `section_name` field added to paragraph entries
- Close-mismatch WARNINGs resolved (COACTUPC, COACTVWC, COCRDLIC, COCRDSLC, COCRDUPC)

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

## Section 3.2 Gate (FROZEN — commit `e9f68d3` on `feature/schema-v1.3-section3-call-using`; cherry-picked to `main` as `490443f`, 2026-05-10)

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

## Section 3.3 Gate (FROZEN — commit `165e9e8` on `feature/schema-v1.3-section3-verbs-rebased`; merged to `main` 2026-05-11)

**Branch (gated):** `feature/schema-v1.3-section3-verbs-rebased` at `165e9e8`
**Recovery anchor:** `feature/schema-v1.3-section3-verbs` at `0a69c0b` (preserved, do not delete)
**Prerequisite met:** 3.2 on `main` as `490443f`; rebase landed cleanly on top.

### Specification

- Handlers added for: `INSPECT`, `SORT`, `MERGE`, `RELEASE`, `RETURN`
- After each handler, zero corpus lines for that verb produce an unresolved
  entry with reason `UNKNOWN_VERB`.
- Previous TODO unresolved entries for these verbs are replaced with proper
  read/mutate classification.

### Frozen contracts (must NOT touch in 3.3 or later without re-gating)

- `_normalise_source`
- `_join_source_lines`
- `extract_paragraphs`
- `_is_area_a_paragraph`
- `_mask_literals`
- `_dispatch_inline`
- `_parse_call`

### 3.3 Gate criteria (FROZEN — 55/55 PASS on `165e9e8`)

```powershell
python tests\test_data_flow.py             # -> 55/55 PASS
python scripts\data_flow.py --all          # -> 31 files, 0 ERROR
                                           # -> ZERO local=0, ZERO local=1 WARNINGs
                                           # -> Allowed: COACTUPC/COACTVWC/COCRDLIC close-mismatch (3.4 bucket)
```

### 3.3 test inventory (locked)

- TestInspect: 2 (`test_inspect_replacing`, `test_inspect_tallying`)
- TestSort: 1 (`test_sort_using_giving`)
- TestMerge: 1 (`test_merge_using_giving`)
- TestRelease: 2 (`test_release_from`, `test_release_no_from`)
- TestReturn: 2 (`test_return_into`, `test_return_no_into`)
- New total: 8. Inherited from 3.2: 47. Grand total: **55**.

---

## Section 3.4 Gate — Schema v1.3 + `section_name` (SPEC LOCKED, not yet gated)

**Spec locked against baseline:** audit `audit/3_4_warning_baseline.json`, `main` SHA `77a5ca5`
**Branch (planned):** `feature/schema-v1.3-section4-schema-bump`
**Prerequisite:** 3.3 merged to `main`; baseline audit committed under `audit/`.

### Objective

1. Bump `SCHEMA_VERSION` from `"1.2"` to `"1.3"`.
2. Add `section_name` field to each paragraph entry in `paragraph_data_flow`.
3. Resolve all `close-mismatch` WARNINGs across the `--all` corpus, including
   defensive coverage of files that are clean today but share the same
   structural pattern.

### Target files (locked)

| File | Status today (`77a5ca5`) | Required after 3.4 |
|---|---|---|
| COACTUPC | close-mismatch local=85 facts=87 delta=-2 | local=87 facts=87 delta=0; no WARNING |
| COACTVWC | close-mismatch local=34 facts=36 delta=-2 | local=36 facts=36 delta=0; no WARNING |
| COCRDLIC | close-mismatch local=39 facts=41 delta=-2 | local=41 facts=41 delta=0; no WARNING |
| COCRDSLC | no WARNING (defensive scope) | no WARNING (regression guard) |
| COCRDUPC | no WARNING (defensive scope) | no WARNING (regression guard) |

### Implementation note (mechanism hint)

All three currently-warning files exhibit `local = facts - 2`. The −2 delta is
uniform across files, strongly suggesting a single shared structural cause:
implicit paragraph closure at SECTION boundaries that the current
paragraph-only counter does not see. The 3.4 fix should re-key
close-mismatch detection on the tuple `(section_name, paragraph_name)`
rather than `paragraph_name` alone. The introduction of `section_name`
in the schema and the resolution of these WARNINGs are therefore one
mechanism, not three.

### Frozen contract re-gating (REQUIRED)

`extract_paragraphs` is currently frozen by the 3.1, 3.2, and 3.3 gates.
Section 3.4 re-gates this contract to add section-aware annotation:
the walker MUST thread the most recently seen SECTION header through
the procedure division and stamp it onto every subsequent paragraph
entry until a new SECTION header is encountered. The previous contract
is superseded by 3.4. Document the new contract in the 3.4 FROZEN
block once gated; do not silently change it.

### Locked spec answers

1. **Paragraphs before any SECTION header.** `section_name` is the
   JSON value `null`. Not `""`, not a sentinel string. Tests must
   include at least one such fixture and assert `null`.
2. **SECTION-header detection regex.** Reuse `_SECTION_HEADER_RE`
   as locked in Section 3.1. No new regex. `_SECTION_HEADER_RE` is
   added to the frozen-contract enumeration as part of 3.4's lock.
3. **Backwards compatibility for v1.2 consumers.** No downgrade path.
   The `SCHEMA_VERSION` bump is the explicit signal; consumers MUST
   upgrade to v1.3 to read v1.3 output. No silent dual-version support.
4. **Frozen-contract update language.** The 3.4 FROZEN block (added
   when the gate closes) will state: "3.4 re-gates `extract_paragraphs`
   to add section-aware annotation; the previous contract is
   superseded." Do not leave the prior freeze in place without that
   supersession line.
5. **Section-aware deduplication.** Any logic in `data_flow_summary`
   that currently merges or dedups paragraph entries by name alone
   MUST become section-aware in 3.4. If no such logic exists today,
   document that explicitly in the 3.4 FROZEN block.

### 3.4 Gate criteria (to be marked FROZEN on the gating commit)

```powershell
python tests\test_data_flow.py
# -> NN/NN PASS (current 55 + new section-aware tests; count locked at gate close)
# Must include: paragraph-before-section (null), duplicate-paragraph-name-across-sections,
# section-header-immediately-followed-by-section-header, multi-paragraph-section.

python scripts\data_flow.py --all
# -> 31 files, 0 ERROR
# -> 0 close-mismatch WARNINGs
# -> 0 local=0, 0 local=1
# -> No deferral clause; the 3.1/3.2/3.3 "allowed COACTUPC/COACTVWC/COCRDLIC" exception
#    is REMOVED at 3.4 close.

python -c "import json; d=json.load(open(r'data\data_flow\COACTUPC.json')); \
           assert d['SCHEMA_VERSION']=='1.3'; \
           p=next(iter(d['paragraph_data_flow'].values())); \
           assert 'section_name' in p"
# -> all corpus JSON has SCHEMA_VERSION == '1.3' and section_name on every paragraph entry.
```

### Recovery anchors (planned)

- Before starting 3.4 implementation, tag `main` as `recovery-3.4-baseline` for
  rollback. Do not delete this tag until 3.4 is gated and merged.
- The 3.4 implementation branch MUST be cut from the tagged commit, not from
  a moving `main`.

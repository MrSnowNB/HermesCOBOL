# HermesCOBOL — Schema v1.2 / v1.3 Validation Gates

This document records the gated validation criteria for each section of
`scripts/data_flow.py`.  A section is **frozen** once all criteria in its
gate pass simultaneously.  No change to the script is permitted after a
section is gated without re-running the full gate for that section and all
previous sections.

---

## Section 2 Gate — FROZEN @ commit `f8d1eaf` / merge `609922d`

**Date:** 2026-05-08  
**Branch merged to `main`:** `feature/schema-v1.2-section2-dataflow`

### Passing criteria

| Criterion | Expected | Status |
|---|---|---|
| `python tests/test_data_flow.py` | 18/18 PASS | ✅ FROZEN |
| `CBACT01C` paragraph_count | 16 | ✅ FROZEN |
| `CBACT01C` para_diff | local=16 facts=16, no delta | ✅ FROZEN |
| `CBACT01C` 1300_unresolved | CALL 'COBDATFT' USING — accepted Section 3 TODO | ✅ FROZEN |
| `CBACT01C` 1350_unresolved | `[]` | ✅ FROZEN |
| `CBACT01C` program_unresolved | `[]` | ✅ FROZEN |
| `data_flow.py --all` | 31 files, 0 ERROR lines | ✅ FROZEN |

### Frozen contracts

- **`_join_source_lines`** — used 4-digit prefix guard (`^\d{4}-`) in
  Section 2; replaced by A-margin rule in Section 3.1 (see below).
- **`extract_paragraphs`** — PROCEDURE DIVISION gate: only lines after
  `PROCEDURE DIVISION` are candidates for paragraph headers.
- **`_mask_literals`** — equal-length underscore replacement before verb-split.
- **`_dispatch_inline`** — verb-splits on masked copy, slices from original.

---

## Section 3.1 Gate — Generalized Paragraph Detection

**Branch:** `feature/schema-v1.3-section3-paradetect`  
**Merges into:** `main` after all criteria below pass.

### Design decisions

#### A-margin rule (replaces 4-digit prefix guard)

COBOL fixed-format source: columns 1–6 are the sequence number, column 7
is the indicator.  After `_normalise_source` strips these, **column 8 is
index 0** of `text`.  A paragraph header **must** start in Area A
(columns 8–11), meaning `text[0] != ' '`.

A candidate line is treated as a new paragraph header only when ALL of:
1. `text[0] != ' '` — starts in Area A.
2. `_PARA_HEADER_RE` matches the stripped text (`WORD.` or `WORD SECTION.`).
3. The first word (before `SECTION`) is not in `_NOT_PARA`.

A line is fused as a continuation when the predecessor has no terminating
period AND the candidate fails the header test above.

#### SECTION header policy

**Decision:** A line of the form `LABEL SECTION.` inside the PROCEDURE
DIVISION is treated as a paragraph whose name is **LABEL** (the token
before the word `SECTION`).

**Rationale:**
- Facts files (`data/facts/<PROG>.json`) count SECTION labels in
  `paragraphs_defined` using only the label, not the full `LABEL SECTION`
  string.
- Treating the SECTION header as a named paragraph is consistent with how
  IBM COBOL and GnuCOBOL expose the symbol table: a SECTION name is a
  valid target for PERFORM and GO TO.
- The bare word `SECTION` is added to `_NOT_PARA` to prevent any line
  that contains only `SECTION.` from becoming a paragraph.

#### Pre-PROCEDURE DIVISION gate

The `in_procedure` flag in `extract_paragraphs` already ensures that no
line before `PROCEDURE DIVISION` is ever examined as a paragraph candidate.
Division/section keywords (`WORKING-STORAGE`, `IDENTIFICATION`, etc.) are
also added to `_NOT_PARA` as belt-and-suspenders.

### Passing criteria

| Criterion | Expected |
|---|---|
| `python tests/test_data_flow.py` | **23/23 PASS** (18 Section 2 + 5 new) |
| `CBACT01C` paragraph_count | 16 |
| `CBACT01C` para_diff | local=16 facts=16, no delta |
| `CBACT01C` 1350_unresolved | `[]` |
| `CBACT01C` program_unresolved | `[]` |
| `data_flow.py --all` | 31 files, 0 ERROR lines |
| `data_flow.py --all` WARNING pattern | **Zero** `local=1` WARNINGs |
| Close-mismatch WARNINGs | May remain (COACTUPC, COACTVWC, COCRDLIC, etc.) — deferred to Section 3.4 |

### Gate command sequence

```powershell
python tests\test_data_flow.py

python scripts\data_flow.py data\raw\cbl\CBACT01C.cbl > data\data_flow\CBACT01C.json
python -c "
import json
d = json.load(open(r'data\\data_flow\\CBACT01C.json'))
print('paragraph_count=', len(d['paragraph_data_flow']))
p = d['paragraph_data_flow'].get('1350-WRITE-ACCT-RECORD')
print('1350_unresolved=', p['unresolved'] if p else None)
print('program_unresolved=', d['program_unresolved'])
"

python scripts\para_diff.py CBACT01C

python scripts\data_flow.py --all
# Verify: no ERROR lines, no 'local=1' in WARNING lines
```

---

## Section 3.2 Gate — CALL USING Classification + call_graph

**Branch:** `feature/schema-v1.3-section3-call` (branches from 3.1 after gate)

### Design decisions

- `CALL 'PROG' USING arg...` operands are classified by mode:
  - Default mode after `USING`: **BY REFERENCE** → operand is both read and mutate.
  - `BY CONTENT` or `BY VALUE` → operand is read only.
  - `RETURNING identifier` → identifier is mutate only.
- A `call_graph` key is added to the program-level output:
  `{ "call_graph": { "PROGRAM": ["CALLED1", "CALLED2", ...] } }`

### Passing criteria (cumulative — includes all Section 3.1 criteria)

| Criterion | Expected |
|---|---|
| All Section 3.1 criteria | Pass |
| `CBACT01C` 1300_unresolved | `[]` |
| `CBACT01C` call_graph | includes `"COBDATFT"` |
| `TestCallUsing` | PASS |

---

## Section 3.3 Gate — Missing Verb Handlers

**Branch:** `feature/schema-v1.3-section3-verbs` (branches from 3.1, rebased onto post-3.2 main)

### Verbs covered

`INSPECT`, `SORT`, `MERGE`, `RELEASE`, `RETURN`

### Gate criterion (per-verb)

After a handler is added, **no line in the corpus containing that verb may
produce an unresolved entry whose reason contains `UNKNOWN_VERB`.**  Other
unresolved reasons (unresolved operand, TODO) are permitted.

---

## Section 3.4 Gate — Schema Bump + section_name

**Branch:** to be created from post-3.3 main

- `SCHEMA_VERSION` → `"1.3"`
- Each paragraph entry gains optional `section_name` field.
- Close-mismatch WARNINGs (COACTUPC 85 vs 87, COACTVWC 32 vs 36, etc.)
  are investigated and resolved or explicitly documented as COPY-boundary
  artifacts.

---

## Regression policy

Every PR that modifies `scripts/data_flow.py` or `tests/test_data_flow.py`
**must** include the full gate command sequence output in its PR description
before merge.  No exceptions.

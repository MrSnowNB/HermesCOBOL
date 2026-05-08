# HermesCOBOL v1.2 — Section 2 Kickoff
## Data Flow Extractor (`scripts/data_flow.py`)

---

## Objective

Build a deterministic per-paragraph `reads[]` / `mutates[]` extractor that runs over every
COBOL program and binds every identifier it sees back to the Section 1 byte layout, so we
can prove paragraph-level memory I/O with qualified names and exact offsets.

This is the prerequisite for:
- **T03 Data Flow validator** in Section 3 (is every verb in source represented in `reads[]`/`mutates[]`?).
- **Translation audit** downstream (does a Java/Python translation touch the same fields, in the same roles, at the same widths?).

---

## Scope (this PR only)

**In scope:**
- New file `scripts/data_flow.py`.
- New test file `tests/test_data_flow.py`.
- New artifact directory `data/data_flow/`.
- New gate section in `docs/V12_VALIDATION_GATES.md` → Section 2 Gate.
- Corpus run that produces `data/data_flow/<PROGRAM>.json` for the 31 programs.

**Out of scope (do not touch):**
- `scripts/extract_facts.py` (schema bump is Section 5).
- REKT adapter (Section 4).
- Any validator module (Section 3).
- `scripts/byte_layout.py` behavior.

---

## Dependency Contract (from Section 1)

`data_flow.py` must read `data/byte_layouts/<PROGRAM>.json` and use it as the resolver
for qualified names. Rule 9 (full ancestor path) is already in layout output, so
`data_flow.py` only needs to perform lookup, not re-resolution.

**Resolver requirements:**
- Build `qmap` at program load: `name → list[(record_name, qualified_name, copybook, offset, length)]`.
- Resolve references in paragraph body using the **nearest-enclosing group rule**: if `ACCT-ID`
  appears in a paragraph that already referenced `ACCOUNT-RECORD`, bind to `ACCOUNT-RECORD.ACCT-ID`.
- If a name is ambiguous and cannot be disambiguated, record it in `unresolved[]` with the
  paragraph and source line — **never silently drop or guess**.

---

## Output Contract

Write one JSON file per program at `data/data_flow/<PROGRAM>.json`:

```json
{
  "program": "CBACT01C",
  "schema_version": "1.2",
  "paragraph_data_flow": {
    "1300-POPUL-ACCT-RECORD": {
      "reads": [
        {"field": "WS-INPUT.WS-INPUT-ACCT-ID",
         "record": "WS-INPUT", "copybook": null,
         "offset": 0, "length": 11}
      ],
      "mutates": [
        {"field": "ACCOUNT-RECORD.ACCT-ID",
         "record": "ACCOUNT-RECORD", "copybook": "CVACT01Y",
         "offset": 0, "length": 11},
        {"field": "ACCOUNT-RECORD.ACCT-ACTIVE-STATUS",
         "record": "ACCOUNT-RECORD", "copybook": "CVACT01Y",
         "offset": 11, "length": 1}
      ],
      "unresolved": []
    }
  },
  "program_unresolved": []
}
```

Do **not** merge this into `data/facts/<PROGRAM>.json`. Schema bump and merge are Section 5's job.

---

## Verb Classifier (minimum required coverage)

The agent must deterministically classify at least these verbs. **Cite source line numbers**
for each entry so T03 can cross-reference statements. Treat verbs that aren't in this list
as no-ops, but still add the source line to `unresolved[]` if the verb is a known mutator
(`SET`, `CALL USING`, etc.) not yet implemented.

| Verb | reads | mutates |
|---|---|---|
| `MOVE src TO dst1 [dst2 ...]` | `src` | each `dst` |
| `MOVE CORRESPONDING group1 TO group2` | every matched leaf in `group1` | each counterpart in `group2` (use byte_layout metadata to enumerate leaves) |
| `ADD n [n2 ...] TO dst [dst2 ...]` | all sources and prior `dst` values | each `dst` |
| `ADD ... GIVING result` | all operands | `result` |
| `SUBTRACT`, `MULTIPLY`, `DIVIDE` | same convention as ADD (with GIVING form) | same |
| `COMPUTE dst = expr` | every identifier in `expr` | `dst` |
| `INITIALIZE dst1 dst2 ...` | — | each `dst` |
| `READ file [INTO dst]` | — | file-record and `dst` if present |
| `WRITE dst [FROM src]` | `src` if present | `dst` |
| `STRING s1 s2 ... INTO dst [WITH POINTER ptr]` | sources and `ptr` | `dst` and `ptr` |
| `UNSTRING src INTO dst1 dst2 ... [WITH POINTER ptr] [TALLYING t]` | `src`, `ptr` | each `dst`, `ptr`, `t` |
| `ACCEPT dst` | — | `dst` |
| `DISPLAY src ...` | each `src` | nothing |
| `IF <cond>` / `EVALUATE <expr>` / `WHEN` | each identifier in condition/expression (control-flow reads) | — |
| `PERFORM <para>` | not a data-flow event | ignore |
| `EXEC CICS ... END-EXEC` | operands of `FROM`, `INTO`, `LENGTH`, `RESP`, `RESP2` | same |
| `SET x TO TRUE/FALSE` | — | parent condition-name data item |
| `SET ptr TO address` | `address` | `ptr` |

Any statement whose verb is recognized but whose operands cannot be resolved via `qmap`
must be logged in the paragraph's `unresolved[]` with
`{verb, line_no, raw_text, reason}`. Never silently drop.

---

## Paragraph Boundary Rule

Paragraph boundaries are already computed in v1.1 facts. To keep Section 2 standalone:

- Re-derive paragraph boundaries **locally** in `data_flow.py` using the same regex the
  v1.1 extractor uses (copy, don't import, to keep the module decoupled for now).
- On any program where locally-derived paragraph count **disagrees** with
  `data/facts/<PROGRAM>.json.paragraphs_defined`, emit a one-line warning to `stderr`
  and record the mismatch in `program_unresolved[]`. Do **not** crash.

---

## Unit Tests (mandatory)

Create `tests/test_data_flow.py` with at least the following fixtures and assertions.
Keep them small, deterministic, and **independent of corpus data**.

| Test | What it asserts |
|---|---|
| `test_move_single_target` | `MOVE A TO B` → `reads=[A]`, `mutates=[B]` |
| `test_move_multiple_targets` | `MOVE A TO B C` → `reads=[A]`, `mutates=[B, C]` |
| `test_move_corresponding` | expand group leaves from byte_layout fixture |
| `test_add_to` | `ADD 1 TO CTR` → `reads=[CTR, <literal>]`, `mutates=[CTR]` |
| `test_add_giving` | `ADD A B GIVING C` → `reads=[A, B]`, `mutates=[C]` |
| `test_compute_expression` | `COMPUTE X = A + B * C` → `reads=[A, B, C]`, `mutates=[X]` |
| `test_initialize` | `INITIALIZE R` → `reads=[]`, `mutates=[R]` |
| `test_read_into` | `READ F INTO REC` → `reads=[]`, `mutates=[REC, <F-record>]` |
| `test_write_from` | `WRITE R FROM S` → `reads=[S]`, `mutates=[R]` |
| `test_if_condition_reads` | `IF A > B` adds `A` and `B` to `reads` |
| `test_unresolved_name` | dangling identifier lands in `unresolved[]` with line number |
| `test_qualified_name_disambiguation` | same unqualified name in two copybooks resolves to correct qualified form based on enclosing record context |

---

## CLI

`scripts/data_flow.py` must run in two modes:

**Single-program mode** (for the gate):
```powershell
python scripts\data_flow.py data\raw\cbl\CBACT01C.cbl > data\data_flow\CBACT01C.json
```

**Corpus mode** (for batch runs):
```powershell
python scripts\data_flow.py --all
```
which discovers programs from `data/raw/cbl/` and writes into `data/data_flow/`.

Both modes must be **idempotent** and must **never fail the whole batch** because a single
program has unresolved items. A program with unresolved entries still produces a valid JSON
file; the unresolved count is printed to `stderr`.

---

## Section 2 Gate

```powershell
# Section 2 — Data Flow Extractor Gate
# What this proves:
# 1) data_flow.py produces paragraph_data_flow for real programs
# 2) qmap lookup is resolving to ACCOUNT-RECORD fields from byte_layout
# 3) unresolved[] is low and explainable on target paragraphs

python scripts\data_flow.py data\raw\cbl\CBACT01C.cbl > data\data_flow\CBACT01C.json

python -c "
import json
d = json.load(open(r'data\\data_flow\\CBACT01C.json'))
print('program=',         d['program'])
print('paragraph_count=', len(d['paragraph_data_flow']))
print('sample_paragraphs=', list(d['paragraph_data_flow'])[:5])

p = d['paragraph_data_flow'].get('1300-POPUL-ACCT-RECORD')
print('1300_exists=', p is not None)
if p:
    print('1300_reads_count=',   len(p['reads']))
    print('1300_mutates_count=', len(p['mutates']))
    print('1300_first_mutate=',  p['mutates'][0] if p['mutates'] else None)
    print('1300_unresolved=',    p['unresolved'])

p = d['paragraph_data_flow'].get('1350-WRITE-ACCT-RECORD')
print('1350_exists=', p is not None)
if p:
    print('1350_reads=',      p['reads'])
    print('1350_mutates=',    p['mutates'])
    print('1350_unresolved=', p['unresolved'])

print('program_unresolved=', d['program_unresolved'])
"
```

### Expected gate output

- `paragraph_count` matches the v1.1 facts `paragraphs_defined` count for CBACT01C (±1 for synthetic end-markers).
- `1300-POPUL-ACCT-RECORD.mutates` contains at least one field qualified as `ACCOUNT-RECORD.*`
  with offsets matching the byte layout (`ACCT-ID` offset 0 length 11,
  `ACCT-ACTIVE-STATUS` offset 11 length 1, etc.).
- `1350-WRITE-ACCT-RECORD.reads` and `.mutates` both non-empty, with at least one entry
  bound to the file-record of `ACCTFILE`.
- `unresolved[]` on both paragraphs is empty (or contains only explicitly named,
  acceptable CICS operands — which CBACT01C should not hit).
- `program_unresolved=[]`.

---

## Definition of Done

Section 2 is **closed** only when all of the following are true and pasted back into the PR:

1. `python tests/test_data_flow.py` → all green.
2. Gate block above runs cleanly on `CBACT01C`.
3. At least one field in `1300-POPUL-ACCT-RECORD.mutates` is an `ACCOUNT-RECORD.*` entry
   with `offset` and `length` matching Section 1 output.
4. `program_unresolved[]` is empty on CBACT01C.
5. Corpus run (`python scripts/data_flow.py --all`) completes for the full set without
   crashing, and writes 31 files under `data/data_flow/`.
6. `docs/V12_VALIDATION_GATES.md` has a Section 2 subsection with the gate commands and
   expected output pasted verbatim.

---

## Explicit Non-Goals

- Do **not** compute T03 scores; that is Section 3.
- Do **not** modify `extract_facts.py` or bump `schema_version`.
- Do **not** attempt to trace control flow through PERFORM chains.
- Do **not** model CICS `LINK` or `XCTL` as data flow — those are control-flow edges
  (Section 4).
- Do **not** widen the verb classifier beyond the list above in this PR. If a verb is
  observed and unhandled, send it to `unresolved[]` and add a `TODO` comment for a
  follow-up PR.

---

## Suggested Branch + PR

Branch from current `feature/schema-v1.2-dataflow`:
```
feature/schema-v1.2-section2-dataflow
```

PR title: `v1.2 Section 2: data flow extractor (reads/mutates per paragraph)`

PR description must include:
- This kickoff document as committed text under `docs/V12_SECTION2_KICKOFF.md`.
- The exact gate block from this document.
- The pasted expected output.
- Merge conditional on sign-off after local gate re-run.

---

## Standing Rules (carried forward from Section 1)

- **Always read the source before writing a probe.** Gate probes must be grounded in what
  the COBOL actually contains, not spec assumptions.
- **Never push code to fix a failing test without first verifying the test is correct.**
- **`redefines_groups[]` is for sub-level REDEFINES only.** 01-level REDEFINES produce
  sibling record entries in the byte layout. Probes must not conflate the two.
- **Section 1 files are frozen.** Do not modify `scripts/byte_layout.py` or
  `tests/test_byte_layout.py` in this PR or any later PR.
- **Unresolved is better than wrong.** A field in `unresolved[]` with a reason is
  infinitely more useful than a silently incorrect binding in `reads[]` or `mutates[]`.

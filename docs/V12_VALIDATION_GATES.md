# HermesCOBOL v1.2 — Validation Gates

> **Process rule.** Every PR in the v1.2 chain must include one of the gate
> blocks below in its PR description. A section is not "done" until the
> expected output has been pasted back here (or into the PR comment thread)
> and jointly reviewed. "Implemented" never means "untested."

---

## Gate format

Every gate block follows this template:

```
Section N Gate

What this proves:
- ...

Run:
<exact command block>

Expected:
- ...
- ...

Paste back here:
- full console output
- 1–2 JSON snippets / grep results called out below
```

---

## Section 1 Gate — Byte Layout Extractor

### What this proves

1. `byte_layout.py` runs on real corpus programs without crashing.
2. DISPLAY / COMP-3 / REDEFINES / OCCURS logic produces visible, correct output.
3. Copybook expansion is working — imported records carry `copybook=<name>` on every field.
4. Unit tests pass (including the nested-OCCURS fixture).

### Run

```powershell
# --- unit tests (no corpus files required) ---
python tests\test_byte_layout.py

# --- corpus programs ---
python scripts\byte_layout.py data\raw\cbl\CBACT01C.cbl > data\byte_layouts\CBACT01C.json
python scripts\byte_layout.py data\raw\cbl\CBTRN02C.cbl > data\byte_layouts\CBTRN02C.json
python scripts\byte_layout.py data\raw\cbl\CBACT04C.cbl > data\byte_layouts\CBACT04C.json

# --- probe CBACT01C ---
python -c "
import json
d = json.load(open(r'data\byte_layouts\CBACT01C.json'))
print('program=',        d['program'])
print('records=',        len(d['records']))
print('unresolved=',     len(d['unresolved']))
r = next((x for x in d['records'] if x['name']=='ACCT-RECORD'), None)
print('acct_record_found=', r is not None)
print('acct_total_bytes=',  None if r is None else r['total_bytes'])
print('first_5_fields=',    [] if r is None else
      [(f['qualified_name'], f['offset'], f['length'], f['storage'])
       for f in r['fields'][:5]])
"

# --- probe CBTRN02C (REDEFINES exposure) ---
python -c "
import json
d = json.load(open(r'data\byte_layouts\CBTRN02C.json'))
print('program=',              d['program'])
print('records=',              len(d['records']))
print('unresolved=',           len(d['unresolved']))
print('redefines_groups_total=',
      sum(len(r.get('redefines_groups', [])) for r in d['records']))
"

# --- probe CBACT04C (OCCURS stress) ---
python -c "
import json
d = json.load(open(r'data\byte_layouts\CBACT04C.json'))
print('program=',    d['program'])
print('records=',    len(d['records']))
print('unresolved=', len(d['unresolved']))
occ = []
for r in d['records']:
    occ.extend([
        (r['name'], f['qualified_name'], f['offset'], f['length'], f['occurs'])
        for f in r['fields'] if (f.get('occurs') or 1) > 1
    ])
print('occurs_fields=', occ[:10])
"
```

### Expected

- Unit tests: `19 passed / 0 failed`.
- All three corpus commands complete without Python tracebacks.
- `CBACT01C.json`: `ACCT-RECORD` present, `acct_total_bytes` is a non-zero integer,
  `first_5_fields` shows real offsets starting at 0, `unresolved` is 0 (or low and
  explainable — e.g. an INSPECT verb edge case, not a missing copybook).
- `CBTRN02C.json`: `redefines_groups_total > 0` (source contains REDEFINES), or
  explicitly confirmed that none exist in that program.
- `CBACT04C.json`: `occurs_fields` is non-empty; at least one field shows `occurs > 1`
  with a plausible multiplied `length`.

### Paste back here

1. Full console output from the entire block above.
2. The complete `ACCT-RECORD` object from `data\byte_layouts\CBACT01C.json`.
3. One REDEFINES example from CBTRN02C (if present), or explicit note that none exist.
4. One OCCURS-related field or record snippet from CBACT04C.

---

## Section 2 Gate — Data Flow Extractor

### What this proves

1. `data_flow.py` resolves `reads[]` and `mutates[]` from real COBOL source.
2. The `qmap` lookup against Section 1 byte layouts is working — fields carry
   `offset` and `length` from the layout, not just name strings.
3. `unresolved[]` is not silently swallowing unmatched identifiers.

### Run

```powershell
python scripts\data_flow.py data\raw\cbl\CBACT01C.cbl > data\data_flow\CBACT01C.json

# --- probe paragraph 1300 ---
python -c "
import json
d = json.load(open(r'data\data_flow\CBACT01C.json'))
print('program=',       d['program'])
print('paragraphs=',    len(d['paragraph_data_flow']))
print('sample_names=',  list(d['paragraph_data_flow'])[:5])
p = d['paragraph_data_flow'].get('1300-POPUL-ACCT-RECORD')
print('1300_exists=',      p is not None)
print('1300_reads=',       [] if p is None else p['reads'])
print('1300_mutates=',     [] if p is None else p['mutates'])
print('1300_unresolved=',  [] if p is None else p['unresolved'])
"

# --- probe paragraph 1350 ---
python -c "
import json
d = json.load(open(r'data\data_flow\CBACT01C.json'))
p = d['paragraph_data_flow'].get('1350-WRITE-ACCT-RECORD')
print('1350_exists=',     p is not None)
print('1350_reads=',      [] if p is None else p['reads'])
print('1350_mutates=',    [] if p is None else p['mutates'])
print('1350_unresolved=', [] if p is None else p['unresolved'])
"

# --- check for ADD / COMPUTE read capture ---
python -c "
import json
d = json.load(open(r'data\data_flow\CBACT01C.json'))
add_paras = {
    k: v for k, v in d['paragraph_data_flow'].items()
    if any(r.get('verb') in ('ADD','COMPUTE','SUBTRACT','MULTIPLY','DIVIDE')
           for r in v.get('reads', []))
}
print('paragraphs_with_arithmetic_reads=', list(add_paras)[:5])
"
```

### Expected

- `data_flow\CBACT01C.json` written without error.
- `1300-POPUL-ACCT-RECORD` exists; `mutates[]` includes every `ACCT-RECORD.*` field
  present in the source MOVE chain.
- `1350-WRITE-ACCT-RECORD` exists; `reads[]` includes the source buffer,
  `mutates[]` includes the file/record target.
- At least one paragraph shows arithmetic verb reads, confirming ADD/COMPUTE capture.
- `unresolved[]` is empty on CBACT01C, or every entry is explicitly explainable.

### Paste back here

1. Full console output.
2. The `1300-POPUL-ACCT-RECORD` dict in full.
3. The `1350-WRITE-ACCT-RECORD` dict in full.
4. At least one arithmetic paragraph snippet (reads showing both operands).

---

## Section 3 Gate — T01–T05 Validators

### What this proves

1. All 31 programs produce a validator JSON without crashing.
2. COBSWAIT degrades gracefully: `T01.score = 0.0`, pipeline continues.
3. T03 is live and detecting real gaps — at least one program scores below 1.00.

### Run

```powershell
python scripts\validators\run_validators.py

# --- corpus-wide summary ---
python -c "
import json, glob, os
files = glob.glob(r'data\validators\*.json')
print('validator_files=', len(files))
lows = []
cobs = None
for fp in files:
    d    = json.load(open(fp))
    t05  = d.get('T05_functional_accuracy')
    t03  = (d.get('T03_data_flow') or {}).get('score')
    if t03 is not None and t03 < 1.0:
        lows.append((os.path.basename(fp), t03))
    if os.path.basename(fp).upper() == 'COBSWAIT.JSON':
        cobs = d
print('t03_below_1=',        sorted(lows)[:10])
print('cobswait_t01=',       None if cobs is None else cobs.get('T01_structural'))
print('cobswait_t05=',       None if cobs is None else cobs.get('T05_functional_accuracy'))
print('programs_below_0.90=',sum(1 for fp in files
    if (json.load(open(fp)).get('T05_functional_accuracy') or 1.0) < 0.90))
"

# --- spot-check CBACT01C validator JSON ---
python -c "
import json
d = json.load(open(r'data\validators\CBACT01C.json'))
print('program=',   d.get('program'))
print('T01=',       d.get('T01_structural'))
print('T02=',       d.get('T02_file_lineage'))
print('T03=',       d.get('T03_data_flow'))
print('T04=',       d.get('T04_cics'))
print('T05=',       d.get('T05_functional_accuracy'))
"
```

### Expected

- `validator_files = 31`.
- `programs_below_0.90 = 0` (all real programs pass the 0.90 floor except COBSWAIT).
- `t03_below_1` is non-empty — at least one entry, proving T03 is not a pass-through.
- `cobswait_t01.score = 0.0` with `missing: ["no_paragraphs"]`.
- `cobswait_t05 < 0.30` (COBSWAIT has no paragraphs so T01 weight alone drags it down).
- CBACT01C spot-check: `T01.score = 1.0`, `T02.score = 1.0`, `T05 >= 0.90`.

### Paste back here

1. Full console output from `run_validators.py`.
2. The corpus-wide summary printout in full.
3. The complete `COBSWAIT.json` validator object.
4. The complete `CBACT01C.json` validator object.

---

## Section 4 Gate — REKT Stage 2 Wiring

### What this proves

1. `extract_facts.py` still completes (no regression).
2. Non-CICS programs upgrade to `cfg_source=rekt` when `smojol-cli` is available.
3. Fallback to `text_scan` does not crash when REKT is unavailable — a single
   warning per program is emitted instead.
4. At least one non-CICS program exposes `conditional_true` / `conditional_false`
   edge types (REKT-only; impossible with text-scan).

### Run

```powershell
python scripts\extract_facts.py

# --- cfg_source distribution ---
python -c "
import json, glob, os
files = glob.glob(r'data\facts\*.json')
rekt   = [os.path.basename(f) for f in files
          if json.load(open(f)).get('control_flow', {}).get('cfg_source') == 'rekt']
tscan  = [os.path.basename(f) for f in files
          if json.load(open(f)).get('control_flow', {}).get('cfg_source') == 'text_scan']
print('cfg=rekt  count=', len(rekt),  rekt[:5])
print('cfg=tscan count=', len(tscan), tscan[:5])
"

# --- conditional edge check (REKT mode only) ---
python -c "
import json, glob, os
for fp in glob.glob(r'data\facts\*.json'):
    d     = json.load(open(fp))
    cf    = d.get('control_flow', {})
    if cf.get('cfg_source') != 'rekt':
        continue
    conds = [e for e in cf.get('edges', [])
             if e.get('type') in ('conditional_true', 'conditional_false')]
    if conds:
        print('program=', d.get('program_name', os.path.basename(fp)))
        print('conditional_edges_sample=', conds[:3])
        break
else:
    print('No rekt programs with conditional edges found (REKT not available — fallback mode active)')
"
```

### Expected (REKT available)

- `extract_facts.py` completes with `30 PASS / 1 WARN / 0 FAIL`.
- `cfg=rekt count = 14` (non-CICS programs).
- `cfg=tscan count = 17` (CICS programs, unchanged).
- At least one program shows `conditional_true` / `conditional_false` edges.

### Expected (REKT not available — fallback mode)

- `extract_facts.py` completes with `30 PASS / 1 WARN / 0 FAIL`.
- All programs remain `cfg=text_scan`.
- Console shows one `WARNING: smojol-cli not found` line per non-CICS program
  (or a single summary warning), no Python traceback.

### Paste back here

1. Final summary lines from `extract_facts.py` run.
2. The `cfg_source` distribution printout.
3. One non-CICS facts snippet showing `cfg_source` and (if REKT) edge count.
4. One conditional edge list snippet if REKT is available, or the fallback warning
   message if not.

---

## Section 5 Gate — Schema Bump + Wiring

### What this proves

1. `facts/*.json` files are now `schema_version: "1.2"`.
2. `byte_layout`, `data_flow`, and `validators` blocks are merged into every facts file.
3. Prior `30 PASS / 1 WARN / 0 FAIL` distribution is preserved.
4. COBSWAIT still degrades gracefully — `WARN no_paragraphs` with `T01.score = 0.0`.
5. At least one program shows `T05 < 1.0`, proving validators are active in the merged
   output (not stubbed as 1.0).

### Run

```powershell
python scripts\extract_facts.py

# --- schema shape check ---
python -c "
import json, glob, os
files = glob.glob(r'data\facts\*.json')
print('facts_files=', len(files))
s = json.load(open(files[0]))
print('sample_program=',    s.get('program_name', os.path.basename(files[0])))
print('schema_version=',    s.get('schema_version'))
print('has_byte_layout=',   'byte_layout' in s)
print('has_data_flow=',     'data_flow' in s)
print('has_validators=',    'validators' in s)
print('T05_in_sample=',     (s.get('validators') or {}).get('T05_functional_accuracy'))
"

# --- COBSWAIT regression check ---
python -c "
import json, glob, os
for fp in glob.glob(r'data\facts\*.json'):
    if 'COBSWAIT' in fp.upper():
        d = json.load(open(fp))
        print('schema_version=',  d.get('schema_version'))
        print('T01_score=',       (d.get('validators') or {}).get('T01_structural', {}).get('score'))
        print('T05=',             (d.get('validators') or {}).get('T05_functional_accuracy'))
        print('cfg_note=',        d.get('control_flow', {}).get('cfg_note'))
        break
"

# --- T05 distribution ---
python -c "
import json, glob
results = []
for fp in glob.glob(r'data\facts\*.json'):
    d   = json.load(open(fp))
    t05 = (d.get('validators') or {}).get('T05_functional_accuracy')
    results.append((d.get('program_name', fp), t05))
below = [(p, s) for p, s in results if s is not None and s < 1.0]
passing= sum(1 for _, s in results if s is not None and s >= 0.90)
print('programs_with_T05=',      len([r for r in results if r[1] is not None]))
print('T05_below_1.0=',          sorted(below)[:10])
print('T05_at_or_above_0.90=',   passing)
"
```

### Expected

- `extract_facts.py` output: `30 PASS / 1 WARN / 0 FAIL`.
- `facts_files = 31`.
- `schema_version = "1.2"` on every facts file.
- `has_byte_layout = True`, `has_data_flow = True`, `has_validators = True`.
- COBSWAIT: `T01_score = 0.0`, `T05 < 0.30`, `cfg_note` contains `structural_minimal`.
- `T05_below_1.0` non-empty — at least one program proving validators are active.
- `T05_at_or_above_0.90 >= 30` (all non-COBSWAIT programs).

### Paste back here

1. Full final summary from `extract_facts.py`.
2. The schema shape printout in full.
3. The COBSWAIT regression check printout.
4. The T05 distribution printout.
5. One complete merged facts snippet for CBACT01C showing all four top-level blocks
   (`byte_layout`, `data_flow`, `validators`, `control_flow`).

---

## Quick-reference checklist

| Section | Gate command | Key assertion |
|---|---|---|
| S1 | `python tests\test_byte_layout.py` + 3 corpus runs | `19 passed / 0 failed`; ACCT-RECORD offset 0 |
| S2 | `python scripts\data_flow.py CBACT01C.cbl` | `1300` mutates ACCT-RECORD.*; `unresolved=[]` |
| S3 | `python scripts\validators\run_validators.py` | 31 files; `t03_below_1` non-empty; COBSWAIT T01=0 |
| S4 | `python scripts\extract_facts.py` | 30 PASS / 1 WARN; 14 rekt or clean fallback |
| S5 | `python scripts\extract_facts.py` | `schema_version=1.2`; all blocks merged; T05 live |

---

## Governance

- This file is the **authoritative gate record** for v1.2.
- No PR merges without a gate-passing paste in the PR thread.
- If a gate expectation turns out to be wrong (e.g. CBACT01C has no ACCT-RECORD by
  that exact name), update this file in the same PR that discovered the discrepancy
  and note the reason.
- After Section 5 merges, this file is preserved as `docs/V12_VALIDATION_GATES.md`
  in `main` as a historical test record.

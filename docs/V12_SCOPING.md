# HermesCOBOL v1.2 Scoping Document
## Memory Parity, Data Flow, Validators, REKT Wiring, Conditional Edges

---

## Mission

v1.1 produced a deterministic structural substrate: paragraphs, control flow (PERFORM/GOTO/fallthrough/call), file verbs, CICS commands, maps, AID keys, screen_flow. v1.2 extends this substrate with the **data layer** and the **validation layer** so HermesCOBOL can answer 1:1 translation questions: which bytes of which copybook a paragraph reads or mutates, whether every source statement was accounted for, and a numeric functional-accuracy score per program.

---

## Branch + Schema Rules

- **Branch:** `feature/schema-v1.2-dataflow`. Do not touch `main` or `feature/schema-v1.1-semantics` except via PR after each section passes.
- Do not modify existing v1.1 fields. Only add new fields.
- Bump `schema_version` to `"1.2"` in `extract_facts.py` **only in Section 5** (the final section).
- No LLM calls in any v1.2 code. Pure deterministic Python 3.10+, standard library + existing `cobol-rekt` CLI only.

---

## Section Order + Context-Sized Chunking

Each section is a **separate PR** into `feature/schema-v1.2-dataflow`. Do not start Section N+1 until Section N is merged and its validation gate is green.

| # | Section | New file(s) |
|---|---|---|
| 1 | Byte Layout Extractor | `scripts/byte_layout.py`, `data/byte_layouts/` |
| 2 | Data Flow Extractor | `scripts/data_flow.py`, `data/data_flow/` |
| 3 | T01–T05 Validator Tier | `scripts/validators/`, `data/validators/` |
| 4 | REKT Stage 2 Wiring | `scripts/cfg_rekt_adapter.py` |
| 5 | Schema Bump + Wiring | `extract_facts.py` updated, `schema_version` → `"1.2"` |

This ordering is deliberate: layout is the prerequisite for data flow, data flow is the prerequisite for T03, and REKT wiring needs T04/T05 to be meaningful. Section 5 is the only one that touches the public contract.

---

## Section 1 — Byte Layout Extractor

### Goal

For each program, emit exact byte offsets, widths, storage class, SYNCHRONIZED slack, and REDEFINES overlays for every record. This is the prerequisite for all 1:1 translation claims.

Reference prior work: CardDemo `extract_byte_layout.py`. Port the core algorithm, simplified and commented.

### Output Artifact

Write one JSON file per program at `data/byte_layouts/<PROGRAM>.json`. Do not merge into `data/facts/*.json` in this section — that happens in Section 5.

Target shape:
```json
{
  "program": "CBACT01C",
  "schema_version": "1.2",
  "records": [
    {
      "name": "ACCT-RECORD",
      "copybook": "CVACT01Y",
      "total_bytes": 300,
      "fields": [
        {
          "qualified_name": "ACCT-RECORD.ACCT-ID",
          "level": 5,
          "offset": 0,
          "length": 11,
          "pic": "9(11)",
          "storage": "DISPLAY",
          "redefines": null,
          "synchronized": false
        },
        {
          "qualified_name": "ACCT-RECORD.ACCT-BAL",
          "level": 5,
          "offset": 12,
          "length": 8,
          "pic": "S9(10)V99",
          "storage": "COMP-3",
          "redefines": null,
          "synchronized": false
        }
      ],
      "redefines_groups": []
    }
  ],
  "unresolved": []
}
```

### Minimal Code Skeleton

```python
# scripts/byte_layout.py
"""
HermesCOBOL v1.2 — Byte Layout Extractor.

Emits exact byte offsets for every data item in every copybook used by a
program. This is the prerequisite for 1:1 translation validation.

Ported and simplified from CardDemo extract_byte_layout.py.
Deterministic. No LLM. Standard library only.
"""

from __future__ import annotations
import re, json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional

RE_LEVEL = re.compile(r'^\s*(\d{2})\s+([A-Z0-9][A-Z0-9\-]*)\b(.*)$', re.IGNORECASE)
RE_PIC   = re.compile(r'\bPIC(?:TURE)?\s+([^\s.]+)', re.IGNORECASE)
RE_COMP  = re.compile(r'\b(COMP-3|COMP-4|COMP-5|COMP|BINARY|PACKED-DECIMAL|DISPLAY)\b', re.IGNORECASE)
RE_REDEF = re.compile(r'\bREDEFINES\s+([A-Z0-9][A-Z0-9\-]*)', re.IGNORECASE)
RE_SYNC  = re.compile(r'\bSYNCHRONIZED\b|\bSYNC\b', re.IGNORECASE)
RE_OCCUR = re.compile(r'\bOCCURS\s+(\d+)', re.IGNORECASE)

@dataclass
class Field:
    qualified_name: str
    level: int
    offset: int
    length: int
    pic: Optional[str]
    storage: str
    redefines: Optional[str]
    synchronized: bool

def pic_length(pic: str, storage: str) -> int:
    """Compute byte length from PIC clause + storage class.
    Rules:
      DISPLAY: one byte per character in the PIC expansion.
      COMP-3 (PACKED-DECIMAL): ceil((digits + 1) / 2) bytes.
      COMP / BINARY: 2 bytes <=4 digits, 4 bytes 5-9 digits, 8 bytes 10-18 digits.
    """
    # ... implement deterministically, see CardDemo extract_byte_layout.py
    ...

def extract_layout(source: str, program: str) -> dict:
    """Walk 01-level records in WORKING-STORAGE and FILE SECTION, compute offsets."""
    # 1. strip fixed-format comments + continuation lines
    # 2. locate 01-level roots
    # 3. recursive walk producing (level, name, pic, storage, redefines, sync, occurs)
    # 4. offset = running cursor at current depth; reset on REDEFINES
    # 5. synchronized slack: align to 2/4/8-byte boundary based on COMP width
    # 6. return records[] shaped as above
    ...

if __name__ == "__main__":
    import sys
    src = Path(sys.argv[1]).read_text()
    out = extract_layout(src, Path(sys.argv[1]).stem)
    print(json.dumps(out, indent=2))
```

### Validation Gate for Section 1

```powershell
python scripts/byte_layout.py data\raw\cbl\CBACT01C.cbl > data\byte_layouts\CBACT01C.json
python scripts/byte_layout.py data\raw\cbl\CBTRN02C.cbl > data\byte_layouts\CBTRN02C.json
```

Hand-verify on CBACT01C:
- `ACCT-RECORD.ACCT-ID` has `offset: 0`, `length: 11`, `storage: "DISPLAY"`.
- A COMP-3 money field has the correct packed-decimal byte length.
- At least one record shows `redefines_groups` non-empty if REDEFINES appears in source.

Ship only when both programs produce byte layouts that match the source PIC clauses by hand.

---

## Section 2 — Data Flow Extractor

### Goal

For every paragraph, emit `reads[]` and `mutates[]` field references with qualified names, resolved against the byte layouts from Section 1.

Reference prior work: CardDemo `extract_paragraph_io.py`. Port the verb classifier + Rule 9 qualified-name resolver.

### Output Artifact

Write one JSON file per program at `data/data_flow/<PROGRAM>.json`. Do not merge into `data/facts/*.json` yet — that is Section 5.

Target shape:
```json
{
  "program": "CBACT01C",
  "schema_version": "1.2",
  "paragraph_data_flow": {
    "1300-POPUL-ACCT-RECORD": {
      "reads": [
        {"field": "WS-INPUT.WS-INPUT-ACCT-ID", "copybook": "CVACT01Y", "offset": 0, "length": 11}
      ],
      "mutates": [
        {"field": "ACCT-RECORD.ACCT-ID", "copybook": "CVACT01Y", "offset": 0, "length": 11},
        {"field": "ACCT-RECORD.ACCT-STATUS", "copybook": "CVACT01Y", "offset": 11, "length": 1}
      ],
      "unresolved": []
    }
  }
}
```

### Verb Classification

The classifier must, at minimum, resolve the following statements deterministically:

| Statement | reads | mutates |
|---|---|---|
| `MOVE src TO dst1 [dst2 ...]` | `src` | each `dst` |
| `ADD n TO dst`, `SUBTRACT n FROM dst`, `MULTIPLY … BY dst`, `DIVIDE … INTO dst` | all operands | target |
| `COMPUTE dst = expr` | every identifier in `expr` | `dst` |
| `INITIALIZE dst1 dst2 …` | — | each |
| `READ file INTO dst` | — | `dst` |
| `WRITE dst FROM src` | `src` | `dst` |
| `STRING … INTO dst`, `UNSTRING src INTO dst1 dst2` | sources | destinations |

Every resolution runs through a `qmap` built from Section 1's byte layouts. Unresolved references go into `unresolved[]` rather than silently dropped.

### Validation Gate for Section 2

```powershell
python scripts/data_flow.py data\raw\cbl\CBACT01C.cbl > data\data_flow\CBACT01C.json
```

Hand-verify three paragraphs in CBACT01C:
- `1300-POPUL-ACCT-RECORD`: `mutates[]` includes every `ACCT-RECORD.*` target present in the source MOVE chain.
- `1350-WRITE-ACCT-RECORD`: `mutates[]` includes the file record, `reads[]` includes the source buffer.
- A paragraph with an ADD or COMPUTE expression shows both operands in `reads[]`.

Confirm `unresolved[]` is empty on CBACT01C. Ship only then.

---

## Section 3 — T01–T05 Validator Tier

### Goal

Produce a numeric functional-accuracy score per program by running five deterministic gates against the facts + byte layout + data flow artifacts from Sections 1 and 2.

Reference prior work: CardDemo T-Series validators.

### Structure

```
scripts/validators/
  __init__.py
  t01_structural.py
  t02_file_lineage.py
  t03_data_flow.py
  t04_cics.py
  t05_functional_accuracy.py
  run_validators.py      # orchestrator
```

### Per-Tier Contract

Each tier exposes:

```python
def validate(program: str,
             source: str,
             facts: dict,
             layout: dict,
             flow: dict) -> dict:
    """
    Returns:
      {
        "tier": "T01",
        "score": 0.0..1.0,
        "expected": int,
        "covered": int,
        "missing": [str, ...]
      }
    """
```

### Tier Semantics

| Tier | Check | Weight in T05 |
|---|---|---|
| T01 Structural | Every paragraph in source appears in `facts.paragraphs_defined`; every CALL/PERFORM/GOTO target is resolved | 0.25 |
| T02 File lineage | Every `SELECT … ASSIGN TO …` pairs with an FD and a copybook; every OPEN/READ/WRITE/CLOSE references a known file | 0.15 |
| T03 Data flow | Every MOVE/ADD/COMPUTE/… in source has a corresponding `reads[]`/`mutates[]` record in flow | 0.30 |
| T04 CICS | Every `EXEC CICS` in source appears in `facts.cics.commands`; every `WHEN DFHxxx` under `EVALUATE EIBAID` appears in `facts.cics.aid_keys` | 0.30 |
| T05 Functional accuracy | Weighted rollup: `0.25*T01 + 0.15*T02 + 0.30*T03 + 0.30*T04` | — |

### Output Artifact

`data/validators/<PROGRAM>.json`:
```json
{
  "program": "CBACT01C",
  "schema_version": "1.2",
  "T01_structural":   {"score": 1.00, "expected": 16, "covered": 16, "missing": []},
  "T02_file_lineage": {"score": 1.00, "expected": 4,  "covered": 4,  "missing": []},
  "T03_data_flow":    {"score": 0.96, "expected": 85, "covered": 82, "missing": ["ADD at line 412"]},
  "T04_cics":         {"score": 1.00, "expected": 0,  "covered": 0,  "missing": []},
  "T05_functional_accuracy": 0.985
}
```

### Validation Gate for Section 3

```powershell
python scripts/validators/run_validators.py
```

Expected:
- 30 programs with `T05_functional_accuracy >= 0.90`.
- COBSWAIT reports `T01.score = 0.0` with `missing: ["no_paragraphs"]`, but pipeline does not crash.
- At least one program legitimately scores below 1.00 on T03 — that is evidence the tier is actually detecting something, not just a pass-through.

Ship only when all 31 programs produce a validator JSON without errors.

---

## Section 4 — REKT Stage 2 Wiring

### Goal

Upgrade `cfg_source` from `"text_scan"` to `"rekt"` on the 14 non-CICS programs, and introduce three new edge types that text-scan cannot resolve: `conditional_true`, `conditional_false`, `return`.

Reference prior work: CardDemo `extract_cfg_local.py` REKT adapter pattern.

### Structure

```python
# scripts/cfg_rekt_adapter.py
"""
HermesCOBOL v1.2 — REKT Stage 2 adapter.

Runs cobol-rekt smojol-cli on non-CICS programs and converts its output
into the v1.1 control_flow edge shape, adding three new edge types:
conditional_true, conditional_false, return.

For CICS programs, returns None so the text_scan CFG remains in place.
"""

from __future__ import annotations
import subprocess, json
from pathlib import Path

REKT_BIN = "smojol-cli"   # assume on PATH, or set via env var HERMES_REKT_BIN

def is_cics(source: str) -> bool:
    return "EXEC CICS" in source.upper()

def run_rekt(program_path: Path, report_dir: Path) -> dict | None:
    """Invoke smojol-cli against one COBOL file. Return parsed CFG dict or None."""
    # 1. skip if is_cics(source)
    # 2. subprocess.run([REKT_BIN, "cfg", "--src", str(program_path), "--out", str(report_dir)])
    # 3. parse report_dir / f"{program}_cfg.json"
    # 4. return adapted dict
    ...

def adapt_edges(rekt_cfg: dict) -> list[dict]:
    """Convert REKT edges into {from,to,type,source_lines} records.
    Supported edge types: perform, perform_thru, goto, call, fallthrough,
                          conditional_true, conditional_false, return."""
    ...
```

### Wiring into `hermes_v11_combined_extractor.enrich()`

In Section 11 of the combined extractor, add an env-gated path:

```python
rekt_cfg = run_rekt(program_path, Path("data/rekt_reports"))
if rekt_cfg is not None:
    control_flow = {
        "cfg_source": "rekt",
        "entry_points": rekt_cfg["entry_points"],
        "edges": adapt_edges(rekt_cfg),
        "unresolved": rekt_cfg.get("unresolved", []),
    }
else:
    control_flow = build_cfg_text_scan(...)  # existing v1.1 path
```

### Validation Gate for Section 4

```powershell
python scripts/extract_facts.py
```

Expected:
- 14 non-CICS programs report `cfg=rekt`.
- 17 CICS programs still report `cfg=text_scan` (unchanged).
- At least one non-CICS program (e.g., CBTRN02C) shows `conditional_true` and `conditional_false` edges in its `control_flow.edges[]`.
- No regressions in paragraph counts, file operations, or CICS subtree.
- If `smojol-cli` is not available locally, the adapter must fall back silently to `text_scan` and log a single warning per program, not crash.

---

## Section 5 — Schema Bump + extract_facts.py Wiring

### Goal

Merge byte layouts, data flow, and validator scores into the per-program `data/facts/<PROGRAM>.json` files and bump the schema version to `1.2`.

### Changes to `extract_facts.py`

After `enrich()` runs, load the artifacts from Sections 1–3 and merge:

```python
facts["schema_version"] = "1.2"
facts["byte_layout"]    = load_or_none("data/byte_layouts", program)
facts["data_flow"]      = load_or_none("data/data_flow",    program)
facts["validators"]     = load_or_none("data/validators",   program)
```

Update the console summary line to include T05:

```
[PASS] CBACT01C   cics=- sql=- paras=16 calls=2 files=4 edges=45 cfg=rekt  T05=0.985
```

### Validation Gate for Section 5

```powershell
python scripts/extract_facts.py
```

Expected:
- `30 PASS / 1 WARN / 0 FAIL` preserved.
- Every facts JSON contains `schema_version: "1.2"`, `byte_layout`, `data_flow`, and `validators` blocks.
- COBSWAIT still `WARN no_paragraphs`, with `T01.score = 0.0` and `cfg_note = "structural_minimal: no paragraphs detected"`.
- At least one program shows `T05 < 1.0` to prove the validators are active.

Ship only when all five gates are green.

---

## Deliverable Checklist for Cloud Agent

Open five sequential PRs into `feature/schema-v1.2-dataflow`:

1. **PR "v1.2 Section 1: byte layout extractor"** — adds `scripts/byte_layout.py` + `data/byte_layouts/`.
2. **PR "v1.2 Section 2: data flow extractor"** — adds `scripts/data_flow.py` + `data/data_flow/`.
3. **PR "v1.2 Section 3: T01–T05 validators"** — adds `scripts/validators/` + `data/validators/`.
4. **PR "v1.2 Section 4: REKT stage 2 adapter"** — adds `scripts/cfg_rekt_adapter.py`, wires into combined extractor.
5. **PR "v1.2 Section 5: schema bump + wiring"** — bumps `schema_version` to `"1.2"`, merges artifacts into facts.

Each PR must include:
- Code with docstrings and inline comments for every non-obvious regex or heuristic.
- The validation gate command + expected output pasted into the PR description.
- No modifications to files outside its section's scope.

After PR 5 merges, open **PR "v1.2 merge into main"** from `feature/schema-v1.2-dataflow` into `main`.

---

## Dependency Graph

```
Section 1 (byte_layout)
    └── Section 2 (data_flow)  [requires qmap from S1]
            └── Section 3 (validators T03)  [requires flow from S2]
Section 3 (validators T04)  [requires cics.aid_keys from v1.1]
Section 4 (REKT wiring)     [standalone; fallback to text_scan if smojol-cli absent]
Section 5 (schema bump)     [requires S1+S2+S3+S4 artifacts on disk]
```

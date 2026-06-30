# HermesCOBOL Manual Runbook

Manual, step-by-step local operation of the deterministic COBOL extraction and knowledge-ingestion pipeline.

---

## Scope

This pipeline produces structured canonical IR from raw COBOL source and loads
it into Honcho v3 as a persistent, queryable knowledge base. No automation runs
the whole pipeline. No LLMs. Each stage is run manually.

```
raw COBOL  →  Python extraction  →  data/canonical/  →  Honcho v3
```

> **COBOL-REKT / smojol:** Not part of this pipeline. These tools were consulted early
> to learn structural patterns. All extraction uses the custom Python scripts in `scripts/`.

---

## Raw-data-only policy

This repo contains **only raw mainframe-style source files**:
- COBOL programs (`data/raw/cbl/`)
- Non-BMS copybooks (`data/raw/cpy/`)
- BMS map copybooks (`data/raw/cpy-bms/`)

**Do NOT add to this repo:**
- Stub copybooks (e.g. `DFHAID.cpy` with synthetic content)
- Translator shims or generated wrappers
- Processed or generated artifacts of any kind
- Server, harness, or agent code

---

## Prerequisites

| Tool | Version | Required? | Check |
|---|---|---|---|
| Python | 3.10+ | **Required** | `python --version` |
| Honcho v3 | latest | **Required** for Phases 5–8 | `http://localhost:18000` |
| GnuCOBOL | 3.2+ | **Optional** (Mode A validation only) | `cobc --version` |

> **GnuCOBOL note:** Only needed if you want to run Mode A preprocess hash verification
> on the ~14 non-CICS programs. The extraction pipeline (Phases 1–4) is pure Python
> and has no GnuCOBOL dependency. If `cobc` is not installed, Mode A is skipped with
> a clear message; all other pipeline functions work normally.

---

## Stage 0 — Populate raw inputs

### Step 0a. Place COBOL programs
```powershell
Copy-Item C:\work\aws-mainframe-modernization-carddemo\app\cbl\*.cbl `
          data\raw\cbl\
```

### Step 0b. Place non-BMS copybooks
```powershell
Copy-Item C:\work\aws-mainframe-modernization-carddemo\app\cpy\*.cpy `
          data\raw\cpy\
```

### Step 0c. Place BMS map copybooks
```powershell
Copy-Item C:\work\aws-mainframe-modernization-carddemo\app\cpy-bms\*.cpy `
          data\raw\cpy-bms\
# or:
Copy-Item C:\work\aws-mainframe-modernization-carddemo\app\bms\*.cpy `
          data\raw\cpy-bms\
```

**Note:** BMS map copybooks include screen layout DSECTs such as `COACTUP`, `COACTVW`,
`COBIL00`, etc. These are standard mainframe copybooks — do NOT replace them with stubs.

---

## Stage 1 — Python fact extraction

Text-scan only — does NOT invoke `cobc`. Reads raw `.cbl` files directly.

```powershell
# All programs:
python scripts\extract_facts.py

# Single program:
python scripts\extract_facts.py CBACT01C
```

Outputs go to `data/facts/<PROG>.json` (gitignored, local only).

**Expected output:**
```
  [PASS] CBACT01C               cics=- sql=-  paras= 21  calls= 2  files= 4
  [WARN] COBSWAIT               cics=- sql=-  paras=  0  calls= 1  files= 0
           reasons: ['no_paragraphs']
```

`WARN` with `no_paragraphs` indicates a very short utility or stub program — expected for COBSWAIT.

---

## Stage 2 — Validate facts schema

```powershell
python scripts\schema.py
```

All programs should show `OK   v1.0`. Any `FAIL` indicates stale or incorrect facts —
re-run `extract_facts.py`.

---

## Stage 3 — Run primary extractor

```powershell
# All programs:
python scripts\hermes_v11_combined_extractor.py --all

# Single program:
python scripts\hermes_v11_combined_extractor.py CBACT01C
```

Outputs paragraph-level IR consumed by `assemble_canonical.py`.

---

## Stage 4 — Build byte layout, CFG, fallthrough, data flow

Run each extractor in order:

```powershell
# Byte layout
python scripts\byte_layout.py --all

# CFG (local per-program)
python scripts\extract_cfg_local.py --all

# CFG summary (cross-program rollup)
python scripts\extract_cfg_summary.py

# Fall-through edge detection
python scripts\extract_fallthrough.py --all

# Data flow
python scripts\data_flow.py --all
```

All outputs go to their respective `data\<type>\` directories (gitignored, local only).

---

## Stage 5 — Assemble canonical IR

```powershell
python scripts\assemble_canonical.py --all
```

Merges all extractor outputs into `data\canonical\<PROG>.canonical.json` for all 31 programs.

---

## Stage 6 — Round-trip validation

```powershell
# All programs:
python scripts\validate_roundtrip.py

# Single program:
python scripts\validate_roundtrip.py CBACT01C
```

This is the **primary domain gate**. See [docs/validation-runbook.md](validation-runbook.md)
for full output interpretation.

**Expected result:** 31 PASS, 0 FAIL, 17 skipped (CICS, Mode A only).

---

## Stage 7 — Load corpus into Honcho

Ensure Honcho v3 is running at `http://localhost:18000` before this step.

```powershell
# Full corpus load (all 31 programs)
python scripts\load_corpus.py --run
```

Expected: ~21 minutes, 31 programs, zero failures.

To verify after loading:
```powershell
python scripts\honcho_loader.py --list
python scripts\honcho_loader.py --verify COACTUPC
```

---

## Stage 8 — Smoke-test CobolWalker

```powershell
python -c "from scripts.cobol_walker import CobolWalker; from scripts.cobol_program_dict import CobolProgramDict; w = CobolWalker(CobolProgramDict('CBACT01C')); print(list(w.walk()))"
```

Run walker audit across all 31 programs:
```powershell
python scripts\audit_cobol_walker.py
```

Expected baseline sums: **live=205, full=518** across 31 programs.

---

## CICS programs — preprocess intentionally skipped

Programs containing `EXEC CICS` (e.g. `COACTUPC`, `COBIL00C`, `COCRDLIC`, etc.)
require the IBM CICS translator as a pre-step before `cobc -E`. That translator
is not available in this repo.

- The round-trip validator marks these as `preprocess_skipped=true`,
  `preprocess_skipped_reason="cics_no_translator"`.
- This is **not a failure** — it is an expected, documented skip.
- Mode B (structural coverage) still runs for CICS programs.
- All 17 CICS programs pass Mode B and are counted in the 31 PASS total.

---

## What is NOT committed

- No preprocessed COBOL output
- No facts JSON, canonical IR JSON, byte layout JSON, CFG JSON, data flow JSON
- No markdown pipeline outputs
- No generated artifacts of any kind

All generated artifacts live under `data/` subdirectories and `validation/` —
gitignored, produced locally only.

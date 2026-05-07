# HermesCOBOL Manual Runbook

Manual, step-by-step local operation of the deterministic COBOL evidence pipeline.

---

## Scope

This pipeline stops at data artifacts. No automation runs the whole pipeline.
No LLMs. No server. No harness. Each stage is run manually.

```
raw COBOL  ->  cobc -E  ->  COBOL-REKT  ->  Python extraction  ->  data/facts/
```

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

| Tool | Version | Check |
|---|---|---|
| Python | 3.10+ | `python --version` |
| GnuCOBOL | 3.2+ | `cobc --version` |
| COBOL-REKT (smojol-cli) | latest | `java -jar smojol-cli.jar --version` |

---

## Stage 0 — Populate raw inputs

### Step 0a. Place COBOL programs
```powershell
# Copy all .cbl files from your CardDemo source
Copy-Item C:\work\aws-mainframe-modernization-carddemo\app\cbl\*.cbl `
          data\raw\cbl\
```

### Step 0b. Place non-BMS copybooks
```powershell
# Copy standard data copybooks
Copy-Item C:\work\aws-mainframe-modernization-carddemo\app\cpy\*.cpy `
          data\raw\cpy\
```

### Step 0c. Place BMS map copybooks
```powershell
# Copy BMS-generated screen map copybooks (DSECT output from BMS assembly)
# These typically live in app/cpy-bms/ or app/bms/ depending on your CardDemo clone
Copy-Item C:\work\aws-mainframe-modernization-carddemo\app\cpy-bms\*.cpy `
          data\raw\cpy-bms\
# or:
Copy-Item C:\work\aws-mainframe-modernization-carddemo\app\bms\*.cpy `
          data\raw\cpy-bms\
```

**Note:** BMS map copybooks include screen layout DSECTs such as `COACTUP`,
`COACTVW`, `COBIL00`, etc. These are standard mainframe copybooks
— do NOT replace them with stubs.

---

## Stage 1 — Preprocess with cobc -E (non-CICS programs only)

GnuCOBOL cannot preprocess raw `EXEC CICS ... END-EXEC` blocks without a
CICS translator. This is **by design** — see the CICS note below.

```powershell
# From repo root. Replace CBACT01C with each non-CICS program name.
cobc -E `
  -I data\raw\cpy `
  -I data\raw\cpy-bms `
  -ext cpy -ext CPY -ext "" `
  data\raw\cbl\CBACT01C.cbl > data\preprocessed\CBACT01C.pre.cbl
```

Save outputs to `data/preprocessed/` (gitignored, local only).

### CICS programs — preprocess intentionally skipped

Programs containing `EXEC CICS` (e.g. `COACTUPC`, `COBIL00C`, `COCRDLIC`, etc.)
require the IBM CICS translator as a pre-step before `cobc -E`. That translator
is not available in this repo.

- The round-trip validator marks these programs as
  `preprocess_skipped = true`, `preprocess_skipped_reason = "cics_no_translator"`.
- This is **not a failure** — it is an expected, documented skip.
- Mode B (structural coverage) still runs for CICS programs.
- Full CICS preprocessing belongs in a separate pipeline layer.

---

## Stage 2 — COBOL-REKT CFG analysis

Run smojol-cli manually against each preprocessed `.cbl` file.

```powershell
# Example (adjust jar path and options to your smojol-cli version)
java -jar smojol-cli.jar `
  --program data\preprocessed\CBACT01C.pre.cbl `
  --copybook-dir data\raw\cpy `
  --output data\rekt\CBACT01C.cbl.report
```

Save outputs to `data/rekt/` (gitignored, local only).

---

## Stage 3 — Python fact extraction

Text-scan only — does NOT invoke cobc. Reads raw `.cbl` files directly.

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

`WARN` with `no_paragraphs` indicates a very short utility or stub program.
Investigate manually before proceeding.

---

## Stage 4 — Validate facts schema

```powershell
python scripts\schema.py
```

All programs should show `OK   v1.0`. Any `FAIL` indicates stale or
incorrect facts — re-run `extract_facts.py`.

---

## Stage 5 — Round-trip validator

```powershell
# All programs:
python scripts\validate_roundtrip.py

# Single program:
python scripts\validate_roundtrip.py CBACT01C
```

### Expected output pattern
```
  [PASS] CBACT01C               preprocess=OK                    -
  [PASS] COACTUPC               SKIP(cics_no_translator)         -  [cics_structural_only]
  [FAIL] CBACT01C               preprocess=OK                    missing_paragraphs
```

### Output locations
```
validation/
  reconstructed/cbl/<PROG>.pre.cbl    # cobc -E output (non-CICS only)
  reports/<PROG>.validation.json      # per-program report
  reports/summary.json                # aggregate
```

### Interpreting preprocess_skipped in reports

In `validation/reports/<PROG>.validation.json`:
```json
{
  "preprocess_skipped": true,
  "preprocess_skipped_reason": "cics_no_translator",
  "gate_note": "cics_structural_only",
  "gate_status": "PASS"
}
```
This means: Mode A was intentionally skipped (CICS program, no translator).
Mode B structural coverage ran and passed. Gate = PASS.

### Interpreting summary.json
```json
{
  "programs_total": 31,
  "programs_pass": 31,
  "programs_fail": 0,
  "programs_skipped_preprocess": 16,
  "skipped_reasons": {"cics_no_translator": 16}
}
```

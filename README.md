# HermesCOBOL

**Manual deterministic COBOL preprocessing and evidence extraction substrate.**

This repo is NOT a finished application, NOT a server, and NOT an automated harness.
It is a clean, manual-first pipeline for stepping through:

```
raw COBOL  ->  cobc -E  ->  COBOL-REKT  ->  Python extraction  ->  data/facts/
```

The pipeline stops at data artifacts. No LLM integration, no server, no agent runtime.
Hermes/harness/agent integration happens later in a separate layer.

---

## Raw-data-only policy

HermesCOBOL contains **only raw mainframe-style source files**:

- COBOL programs (`data/raw/cbl/`)
- Non-BMS copybooks (`data/raw/cpy/`)
- BMS map copybooks (`data/raw/cpy-bms/`)

**Not in this repo:**
- Stub or synthetic copybooks
- Translators or generated shims
- Processed / generated artifacts of any kind
- Server, harness, Docker, CI, or agent code

CICS preprocessing is **intentionally not supported** in this repo.
GnuCOBOL cannot preprocess raw `EXEC CICS` blocks without the IBM CICS
translator. CICS programs are marked `preprocess_skipped` in validator
reports — this is by design, not a failure.

Hermes harness work happens in a **separate layer** that consumes the
deterministic artifacts produced locally by running this pipeline.

---

## Scope

| In scope | Out of scope |
|---|---|
| Raw `.cbl` source files | Processed / generated artifacts |
| Raw `.cpy` copybooks | FastAPI / uvicorn server |
| Raw BMS `.cpy` map copybooks | Ollama / LLM integration |
| Fixed Python extraction scripts | GitHub Actions / Docker |
| Schema definitions | Agent harness code |
| Deterministic round-trip validator | CICS translator / stubs |
| Manual runbook | Automated pipeline runners |

---

## Prerequisites

- Python 3.10+
- [GnuCOBOL 3.2+](https://gnucobol.sourceforge.io/) (`cobc` on PATH)
- [COBOL-REKT (smojol-cli)](https://github.com/avishek-sen-gupta/cobol-rekt) (Java, run manually)
- `pip install -r requirements.txt`

---

## Quick orientation

```
HermesCOBOL/
  data/raw/cbl/           <- raw COBOL .cbl source files (committed)
  data/raw/cpy/           <- raw non-BMS copybooks (committed)
  data/raw/cpy-bms/       <- raw BMS map copybooks (committed, user-populated)
  scripts/                <- Python extraction + validation (run manually)
  validation/             <- validator outputs (gitignored, local only)
  docs/manual-runbook.md      <- step-by-step local operation guide
  docs/validation-runbook.md  <- round-trip validator guide
```

See [docs/manual-runbook.md](docs/manual-runbook.md) for the full pipeline.
See [docs/validation-runbook.md](docs/validation-runbook.md) for the validator.

---

## Round-Trip Validation (manual, deterministic)

- **Mode A (preprocess):** Runs `cobc -E -I cpy -I cpy-bms` on each non-CICS `.cbl`.
  SHA-256 hashes both raw and preprocessed outputs. Pins GnuCOBOL version.
  CICS programs are skipped with reason `cics_no_translator` — not failed.
- **Mode B (structural coverage):** Independently scans each `.cbl` for paragraphs,
  01-level items, CALL targets, SELECT/ASSIGN definitions, EXEC CICS/SQL presence.
  Compares against `data/facts/<PROG>.json`. Runs for ALL programs.

**Reports go to:** `validation/reports/` (gitignored, local only)

```bash
python scripts/validate_roundtrip.py             # all programs
python scripts/validate_roundtrip.py CBACT01C    # single program
```

Exit code `0` = all PASS. Exit code `1` = one or more FAIL.

**No LLMs. No server. No automation. No stubs.**

---

## What is NOT committed

- No preprocessed COBOL output
- No REKT CFG JSON reports
- No facts JSON
- No markdown pipeline outputs
- No generated artifacts of any kind
- No stubs, translators, or synthetic copybooks

All generated artifacts live under `data/preprocessed/`, `data/rekt/`,
`data/facts/`, and `validation/` — gitignored, produced locally only.

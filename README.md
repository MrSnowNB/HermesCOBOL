# HermesCOBOL

**Manual deterministic COBOL preprocessing and evidence extraction substrate.**

This repo is NOT a finished application, NOT a server, and NOT an automated harness.
It is a clean, manual-first pipeline for stepping through:

```
raw COBOL  ->  cobc -E  ->  COBOL-REKT  ->  Python extraction  ->  data/facts/
```

The pipeline stops at data artifacts. No LLM integration, no server, no agent runtime.
Hermes/harness/agent integration happens later in a separate layer.

## Scope

| In scope | Out of scope |
|---|---|
| Raw `.cbl` source files | Processed / generated artifacts |
| Raw `.cpy` copybooks | FastAPI / uvicorn server |
| Fixed Python extraction scripts | Ollama / LLM integration |
| Manual runbook | GitHub Actions / Docker |
| Schema definitions | Agent harness code |
| Deterministic round-trip validator | Automated pipeline runners |

## Prerequisites

- Python 3.10+
- [GnuCOBOL 3.2+](https://gnucobol.sourceforge.io/) (`cobc` on PATH)
- [COBOL-REKT (smojol-cli)](https://github.com/avishek-sen-gupta/cobol-rekt) (Java, run manually)
- `pip install -r requirements.txt`

## Quick orientation

```
HermesCOBOL/
  data/raw/cbl/           <- raw COBOL .cbl source files (committed)
  data/raw/cpy/           <- raw copybook .cpy files (committed)
  scripts/                <- Python extraction + validation scripts (run manually)
  validation/             <- validator outputs (gitignored, local only)
  docs/manual-runbook.md  <- step-by-step local operation guide
  docs/validation-runbook.md  <- round-trip validator guide
```

See [docs/manual-runbook.md](docs/manual-runbook.md) for the full extraction pipeline.
See [docs/validation-runbook.md](docs/validation-runbook.md) for the validator.

## Round-Trip Validation (manual, deterministic)

The validator proves every step of the pipeline is covered and reversible:

- **Mode A (preprocess):** Runs `cobc -E` on each raw `.cbl` and SHA-256 hashes
  both raw and preprocessed outputs (LF-normalized). Pins GnuCOBOL version.
- **Mode B (structural coverage):** Independently scans each `.cbl` for paragraphs,
  01-level items, CALL targets, SELECT/ASSIGN definitions, EXEC CICS/SQL presence.
  Compares against `data/facts/<PROG>.json` and reports any gaps.

**Reports go to:** `validation/reports/` (gitignored, local only)

```bash
# Run against all programs:
python scripts/validate_roundtrip.py

# Run against a single program:
python scripts/validate_roundtrip.py CBACT01C
```

Exit code `0` = all PASS. Exit code `1` = one or more FAIL.

See [docs/validation-runbook.md](docs/validation-runbook.md) for full details.

**No LLMs. No server. No automation. Read-only against `data/raw/` and `data/facts/`.**

## What is NOT in this repo

- No preprocessed COBOL output
- No REKT CFG JSON reports
- No facts JSON
- No markdown pipeline outputs
- No generated artifacts of any kind
- No server, no CLI launcher, no automation

All generated artifacts live under `data/preprocessed/`, `data/rekt/`, `data/facts/`,
and `validation/` — these directories are gitignored and must be produced locally
by running each stage manually.

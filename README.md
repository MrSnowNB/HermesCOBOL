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

## Prerequisites

- Python 3.10+
- [GnuCOBOL 3.2+](https://gnucobol.sourceforge.io/) (`cobc` on PATH)
- [COBOL-REKT (smojol-cli)](https://github.com/avishek-sen-gupta/cobol-rekt) (Java, run manually)
- `pip install -r requirements.txt`

## Quick orientation

```
HermesCOBOL/
  data/raw/cbl/       <- raw COBOL .cbl source files (committed)
  data/raw/cpy/       <- raw copybook .cpy files (committed)
  scripts/            <- Python extraction scripts (run manually)
  docs/manual-runbook.md  <- step-by-step local operation guide
```

See [docs/manual-runbook.md](docs/manual-runbook.md) for the full step-by-step process.

## What is NOT in this repo

- No preprocessed COBOL output
- No REKT CFG JSON reports
- No facts JSON
- No markdown pipeline outputs
- No generated artifacts of any kind
- No server, no CLI launcher, no automation

All generated artifacts live under `data/preprocessed/`, `data/rekt/`, and `data/facts/` —
these directories are gitignored and must be produced locally by running each stage manually.

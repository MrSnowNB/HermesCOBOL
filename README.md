# HermesCOBOL

**Deterministic COBOL extraction and knowledge-ingestion pipeline for the IBM CardDemo corpus.**

This repo contains a fully custom Python extraction stack that parses 31 COBOL programs,
produces structured canonical IR, and loads the results into a Honcho v3 memory server
for AI-assisted translation by the Hermes agent.

```
data/raw/cbl/  →  custom Python extractors  →  data/canonical/  →  Honcho v3 RAM
```

The pipeline is **pure Python**. There is no dependency on COBOL-REKT, smojol, or any
external Java tooling. GnuCOBOL (`cobc`) is an **optional validation aid** only — see
the Prerequisites section for details.

---

## Honcho-as-RAM Architecture

HermesCOBOL uses [Honcho](https://github.com/plastic-labs/honcho) as a
persistent memory store for the full CardDemo COBOL corpus. This replaces
re-parsing source files on every AI query with instant structured reads.

**Honcho must be running before querying the corpus:**
```bash
honcho run   # or: docker-compose up
```

### Quick Start — AI Harness Integration

If you are building a local AI harness (Hermes, Claude, Ollama, etc.)
that needs to query the CardDemo corpus, connect to Honcho like this:

**Python (requests)**
```python
import requests

HONCHO_BASE = "http://localhost:18000"
WORKSPACE   = "hermes"
SESSION     = "hermes-agent"
MESSAGES_URL = f"{HONCHO_BASE}/v3/workspaces/{WORKSPACE}/sessions/{SESSION}/messages"

def honcho_get(key: str) -> dict | None:
    """Retrieve the latest value for a canonical key."""
    resp = requests.get(MESSAGES_URL, params={
        "metadata_filter": f'{{"honcho_key": "{key}"}}',
        "reverse": "true",
        "size": 1
    })
    if resp.status_code == 200:
        items = resp.json().get("items", [])
        if items:
            import json
            return json.loads(items[0]["content"])
    return None

# Examples
para   = honcho_get("COACTUPC/para/0000-MAIN")
layout = honcho_get("COACTUPC/layout/WS-MISC-STORAGE.ACCT-UPDATE-RECORD")
cfg    = honcho_get("COACTUPC/cfg/summary")
oracle = honcho_get("COACTUPC/oracle/v1")
meta   = honcho_get("COACTUPC/meta")
```

**Key Schema Reference**
```
{PROGRAM}/para/{PARAGRAPH_NAME}        — IR unit with performs, mutates
{PROGRAM}/layout/{QUALIFIED.FIELD}     — byte offset, length, PIC clause
{PROGRAM}/cfg/summary                  — nodes, edges, entry point
{PROGRAM}/oracle/v{N}                  — regression oracle
{PROGRAM}/meta                         — program metadata
```

**Corpus Coverage**
- 31 programs, 518 paragraphs, ~3,900 layout fields, 31 CFGs
- Oracle: COACTUPC only (v1)

### Reloading the Corpus (if Honcho is reset)
```bash
python scripts/load_corpus.py --run
# Expected: ~21 minutes, 31 programs, zero failures
```

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
translator. 17 of 31 programs are CICS programs and are permanently outside
GnuCOBOL's scope. CICS programs are marked `preprocess_skipped` in validator
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
| Custom Python extraction scripts | GitHub Actions / Docker |
| Schema definitions | Agent harness code |
| Deterministic round-trip validator | CICS translator / stubs |
| Manual runbook | Automated pipeline runners |

---

## Prerequisites

- **Python 3.10+** — required
- **Honcho v3** running at `http://localhost:18000` — required for AI harness queries
- **GnuCOBOL 3.2+** (`cobc` on PATH) — **optional**, used only by `validate_roundtrip.py`
  Mode A (preprocess verification) on the ~14 non-CICS programs. The extraction
  pipeline itself has no GnuCOBOL dependency. If `cobc` is not installed,
  Mode A is skipped with a clear `cobc not found on PATH` message; all other
  pipeline and validation functions work normally.
- `pip install -r requirements.txt`

> **Note on COBOL-REKT / smojol:** These tools were used early in the project
> to understand COBOL program structure patterns. They are **not** part of the
> current pipeline and are **not** required. All extraction is performed by the
> custom Python scripts in `scripts/`.

---

## Quick orientation

```
HermesCOBOL/
  data/raw/cbl/           <- raw COBOL .cbl source files (committed)
  data/raw/cpy/           <- raw non-BMS copybooks (committed)
  data/raw/cpy-bms/       <- raw BMS map copybooks (committed)
  data/canonical/         <- canonical IR JSON per program (gitignored, produced locally)
  data/facts/             <- extracted facts JSON per program (gitignored, produced locally)
  data/byte_layouts/      <- byte layout JSON per program (gitignored, produced locally)
  data/cfg/               <- CFG JSON per program (gitignored, produced locally)
  data/data_flow/         <- data flow JSON per program (gitignored, produced locally)
  scripts/                <- custom Python extraction + validation (run manually)
  validation/             <- validator outputs (gitignored, local only)
  docs/manual-runbook.md      <- step-by-step local operation guide
  docs/validation-runbook.md  <- round-trip validator guide
```

See [docs/manual-runbook.md](docs/manual-runbook.md) for the full pipeline.
See [docs/validation-runbook.md](docs/validation-runbook.md) for the validator.

---

## Custom Python Extraction Stack

All extraction is performed by scripts in `scripts/`. Key components:

| Script | Role |
|---|---|
| `hermes_v11_combined_extractor.py` | Primary combined extractor (paragraph IR, performs, terminators) |
| `extract_byte_layout.py` + `byte_layout.py` | WORKING-STORAGE byte layout parser |
| `extract_cfg_local.py` / `extract_cfg_summary.py` | Control flow graph builder |
| `extract_paragraph_io.py` | Paragraph I/O analysis |
| `extract_fallthrough.py` | Fall-through edge detection |
| `data_flow.py` | Data flow and mutation analysis |
| `pass1_annotate.py` | First-pass annotation |
| `assemble_canonical.py` | Assembles all extractions into canonical IR |
| `cobol_program_dict.py` | Unified validated access layer over canonical IR |
| `cobol_walker.py` | Deterministic DFS traversal engine over CobolProgramDict |
| `honcho_loader.py` | Loads / verifies / lists Honcho entries |
| `load_corpus.py` | Orchestrates full 31-program corpus load into Honcho |

---

## Round-Trip Validation (manual, deterministic)

- **Mode A (preprocess):** Runs `cobc -E -I cpy -I cpy-bms` on each non-CICS `.cbl`.
  SHA-256 hashes both raw and preprocessed outputs. Pins GnuCOBOL version.
  CICS programs (17 of 31) are skipped with reason `cics_no_translator` — not failed.
  **GnuCOBOL is only required for this mode.**
- **Mode B (structural coverage):** Independently scans each `.cbl` using pure Python
  for paragraphs, 01-level items, CALL targets, SELECT/ASSIGN definitions, EXEC CICS/SQL
  presence. Compares against `data/facts/<PROG>.json`. Runs for **ALL 31 programs** with
  no GnuCOBOL dependency.

**Reports go to:** `validation/reports/` (gitignored, local only)

```bash
python scripts/validate_roundtrip.py             # all programs
python scripts/validate_roundtrip.py CBACT01C    # single program
```

Exit code `0` = all PASS. Exit code `1` = one or more FAIL.

**Mode B is pure Python. No LLMs. No server. No automation. No stubs.**

---

## What is NOT committed

- No preprocessed COBOL output
- No CFG JSON reports
- No facts JSON
- No canonical IR JSON
- No byte layout JSON
- No data flow JSON
- No markdown pipeline outputs
- No generated artifacts of any kind
- No stubs, translators, or synthetic copybooks

All generated artifacts live under `data/preprocessed/`, `data/rekt/`,
`data/facts/`, `data/canonical/`, `data/byte_layouts/`, `data/cfg/`,
`data/data_flow/`, and `validation/` — gitignored, produced locally only.

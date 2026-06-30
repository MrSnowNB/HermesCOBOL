---
title: HermesCOBOL — Project Rules
version: 1.1
scope: project
---

# Stack Summary

- **Language/Runtime:** Python 3.10+ (core pipeline uses only stdlib: re, json, pathlib, hashlib, subprocess)
- **COBOL Tooling:**
  - GnuCOBOL 3.2+ (`cobc -E -I ...`) — **optional**, used only by `validate_roundtrip.py` Mode A (preprocess hash verification) on non-CICS programs. The extraction pipeline has no GnuCOBOL dependency. 17 of 31 programs are CICS and are permanently skipped by Mode A.
  - COBOL-REKT / smojol — **not used**. These tools were consulted early in the project to understand structural patterns. All extraction is performed by the custom Python scripts in `scripts/`.
- **Memory Store:** Honcho v3 at `http://localhost:18000` — **required** for AI harness queries. Must be running before calling `honcho_loader.py` or `load_corpus.py`.
- **Corpus:** 31 raw mainframe COBOL programs + copybooks from AWS CardDemo (`data/raw/cbl/*.cbl`, `data/raw/cpy/*.cpy`, `data/raw/cpy-bms/*.cpy`)
- **Key Constraints:** Raw-data-only policy (see README.md). No generated artifacts committed. CICS programs intentionally skip `cobc -E` (no translator; marked `preprocess_skipped=cics_no_translator`). All pipeline outputs go to gitignored dirs only: `data/preprocessed/`, `data/facts/`, `data/canonical/`, `data/byte_layouts/`, `data/data_flow/`, `data/cfg/`, `validation/`, `audit/`
- **Testing:** pytest (`tests/test_*.py`); domain validator `scripts/validate_roundtrip.py` (primary gate)
- **Docs:** `docs/manual-runbook.md` (full pipeline steps), `docs/validation-runbook.md` (round-trip gates), `scripts/SCRIPTS_INVENTORY.md` (living script registry and gate status)

# Custom Python Extraction Stack

All COBOL parsing and IR extraction is performed by scripts in `scripts/`. Key components (in pipeline order):

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
| `cobol_walker.py` | Deterministic DFS traversal engine |
| `honcho_loader.py` | Loads / verifies / lists Honcho entries |
| `load_corpus.py` | Orchestrates full 31-program corpus load into Honcho |

# Journal Path Convention

`logs/morty-journal.jsonl` (append-only JSONL). Use `journal-anchor` skill (or `scripts/append.ps1` if added) for durable traces of type `done|checkpoint|decision|close|issue`. Create `logs/` directory on first use. See journal-anchor SKILL.md for payload schema. All session state that must survive compaction goes here.

# Test Command

**Primary domain gate (recommended before claiming any extraction work complete):**
```bash
python scripts/validate_roundtrip.py              # all programs (31)
python scripts/validate_roundtrip.py CBACT01C     # single program
```
- Exit code `0` = all PASS
- Exit code `1` = one or more FAIL
- Exit code `2` = fatal input error

> Mode A (GnuCOBOL preprocess hash) runs only on non-CICS programs (~14). Mode B (pure Python structural coverage) runs on all 31. Both modes must pass for a green run.

Also run after facts changes:
```bash
python scripts/schema.py
```

**Unit tests:**
```bash
pytest tests/ -v
# or targeted
python -m pytest tests/test_byte_layout.py tests/test_data_flow.py tests/test_extract_facts_alignment.py -q --tb=short
```

# Commit Protocol Hint

Follow **Morty Law** from the user-global CLAUDE.md (and MORTY.md):
- **Never** run `git commit` directly.
- For any non-trivial work: invoke `/spec` first (writes SPEC.md at project root), implement strictly per the spec, then ask Mark to review the changes before proposing any commit message.
- If this project later defines a `/commit` slash command (in `.claude/commands/`), use it exclusively.
- Always update `scripts/SCRIPTS_INVENTORY.md` and re-run the relevant validators when modifying extractors (`data_flow.py`, `byte_layout.py`, `extract_facts.py`, etc.).

# Additional Project Conventions

- **Read first:** README.md (raw-data-only policy, scope table, CICS note) + the two runbooks in `docs/` before touching any script or data.
- **Source of truth:** Validators (`validate_roundtrip.py`, `schema.py`) and facts snapshots. Do not declare "done" or "green" without clean runs.
- **Domain vocabulary (use exactly):**
  - `raw .cbl` / `raw .cpy` — committed sources only (never edit in place)
  - `preprocess_skipped`, `cics_no_translator`, `cics_structural_only`, `gate_note`, `gate_status`
  - `Mode A` (preprocess hash roundtrip, GnuCOBOL, non-CICS only), `Mode B` (structural coverage via facts, pure Python, all 31 programs)
  - `facts/` (ground truth), `canonical/` (assembled IR), `byte_layouts/`, `data_flow/` (extracted artifacts)
  - Section gates: 3.1 (paragraphs), 3.2 (CALL), 3.3 (INSPECT/SORT), 3.4 (section_name + close-out)
- **CardDemo corpus programs:** CBACT01C–04C, CBCUS01C, CBEXPORT, CBIMPORT, CBSTM03A/B, CBTRN01C–03C, COACTUPC/WC, COADM01C, COBIL00C, COBSWAIT, COCRDLIC/SLC/DUPC, COMEN01C, CORPT00C, COSGN00C, COTRN00C–02C, COUSR00C–03C, CSUTLDTC
- **Do not:** Add stub/synthetic copybooks, CICS translator output, LLM-generated code, servers, or harness code to this repo. Those belong in hermes-agent / harness-sandbox layers.
- **Do not** reference COBOL-REKT or smojol as current dependencies anywhere. They are historical research tools only.
- **Sub-project note:** `scripts/carddemo_imported/` contains legacy/ported CardDemo scripts (REFERENCE status). Prefer and maintain the native top-level `scripts/` versions for active pipeline.

# Local Workflow / Slash Commands

Inherits all global Morty commands (`/spec`, `/checkpoint`, `/compact`, `/teach`, `/introspect`, `/research`, `/review`).

Project-specific commands can be added under `.claude/commands/` later (none yet).

When starting work here, run `/introspect` to confirm MORTY_PROJECT_ROOT points here, then read this CLAUDE.md (it overlays the global policy).

# References (read these)

- [README.md](README.md)
- [docs/manual-runbook.md](docs/manual-runbook.md)
- [docs/validation-runbook.md](docs/validation-runbook.md)
- [scripts/SCRIPTS_INVENTORY.md](scripts/SCRIPTS_INVENTORY.md)
- [RELEASE_NOTES.md](RELEASE_NOTES.md)
- `audit/` and `validation/` for current gate status (local only)

---
*v1.1 — corrected stack summary to reflect custom Python extraction stack; COBOL-REKT/smojol removed as active dependency; GnuCOBOL correctly scoped to optional Mode A validation only; Honcho documented as required runtime dependency.*

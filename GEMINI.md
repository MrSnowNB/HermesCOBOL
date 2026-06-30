# HermesCOBOL — Project State (Honcho-as-RAM v1)

## What This Project Is
HermesCOBOL is a deterministic COBOL extraction and knowledge-ingestion pipeline
for the IBM CardDemo application (31 COBOL programs). A fully custom Python stack
parses each program, produces paragraph-level IR, byte layout maps, and control flow
graphs — all stored in a Honcho v3 memory server as a persistent, queryable knowledge
base for AI-assisted translation by the Hermes agent.

## Important: Tooling Clarification

- **COBOL-REKT / smojol:** NOT part of the pipeline. These tools were consulted early
  in the project to learn COBOL structural patterns. All extraction is performed by
  custom Python scripts in `scripts/`.
- **GnuCOBOL (`cobc`):** OPTIONAL. Used only by `validate_roundtrip.py` Mode A
  (preprocess hash verification) on the ~14 non-CICS programs. The extraction pipeline
  itself has no GnuCOBOL dependency. 17 of 31 programs are CICS and are permanently
  outside GnuCOBOL's scope — they are marked `preprocess_skipped=cics_no_translator`,
  which is by design, not a failure.
- **Honcho v3:** REQUIRED at `http://localhost:18000` for any AI harness queries.

## Honcho Store — Current State
Honcho is running at `http://localhost:18000`.
Workspace: `hermes` | Session: `hermes-agent`

| Namespace            | Count        | Description                        |
|----------------------|--------------|------------------------------------|
| `{PROG}/para/{name}` | 518 units    | Paragraph-level IR for 31 programs |
| `{PROG}/layout/{field}` | ~3,900 fields | WORKING-STORAGE byte layout     |
| `{PROG}/cfg/summary` | 31 documents | Control flow graph per program     |
| `{PROG}/oracle/v1`   | 1 document   | Regression oracle (COACTUPC only)  |
| `{PROG}/meta`        | 31 documents | Program metadata index             |

## Key Schema
```
{PROGRAM}/para/{PARAGRAPH_NAME}     — IR unit
{PROGRAM}/layout/{QUALIFIED.FIELD}  — layout entry
{PROGRAM}/cfg/summary               — CFG document
{PROGRAM}/oracle/v{N}               — simulation oracle
{PROGRAM}/meta                      — program metadata
```

## Programs in Corpus
31 CardDemo programs. All have: layout ✅, CFG ✅, para IR ✅.
Oracle exists only for COACTUPC (v1).
COBSWAIT is a stub program (0 paragraphs, 2 fields) — expected.
17 programs are CICS — their paragraph flow was extracted by the custom Python stack
(not GnuCOBOL, which cannot handle raw EXEC CICS blocks).

## Custom Python Extraction Stack (pipeline order)
| Script | Purpose |
|--------|---------|
| `scripts/hermes_v11_combined_extractor.py` | Primary extractor: paragraph IR, performs, terminators |
| `scripts/extract_byte_layout.py` + `byte_layout.py` | WORKING-STORAGE byte layout parser |
| `scripts/extract_cfg_local.py` | Local CFG extractor (canonical path) |
| `scripts/extract_cfg_summary.py` | CFG summary generator |
| `scripts/extract_paragraph_io.py` | Paragraph I/O analysis |
| `scripts/extract_fallthrough.py` | Fall-through edge detection |
| `scripts/data_flow.py` | Data flow and mutation analysis |
| `scripts/pass1_annotate.py` | First-pass annotation |
| `scripts/assemble_canonical.py` | Assembles all extractions into canonical IR |
| `scripts/cobol_program_dict.py` | Unified validated access layer over canonical IR |
| `scripts/cobol_walker.py` | Deterministic DFS traversal engine (CobolWalker) |
| `scripts/honcho_loader.py` | Load/verify/list Honcho entries. Primary loader. |
| `scripts/load_corpus.py` | Orchestrate full 31-program corpus load |
| `scripts/validate_roundtrip.py` | Roundtrip validation — Mode A (GnuCOBOL, non-CICS) + Mode B (pure Python, all 31) |
| `scripts/validate_section34_diagnosis.py` | Paragraph count validator |
| `scripts/audit_cobol_walker.py` | Walker baseline for Gate 10 regression |

## Common Commands
```bash
# Check what's in Honcho
python scripts/honcho_loader.py --list

# Verify a single program
python scripts/honcho_loader.py --verify COACTUPC

# Reload a program's paragraphs
python scripts/honcho_loader.py --program COACTUPC \
  --manifest docs/COACTUPC_Honcho_Load_Manifest.json

# Reload a program's layout
python scripts/honcho_loader.py --program COACTUPC \
  --layout docs/COACTUPC_byte_layout.json

# Full corpus reload (if Honcho is reset)
python scripts/load_corpus.py --run

# Audit stale UNKNOWN keys
python scripts/honcho_loader.py --audit-unknown

# Run all validators (primary gate)
python scripts/validate_roundtrip.py
```

## Completed Phases
- ✅ Phase 1 — `honcho_loader.py` + COACTUPC para IR (fd34250)
- ✅ Phase 2 — Byte layout load, 1,165 fields (d07be38)
- ✅ Perf Fix — Batch writes, 90x speedup (b825709)
- ✅ Phase 3+4 — CFG + Oracle load (ada4865)
- ✅ Phase 5 — Full 31-program corpus load, 21 min (cca0804)
- ✅ Phase 6 — Para key mapping fix, 518 paragraphs (d7534f3)
- ✅ Phase 7 — CobolProgramDict unified access layer (SPEC.md)
- ✅ Phase 8 — CobolWalker deterministic DFS traversal (SPEC-CobolWalker.md)

## Next Phase — Translation (Hermes)
Honcho infrastructure is complete. Switch to Hermes for:
- Cross-program analysis queries
- Paragraph-level translation to Python
- Simulation and oracle validation
- Regression testing against write-path oracle

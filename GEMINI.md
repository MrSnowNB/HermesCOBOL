# HermesCOBOL — Project State (Honcho-as-RAM v1)

## What This Project Is
HermesCOBOL is a deterministic COBOL-to-modern-language translation engine
for the IBM CardDemo application (31 COBOL programs). It uses a structured
extraction pipeline to produce paragraph-level IR, byte layout maps, and
control flow graphs — all stored in a Honcho v3 memory server as a
persistent, queryable knowledge base for AI-assisted translation.

## Honcho Store — Current State
Honcho is running at `http://localhost:18000`.
Workspace: `hermes` | Session: `hermes-agent`

| Namespace            | Count        | Description                        |
|----------------------|--------------|------------------------------------|
| `{PROG}/para/{name}` | 518 units    | Paragraph-level IR for 30 programs |
| `{PROG}/layout/{field}` | ~3,900 fields | WORKING-STORAGE byte layout     |
| `{PROG}/cfg/summary` | 31 documents | Control flow graph per program     |
| `{PROG}/oracle/v1`   | 1 document   | Regression oracle (COACTUPC only)  |
| `{PROG}/meta`        | 31 documents | Program metadata index             |

## Key Schema
{PROGRAM}/para/{PARAGRAPH_NAME} — IR unit
{PROGRAM}/layout/{QUALIFIED.FIELD} — layout entry
{PROGRAM}/cfg/summary — CFG document
{PROGRAM}/oracle/v{N} — simulation oracle
{PROGRAM}/meta — program metadata

## Programs in Corpus
31 CardDemo programs. All have: layout ✅, CFG ✅, para IR ✅.
Oracle exists only for COACTUPC (v1).
COBSWAIT is a stub program (0 paragraphs, 2 fields) — expected.

## Scripts Inventory
| Script | Purpose |
|--------|---------|
| `scripts/honcho_loader.py` | Load/verify/list Honcho entries. Primary loader. |
| `scripts/load_corpus.py` | Orchestrate full 31-program corpus load |
| `scripts/extract_byte_layout.py` | Extract WORKING-STORAGE byte layout from source |
| `scripts/byte_layout.py` | Byte layout data model (v1.2.2) |
| `scripts/extract_cfg_summary.py` | Generate CFG JSON from COBOL source |
| `scripts/extract_cfg_local.py` | Local CFG extractor variant |
| `scripts/audit_cobol_walker.py` | Walker baseline for Gate 10 regression |
| `scripts/validate_roundtrip.py` | Roundtrip validation (all 31 programs) |
| `scripts/validate_section34_diagnosis.py` | Paragraph count validator |

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
```

## Completed Phases
- ✅ Phase 1 — `honcho_loader.py` + COACTUPC para IR (fd34250)
- ✅ Phase 2 — Byte layout load, 1,165 fields (d07be38)
- ✅ Perf Fix — Batch writes, 90x speedup (b825709)
- ✅ Phase 3+4 — CFG + Oracle load (ada4865)
- ✅ Phase 5 — Full 31-program corpus load, 21 min (cca0804)
- ✅ Phase 6 — Para key mapping fix, 518 paragraphs (d7534f3)

## Next Phase — Translation (Hermes)
Honcho infrastructure is complete. Switch to Hermes for:
- Cross-program analysis queries
- Paragraph-level translation to Python
- Simulation and oracle validation
- Regression testing against write-path oracle
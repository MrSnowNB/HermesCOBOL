# AI Harness Integration Guide — HermesCOBOL Honcho Store

## Overview
This guide is for AI agents (Hermes, Claude, Gemini, Ollama-hosted models,
or any LLM harness) that need to reason over the CardDemo COBOL corpus
without re-parsing source files.

## Prerequisites
- Honcho v3 running at `http://localhost:18000`
- Workspace `hermes`, session `hermes-agent` populated
- Verify: `python scripts/honcho_loader.py --list`

---

## Orientation Sequence for a New AI Session

When starting a fresh session, run this orientation sequence to load
working context:

```python
# Step 1 — Verify store is live
meta = honcho_get("COACTUPC/meta")
assert meta is not None, "Honcho store is not reachable or empty"

# Step 2 — Load program index
programs = []
for prog in ["COACTUPC","COACTVWC","COCRDLIC","COCRDUPC","COBIL00C",
             "CBACT01C","CBACT02C","CBACT03C","CBACT04C","CBCUS01C",
             "CBEXPORT","CBIMPORT","CBSTM03A","CBSTM03B","CBTRN01C",
             "CBTRN02C","CBTRN03C","COADM01C","COBSWAIT","COCRDSLC",
             "COMEN01C","CORPT00C","COSGN00C","COTRN00C","COTRN01C",
             "COTRN02C","COUSR00C","COUSR01C","COUSR02C","COUSR03C",
             "CSUTLDTC"]:
    m = honcho_get(f"{prog}/meta")
    if m:
        programs.append(m)

# Step 3 — Load target program IR
def load_program_context(prog: str) -> dict:
    return {
        "meta":   honcho_get(f"{prog}/meta"),
        "cfg":    honcho_get(f"{prog}/cfg/summary"),
        "oracle": honcho_get(f"{prog}/oracle/v1"),  # None if not yet built
    }
```

---

## Query Patterns

### Get a specific paragraph
```python
para = honcho_get("COACTUPC/para/1200-EDIT-MAP-INPUTS")
# Returns: {name, performs, goto_targets, mutates, reachable, ...}
```

### Get a field's byte layout
```python
field = honcho_get("COACTUPC/layout/WS-MISC-STORAGE.ACCT-UPDATE-RECORD.ACCT-UPDATE-ID")
# Returns: {qualified_name, level, offset, length, pic, storage, redefines}
```

### Check if a field is a write-only oracle field
```python
oracle = honcho_get("COACTUPC/oracle/v1")
write_fields = set(oracle["write_only_fields"])
is_write_target = "WS-MISC-STORAGE.ACCT-UPDATE-RECORD" in write_fields
```

### Walk a CFG from entry point
```python
cfg = honcho_get("COACTUPC/cfg/summary")
entry = cfg["program_id"]  # or cfg.get("entry_point", "0000-MAIN")
# cfg["paragraphs"] contains nodes with performs lists
```

---

## Translation Workflow (Paragraph-by-Paragraph)

The intended translation loop for Hermes or any translation agent:

```python
PROGRAM = "COACTUPC"
cfg     = honcho_get(f"{PROGRAM}/cfg/summary")
oracle  = honcho_get(f"{PROGRAM}/oracle/v1")

# Walk paragraphs in CFG order
for node in cfg["paragraphs"]:
    para_name = node["name"]
    para_ir   = honcho_get(f"{PROGRAM}/para/{para_name}")
    if para_ir is None:
        continue

    # For each mutated field, get its layout
    for field in para_ir.get("mutates", []):
        layout = honcho_get(f"{PROGRAM}/layout/{field}")
        # Use offset/length/pic to generate correct Python type

    # Translate paragraph to Python function
    # Validate: if para writes oracle fields, run regression check
    is_write_para = any(
        f in (oracle or {}).get("write_only_fields", [])
        for f in para_ir.get("mutates", [])
    )
```

---

## Reload Reference

If Honcho is reset or a program needs to be refreshed:

```bash
# Single program (all namespaces)
python scripts/load_corpus.py --program COACTUPC

# Full corpus
python scripts/load_corpus.py --run

# Layout only
python scripts/honcho_loader.py --program COACTUPC \
  --layout docs/COACTUPC_byte_layout.json

# Para IR only
python scripts/honcho_loader.py --program COACTUPC \
  --manifest docs/COACTUPC_Honcho_Load_Manifest.json

# Verify after reload
python scripts/honcho_loader.py --verify COACTUPC
```

---

## Known Limitations (v1)
- DELETE is not supported by Honcho v3 — stale duplicate keys accumulate
  on reload. `get()` always returns the newest entry (reverse=true&size=1).
- Oracle exists only for COACTUPC. Other programs need oracle generation
  before write-path regression testing can run.
- COBSWAIT has 0 paragraphs — it is a CICS wait stub, not a logic program.
- `_SUMMARY` may appear as a ghost entry in `--list` — it is a known
  artifact from the canonical JSON structure and can be ignored.
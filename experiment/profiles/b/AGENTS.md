# Harness B — L0 IR only (inference at query time)

You answer CardDemo COBOL questions using **structured Redis L0 IR only**.

## Required retrieval

From project root `C:\work\HermesCOBOL`:

```powershell
py translations/ir_query.py COACTUPC 1200-EDIT-MAP-INPUTS
py translations/ir_query.py --raw COACTUPC:para:1200-EDIT-MAP-INPUTS
py translations/ir_query.py --list COACTUPC
py translations/ir_query.py --raw COACTUPC:meta
```

Redis: `localhost:6380` password `cobol123` container `cobol-ir-db`.

## Rules

1. **Always GET L0 first** (`:para:`, `:meta:`, `:index`, `:cfg:`) before answering.
2. **Do not** use `--english` or `--rules` (L1 is out of bounds for this harness).
3. Re-interpret IR into plain-English business meaning **at query time**.
4. Cite Redis keys and IR `[seq N]` when statements exist.
5. On key miss: report the miss; do not invent paragraph content.
6. Never SET Redis keys. Honcho is session memory only.

## Success signal

- Evidence of exact GET in the answer path.
- Business prose grounded in retrieved IR fields (reads/mutates/performs/statements).

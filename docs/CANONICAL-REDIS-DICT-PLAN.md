# Living Plan — Replace COBOL Redis Vector DB with Canonical IR Dictionary

**Status:** COMPLETE (automation + skills); Hermes interactive smoke optional  
**Created:** 2026-07-14  
**Last updated:** 2026-07-14  
**Owner:** HermesCOBOL alpha packaging track  
**Final report:** `docs/CANONICAL-REDIS-MIGRATION-REPORT.md`

---

## Intent

Replace the experimental **vector** Redis store with a **plain Redis dictionary** of exact key → full JSON IR values. This is the **inference boundary**.

```
data/canonical/*.canonical.json   (source of truth — not modified)
        │
        ▼  ingest_redis_canonical.py
   Redis plain GET/SET dictionary  (cobol-ir-db :6380)
        │
        ▼  ← inference boundary
   Hermes / ir_query.py (GET only)
```

---

## Non-negotiable rules (observed)

| Rule | Status |
|------|--------|
| Do not modify `data/canonical/` | ✅ |
| Do not modify translation modules (except `ir_query.py`) | ✅ |
| Do not modify Honcho | ✅ |
| Do not delete `data/raw/cbl/` | ✅ |
| Do not run `load_corpus.py` | ✅ |
| Archive vector scripts before replace | ✅ |

---

## Step tracker

| Step | Title | Status |
|------|--------|--------|
| 1 | Verify vector Redis state | **DONE** — DBSIZE 101, hashes + `cobol_ir` |
| 2 | Audit canonical IR | **DONE** — 31 programs, 518 paragraphs |
| 3 | Archive scripts | **DONE** — `archive/vector_experiment/` |
| 4 | Flush vector data | **DONE** — FLUSHALL → 0 |
| 5 | Update compose → `cobol-ir-db` / `redis:7-alpine` | **DONE** |
| 6 | Write `ingest_redis_canonical.py` | **DONE** |
| 7 | Load + verify | **DONE** — DBSIZE 1130, all pass criteria |
| 8 | Update Hermes skills + `ir_query.py` | **DONE** |
| 9 | Hermes Acid Burn smoke | **Manual prompt ready** (automated GET smoke PASS) |
| 10 | Final report | **DONE** — `CANONICAL-REDIS-MIGRATION-REPORT.md` |

---

## Key schema (live)

| Key | Value |
|-----|--------|
| `{PROG}:meta` | Program metadata |
| `{PROG}:para:{NAME}` | Full paragraph IR JSON |
| `{PROG}:cfg:{NAME}` | CFG slice |
| `{PROG}:cfg:summary` | Program CFG summary |
| `{PROG}:index` | Paragraph name list |
| `cobol:manifest` | Load summary |

---

## Reload commands

```powershell
cd C:\work\HermesCOBOL
docker compose -f docker-compose-cobol-db.yml up -d
python ingest_redis_canonical.py
py translations\ir_query.py COACTUPC 1200-EDIT-MAP-INPUTS
```

---

## Rollback

1. `archive/vector_experiment/*` restore scripts/compose  
2. `docker compose -f docker-compose-cobol-db.yml down`  
3. Restore stack image if needed from bak  

---

## Execution log (condensed)

- Step 1: Vector experiment confirmed (raw text chunks + embeddings).  
- Step 2: Canonical structural IR 1.4; COACTUPC statement enrichment from manifest v2.  
- Step 3–4: Archived; flushed.  
- Step 5–7: `cobol-ir-db` up; 518 paras loaded; GET proof for 0000-MAIN and 1200-EDIT-MAP-INPUTS.  
- Step 8: Skills + `ir_query.py` exact GET.  
- Step 9–10: Report + interactive prompt documented.  

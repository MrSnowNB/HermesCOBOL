# Migration Report — COBOL Redis Vector DB → Canonical IR Dictionary

**Date:** 2026-07-14  
**Living plan:** `docs/CANONICAL-REDIS-DICT-PLAN.md`  
**Status:** COMPLETE (Steps 1–8, 10 automated; Step 9 Hermes interactive — paste-ready)

---

## 1. Before state

| Item | Value |
|------|--------|
| Container | `cobol-vector-db` |
| Image | `redis/redis-stack:latest` |
| Port | 6380 |
| DBSIZE | **101** |
| Data shape | HASH keys `cobol:para:{NAME}:{chunk}` |
| Fields | `embedding` (768-d), `paragraph_name`, `content` (raw COBOL text chunks), `chunk_index` |
| Index | RediSearch **`cobol_ir`** (HNSW) |
| App keys (SCAN) | ~64 hashes (COACTUPC-scale slice) |
| Structured IR? | **No** — text chunks only |
| Loader | `ingest_cobol_redis.py` (archived) |

---

## 2. After state

| Item | Value |
|------|--------|
| Container | **`cobol-ir-db`** |
| Image | **`redis:7-alpine`** |
| Port | 6380 (unchanged) |
| Password | `cobol123` |
| DBSIZE | **1130** |
| Data shape | STRING keys (JSON payloads) |
| Key schema | `{PROG}:meta`, `{PROG}:para:{NAME}`, `{PROG}:cfg:{NAME}`, `{PROG}:cfg:summary`, `{PROG}:index`, `cobol:manifest` |
| Programs | **31** |
| Paragraphs | **518** |
| Vector index | **None** (`FT._LIST` → unknown command) |
| Old vector keys | **0** |
| Loader | `ingest_redis_canonical.py` |

### Sample proof — `COACTUPC:para:1200-EDIT-MAP-INPUTS`

- Structured JSON (not plain text chunk)
- `statements`: **134**
- `verbs`: **134**
- First statement: `{"seq": 209, "verb": "SET", "raw": "SET INPUT-OK TO TRUE", ...}`
- Enriched from `docs/COACTUPC_Honcho_Load_Manifest_v2.json` (canonical files untouched)

### Manifest

```json
{
  "program_count": 31,
  "paragraph_count": 518,
  "schema_version": "1.4",
  "store": "canonical-ir-dictionary"
}
```

---

## 3. Container rename

| Before | After |
|--------|--------|
| service / container `cobol-vector-db` | **`cobol-ir-db`** |
| `redis/redis-stack:latest` | **`redis:7-alpine`** |
| volume `cobol_redis_data` | **`cobol_ir_data`** |
| compose file | `docker-compose-cobol-db.yml` (updated in place) |

---

## 4. Scripts archived

```
archive/vector_experiment/
  ingest_cobol_redis.py.bak
  test_redis_query.py.bak
  docker-compose-cobol-db.yml.bak
  ir_query.py.bak
```

Root copies of vector scripts may still exist as historical files; **do not run them**. Use `ingest_redis_canonical.py` only.

---

## 5. Scripts created

| Path | Role |
|------|------|
| `ingest_redis_canonical.py` | Load all `data/canonical/*.canonical.json` into Redis dictionary; optional statement enrichment from docs manifests |
| `translations/ir_query.py` | Exact GET client (SCAN fallback); **no embeddings / KNN / FT.SEARCH** |

Reload anytime:

```powershell
cd C:\work\HermesCOBOL
docker compose -f docker-compose-cobol-db.yml up -d
python ingest_redis_canonical.py
```

---

## 6. Skills updated

| Skill / file | Change |
|--------------|--------|
| `~/.hermes/skills/cobol/cobol-ir-query/SKILL.md` | Vector/KNN → **exact GET dictionary** |
| `~/.hermes/skills/cobol/cobol-ir-query/references/ir_query.py` | GET-only mirror |
| `~/.hermes/skills/software-development/cobol-translation/SKILL.md` | Pre-flight + review use exact GET |
| `.../cobol-translation/references/pre-flight-diagnosis-checklist.md` | Verify `cobol-ir-db` + GET |
| `.../cobol-translation/references/evidence-first-source-fallback.md` | Dictionary-first, not truncated chunks |
| `~/.hermes/skills/software-development/cobol-ir-translation/SKILL.md` | Workflow: exact GET not KNN |

---

## 7. Smoke test

### Automated (PASS)

```text
py translations/ir_query.py COACTUPC 1200-EDIT-MAP-INPUTS
→ Method: GET  (no embeddings / no KNN / no FT.SEARCH)
→ Key: COACTUPC:para:1200-EDIT-MAP-INPUTS
→ statements: 134, verbs: 134
```

### Hermes Acid Burn interactive (manual)

Paste into the live Hermes session:

```
For the question "What does 1200-EDIT-MAP-INPUTS do in COACTUPC?":
1. List every tool or skill you will call
2. Show the raw tool output — do not summarize it
3. Cite exactly which store each fact came from (Redis key, file path, or Honcho session)
4. Do NOT answer from memory alone — retrieve first, then answer

Required retrieval command (from C:\work\HermesCOBOL):
  py translations/ir_query.py --raw COACTUPC:para:1200-EDIT-MAP-INPUTS

You must use Redis GET / ir_query exact lookup — not FT.SEARCH, not KNN, not embeddings.
```

Pass criteria for interactive run:

- [ ] Hermes calls Redis GET / `ir_query.py` (not FT.SEARCH, not KNN)
- [ ] Key cited: `COACTUPC:para:1200-EDIT-MAP-INPUTS`
- [ ] Raw output is structured JSON with statements/verbs
- [ ] No embedding model called
- [ ] Answer cites Redis key as source

---

## 8. Anomalies / notes

1. **Canonical IR vs statement IR:** Corpus-wide `data/canonical/` is structural (schema 1.4: terminator, last_verb, performs…). Full `statements[]` enrichment exists for **COACTUPC** (39 non-EXIT units in manifest v2); other programs get structural dictionary entries + `verbs` from `last_verb`.
2. **DBSIZE 1130** ≈ 518 para + 518 cfg + 31 meta + 31 index + ~31 cfg:summary + manifest (+ rounding).
3. **`data/canonical/` not modified** (source of truth preserved).
4. **Honcho untouched.**
5. Old root `ingest_cobol_redis.py` / `test_redis_query.py` left in tree for history; archived copies are authoritative backups.
6. Skill references under `cobol-ir-query/references/1215-edit-mandatory-retrieval.md` still describe old KNN example — historical; skill body is updated.

---

## Pass criteria checklist (Step 7)

- [x] DBSIZE > 100 (**1130**)
- [x] `GET COACTUPC:para:0000-MAIN` → structured JSON
- [x] JSON has `statements` / `verbs` (COACTUPC enriched)
- [x] `GET cobol:manifest` → paragraph_count **518**
- [x] Container name **`cobol-ir-db`**
- [x] No FT vector index
- [x] No old `cobol:para:*` chunk keys

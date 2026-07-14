# HermesCOBOL — Comprehensive Plan Summary & Next Steps

**Date:** 2026-07-14  
**Audience:** Partners, maintainers, Docker alpha packaging  
**Status:** Phase 1 complete · Phase 2 complete for COACTUPC · Full corpus Phase 2 deferred  

---

## 1. Product thesis (locked)

We are **not** building a COBOL-to-Python compiler as the primary deliverable.

We are building a **COBOL → English business-logic documentation engine**:

| Layer | Role |
|-------|------|
| **L0 — Deterministic IR** | Parsed structure from COBOL; ground truth |
| **L1 — English / rules** | Business documentation **generated once at ingestion**, frozen in Redis |
| **Query** | LLM **GETs** stored English/rules and synthesizes across keys — **does not re-interpret raw IR** |

**Key insight:** Partners’ stacks run expensive, error-prone interpretation on **every query**. We run interpretation **once** (Phase 2), store the result, and serve it. That is the production architecture that beats stacked fine-tuned models at query time.

**Seq provenance:** Every business claim in English should cite IR `[seq N]` (or range) when statements exist.

Primary docs:

- `docs/ENGLISH-BUSINESS-LOGIC-ENGINE.md` — architecture  
- `docs/ENGLISH-QUALITY-EVAL.md` — Prompt 3 + Tests A–D  
- `docs/PHASE2-COMPLETION-REPORT.md` — Phase 2 gate results  

---

## 2. What was delivered (this program of work)

### 2.1 Phase 1 — Deterministic IR dictionary (L0)

```
COBOL source → custom Python extractors → data/canonical/
  → ingest_redis_canonical.py → Redis cobol-ir-db
```

| Item | Result |
|------|--------|
| Container | `cobol-ir-db` (`redis:7-alpine`, port **6380**, password `cobol123`) |
| Replaced | Vector experiment (`cobol-vector-db` / Redis Stack / HNSW) |
| Programs | **31** |
| Paragraphs | **518** |
| Key types | `{PROG}:para:`, `:meta`, `:cfg:`, `:index`, `cobol:manifest` |
| Access | Plain **GET/SET** only — no embeddings, no FT.SEARCH |

Supporting:

- `docker-compose-cobol-db.yml`  
- `ingest_redis_canonical.py`  
- `archive/vector_experiment/` (old vector scripts)  
- Migration reports under `docs/CANONICAL-REDIS-*.md`  

### 2.2 Phase 2 — English ingestion worker (L1) — COACTUPC pilot

```
Redis :para: → phase2_english_worker.py (LLM once)
  → SET {PROG}:english:{NAME}
  → SET {PROG}:rules:{NAME}
```

| Item | Result |
|------|--------|
| Worker | `phase2_english_worker.py` |
| Model | `Qwen3.6-35B-A3B-MTP-GGUF` @ `http://127.0.0.1:8000/api/v1` |
| COACTUPC | **85** paragraphs: **84 DONE**, **1 SKIP** (pilot 1200), **0 FAIL**, **0 ERROR** |
| Runtime | ~**26 minutes** (full program after pilot) |
| Write protection | Only `:english:` / `:rules:` — never overwrites L0 |
| DBSIZE | 1132 → **1300** (+168 this run; pilot already +2) |

Query client:

- `translations/ir_query.py` — exact GET; **`--english`** / **`--rules`**; L1 miss → `L1 key not found — run phase2_english_worker.py` (no silent IR reinterpretation)

### 2.3 Inference boundary (ops contract)

| Phase | When | Inference? |
|-------|------|------------|
| 1 | Offline / load IR | **None** |
| 2 | First load / IR change | **Once per paragraph** |
| Query | Every partner question | **GET + multi-key synthesis only** |

### 2.4 Hermes agent startup contract

Slim `C:\work\hermes-agent\AGENTS.md` (~3–4 KB): product purpose, Redis schema (3 layers), `ir_query` usage, boundary, skill paths.  
Full upstream Hermes guide: `hermes-agent/docs/AGENTS-FULL.md` (not truncated into startup context).

### 2.5 Environment notes (ops)

| Issue | Resolution |
|-------|------------|
| Dual MTP / non-MTP Qwen loaded | Prefer MTP; `ensure_mtp_loaded.ps1` / unload non-MTP |
| `hermes update` Access Denied | Stop all `hermes.exe` first (`stop_hermes_for_update.ps1`) |
| Non-MTP reappears in Lemonade catalog | Built-in marketplace entry; DELETE does not remove catalog permanently |

---

## 3. Redis key schema (canonical)

| Key | Layer | Writer |
|-----|--------|--------|
| `{PROG}:para:{NAME}` | L0 | `ingest_redis_canonical.py` only |
| `{PROG}:meta` / `:cfg:…` / `:index` | L0 | same |
| `cobol:manifest` | L0 | same |
| `{PROG}:english:{NAME}` | L1 | `phase2_english_worker.py` only |
| `{PROG}:rules:{NAME}` | L1 | same |

Container: **`cobol-ir-db`** · **6380** · **cobol123**

---

## 4. How to operate (commands)

```powershell
cd C:\work\HermesCOBOL

# L0
docker compose -f docker-compose-cobol-db.yml up -d
python ingest_redis_canonical.py

# L1 (single program pilot pattern)
python phase2_english_worker.py --dry-run --program COACTUPC
python phase2_english_worker.py --program COACTUPC --paragraph 1200-EDIT-MAP-INPUTS --force
python phase2_english_worker.py --program COACTUPC

# Query
py translations/ir_query.py COACTUPC 1200-EDIT-MAP-INPUTS --english
py translations/ir_query.py COACTUPC 1200-EDIT-MAP-INPUTS --rules --raw
py translations/ir_query.py COACTUPC 9999-NONEXISTENT --english
# → L1 key not found — run phase2_english_worker.py
```

---

## 5. Known gaps / quality notes

| Gap | Severity | Notes |
|-----|----------|--------|
| Word budget overshoot | Medium | Prompt asks &lt;400 words; many docs 500–900w |
| Multi-seq BR parse | Low | Some BRs have `seq: null` while cites remain in text |
| Statement IR corpus-wide | Medium | Full `statements[]` enrichment strongest for COACTUPC; other programs more structural |
| Phase 2 for all 31 programs | Deferred | COACTUPC pilot only |
| Docker entrypoint automation | Deferred | Manual compose + worker today |
| Honcho IR reload | Separate | Structured Honcho corpus was empty earlier; not required for Redis L0/L1 path |

---

## 6. Next steps (prioritized)

### P0 — Partner alpha packaging (short path)

1. **Docker Compose stack** for alpha: `cobol-ir-db` + optional Honcho + Hermes; document env for Lemonade/LLM.  
2. **Image seed strategy:** bake L0 + COACTUPC L1 into volume/snapshot, or run Phase 1 then Phase 2 on first boot (long if LLM inside).  
3. **Partner runbook:** one page — up stack → `ir_query --english` → sample questions (Tests A–D).  
4. **Strict query skill:** Hermes skills default to `--english` / `--rules`; refuse to free-form invent on L1 miss.

### P1 — Quality & scale

5. **Word-budget enforcement** in worker (prompt + soft truncate / regenerate if &gt;500 words).  
6. **Improve BR `seq` parser** for multi-cite lines (`[seq 233, 241, 249]`).  
7. **Phase 2 remaining 30 programs** after COACTUPC quality review (overnight job; ~hours of LLM time).  
8. **Idempotent regen gate:** re-run Phase 2 when IR content hash changes only.

### P2 — Product surface

9. **Manifest L1 keys** in `cobol:manifest` or `cobol:english_manifest` (counts, generator_id, model_id).  
10. **Eval harness script** that runs Tests A–D against Redis and scores PASS/FAIL without interactive TUI.  
11. **Optional:** keep Python `translations/` as demo only; de-emphasize in partner docs.  
12. **Honcho:** re-align as session memory only; document separation from Redis business dictionary.

### P3 — Ops hardening

13. Automate MTP-only Lemonade profile on host.  
14. `hermes update` SOP: stop processes → update → ensure_mtp → healthcheck.  
15. CI: dry-run Phase 2 + L0 load in CI without LLM (or mock LLM).

---

## 7. Success criteria for “Docker alpha ready”

| Criterion | Status |
|-----------|--------|
| Deterministic IR in Redis for CardDemo | **Met** |
| English docs for flagship program (COACTUPC) | **Met** |
| Query path is GET of frozen English (not live IR reinterpret) | **Met** (client + data for COACTUPC) |
| Hallucination trap (missing key → nil / explicit L1 message) | **Met** |
| Full corpus English | **Not met** (deferred) |
| One-command partner deploy | **Not met** (next packaging slice) |

---

## 8. One-line partner pitch

> We isolate inference from data. COBOL becomes a deterministic IR dictionary; business meaning is written once into English documents at ingestion time. At query time you only retrieve—partners re-interpret mainframe logic with stacked models on every request.

---

## 9. Document map

| Doc | Purpose |
|-----|---------|
| `docs/PLAN-SUMMARY-AND-NEXT-STEPS.md` | **This file** |
| `docs/ENGLISH-BUSINESS-LOGIC-ENGINE.md` | Product architecture |
| `docs/ENGLISH-QUALITY-EVAL.md` | Prompt 3 + Tests A–D |
| `docs/PHASE2-COMPLETION-REPORT.md` | Phase 2 gate evidence |
| `docs/PHASE2-ENGLISH-WORKER-PLAN.md` | Worker step tracker |
| `docs/CANONICAL-REDIS-MIGRATION-REPORT.md` | Vector → dict migration |
| `docs/CANONICAL-REDIS-DICT-PLAN.md` | L0 living plan |
| `README.md` / `CLAUDE.md` | Project orientation |

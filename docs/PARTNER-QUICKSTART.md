# Partner Quickstart — HermesCOBOL English Business-Logic Engine

**One-line pitch:** We isolate inference from data. COBOL becomes a deterministic IR dictionary; business meaning is written **once** into English at ingestion. At query time you only **retrieve**.

---

## What you get

| Layer | Content | When written |
|-------|---------|--------------|
| **L0** | Structured IR in Redis (`:para:`, `:meta:`, `:index`) | Offline, deterministic |
| **L1** | English docs + business rules (`:english:`, `:rules:`) | Phase 2, once per paragraph |
| **Query** | Exact Redis GET via `ir_query.py` | Every question |

**Not included in the query path:** live re-interpretation of raw IR, vector search, embeddings, or writing chat conclusions back into Redis.

---

## Prerequisites

| Component | Default | Notes |
|-----------|---------|-------|
| Docker | Desktop / Engine | For `cobol-ir-db` |
| Redis dictionary | `localhost:6380` / password `cobol123` | `docker-compose-cobol-db.yml` |
| Python 3.11+ | project venv | `redis` package for loaders/query |
| LLM (ingestion + optional chat) | Lemonade `http://127.0.0.1:8000/api/v1` | Model: `Qwen3.6-35B-A3B-MTP-GGUF` or partner endpoint |
| Hermes CLI (optional) | `hermes` on PATH | Experiment harnesses A/B/C |

---

## 5-minute path (retrieve only)

```powershell
cd C:\work\HermesCOBOL

# 1. Start dictionary
docker compose -f docker-compose-cobol-db.yml up -d

# 2. Load L0 if empty (idempotent)
python ingest_redis_canonical.py

# 3. Query L0 IR
py translations/ir_query.py COACTUPC 1200-EDIT-MAP-INPUTS

# 4. Query L1 English (after Phase 2)
py translations/ir_query.py COACTUPC 1200-EDIT-MAP-INPUTS --english
py translations/ir_query.py COACTUPC 1200-EDIT-MAP-INPUTS --rules
```

**Hallucination trap (must refuse):**

```powershell
py translations/ir_query.py COACTUPC 9999-NONEXISTENT --english
# → L1 key not found — run phase2_english_worker.py
```

---

## Sample questions (Tests A–D)

Full prompts: `docs/ENGLISH-QUALITY-EVAL.md`.

| Test | Intent |
|------|--------|
| **A** | Extract BRs from `1265-EDIT-US-SSN` with `[seq N]` |
| **B** | Plain-English data flow for `CUST-SSN` |
| **C** | One-page COACTUPC business description |
| **D** | Missing paragraph 9999 — refuse, do not invent |

Prefer answering from `--english` / `--rules`. Do not re-parse COBOL source at query time.

---

## Phase 2 (ingestion — run once per corpus)

```powershell
# Single program
python phase2_english_worker.py --program COACTUPC

# Remaining incomplete programs (long-running)
powershell -File scripts\run_phase2_remaining.ps1
```

Writes only `:english:` and `:rules:` keys. Never overwrites L0.

---

## A/B/C comparison harnesses (optional)

| File | Role |
|------|------|
| `docker-compose-harness-a.yml` | **A** — no Redis COBOL dict (partner baseline) |
| `docker-compose-harness-b.yml` | **B** — L0 IR + re-interpret at query time |
| `docker-compose-harness-c.yml` | **C** — L1 English GET only (product path) |
| `docs/EXPERIMENT-QUESTIONS.md` | 10 shared questions + rubric |
| `experiment_runner.py` | Batch runner (`hermes chat -Q`) |

```powershell
# List harnesses / questions / L1 coverage
python experiment_runner.py --list

# Smoke only (safe anytime Redis is up)
python experiment_runner.py --smoke --harness c

# Full suite — ONLY after L1 ≥95% and partner approval
# python experiment_runner.py --harness a,b,c
```

Results land in `experiment/results/run_*.jsonl`. Score with the rubric; runner does not auto-PASS.

---

## Boundaries (do not cross)

| Do | Do not |
|----|--------|
| GET Redis keys | Embeddings / KNN / `FT.SEARCH` |
| Cite keys and `[seq N]` from docs | Invent missing paragraphs |
| Use Honcho for **session** memory | Treat Honcho as COBOL IR source of truth |
| Run Phase 2 offline for new English | Re-generate English on every chat turn |
| Keep `data/canonical` immutable in alpha | Re-run full extraction for partner demo |

---

## Key docs

| Doc | Purpose |
|-----|---------|
| `docs/ENGLISH-BUSINESS-LOGIC-ENGINE.md` | Product architecture |
| `docs/ENGLISH-QUALITY-EVAL.md` | Prompt 3 + Tests A–D |
| `docs/PLAN-SUMMARY-AND-NEXT-STEPS.md` | Roadmap |
| `docs/REDIS-FIDELITY-AUDIT.md` | L0 integrity evidence |
| `docs/EXPERIMENT-QUESTIONS.md` | A/B/C question bank |
| `CLAUDE.md` / `README.md` | Repo orientation |

---

## Support contacts / ops

- Redis health: `docker exec cobol-ir-db redis-cli -a cobol123 ping`
- Manifest: `py translations/ir_query.py --raw cobol:manifest`
- Hermes stop-before-update: `tmp/mtp-cleanup/stop_hermes_for_update.ps1`
- MTP model ensure: `tmp/mtp-cleanup/ensure_mtp_loaded.ps1`

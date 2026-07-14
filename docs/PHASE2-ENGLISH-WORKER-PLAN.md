# Living Plan — Phase 2 English Ingestion Worker

**Status:** **COMPLETE** — Steps 1–10; see `docs/PHASE2-COMPLETION-REPORT.md`. Commit proposed under Morty Law (not auto-executed).  
**Created:** 2026-07-14  
**Worker script:** `phase2_english_worker.py` (written, not yet executed)  

---

## Step tracker

| Step | Title | Status |
|------|--------|--------|
| 1 | Read contracts | **DONE** |
| 2 | Confirm L0 populated | **DONE** — paragraph_count 518, DBSIZE 1130 |
| 3 | LLM call strategy | **DONE** — MTP + `/api/v1/chat/completions` |
| 4 | Write `phase2_english_worker.py` | **DONE** — await review before run |
| 5 | Dry-run COACTUPC | **DONE** — 85 WOULD, DBSIZE 1130 unchanged |
| 6 | Pilot one paragraph | **DONE** — 1200 written; word_count 868 (over 500 target) |
| 7 | Test D | **DONE — PASS** (known GET full; 9999 → nil) |
| 8 | Full COACTUPC | **DONE** — 84 DONE / 1 SKIP / 0 FAIL; eng=85 rules=85 |
| 9 | ir_query L1 flags | **DONE** — --english / --rules; no :para: fallback |
| 10 | Report (no full 31-program run) | **DONE** — PHASE2-COMPLETION-REPORT.md |

---

## Step 2 result

- `cobol:manifest` paragraph_count **518**, program_count **31**
- DBSIZE **1130** ≥ 1130 ✅

## Step 3 result

| Item | Value |
|------|--------|
| Model | `Qwen3.6-35B-A3B-MTP-GGUF` (health model_loaded; hermes config) |
| Alt name in .env | `user.Qwen3.6-35B-A3B-MTP-GGUF` — prefer non-`user.` id matching health |
| Base URL | `http://127.0.0.1:8000/api/v1` |
| Completions path | **`/api/v1/chat/completions`** (append to base) |

## Step 4

Script at repo root: `phase2_english_worker.py` — show to Mark before dry-run.

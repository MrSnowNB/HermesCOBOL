# Temporary Plan — MTP Model Cleanup & Gated Validation

**Status:** COMPLETE — 9/9 gates PASS (`gates/RESULTS.json`)  
**Created:** 2026-07-14  
**Completed:** 2026-07-14T16:00:25Z  
**Scope:** Remove leftover non-MTP Qwen3.6-35B-A3B so only MTP is the chat 35B path.  
**Artifact root:** `C:\work\HermesCOBOL\tmp\mtp-cleanup\`  
**Proof:** `PROOF.md`  
**This file is temporary** — not part of the product; safe to delete after review.

---

## Goal

Prove that the dual-load of:

- `Qwen3.6-35B-A3B-MTP-GGUF` (correct)
- `Qwen3.6-35B-A3B-GGUF` (stale non-MTP)

is eliminated, and that Hermes / Lemonade / HermesCOBOL configs all pin **MTP only** for the 35B chat model.

**In scope:** Lemonade registry + load state, Hermes `config.yaml` model pin, HermesCOBOL `.env`, recipe_options leftovers, validation artifacts.  
**Out of scope:** Honcho deriver model (intentionally `Hermes-3-Llama-3.1-8B-GGUF`), nomic embeddings, other user models (27B, gemma).

---

## Target end state

| Component | Required |
|-----------|----------|
| Lemonade `all_models_loaded` LLMs | MTP 35B + Hermes-3 only (no non-MTP 35B) |
| Lemonade `model_loaded` | `Qwen3.6-35B-A3B-MTP-GGUF` (or empty/other non-35B non-MTP) |
| Lemonade `/api/v1/models` | **No** `Qwen3.6-35B-A3B-GGUF` without `MTP` |
| `user_models.json` | **No** `Qwen3.6-35B-A3B-GGUF` key |
| `recipe_options.json` | **No** `user.Qwen3.6-35B-A3B-GGUF` key |
| `~/.hermes/config.yaml` | `model.default` = MTP id; provider custom → Lemonade |
| `HermesCOBOL/.env` | `OPENAI_MODEL` / `LEMONADE_CHAT_MODEL` = MTP |

---

## Steps

| Step | Action | Gate |
|------|--------|------|
| 0 | Create artifact dir + backups | G0 |
| 1 | Capture baseline telemetry | G1 |
| 2 | Unload/delete non-MTP from Lemonade if resident | G2 |
| 3 | Scrub `user_models.json` / `recipe_options.json` | G3 |
| 4 | Pin Hermes `config.yaml` to MTP | G4 |
| 5 | Verify HermesCOBOL `.env` MTP | G5 |
| 6 | Run automated gate script → `gates/RESULTS.json` | G6–G9 |
| 7 | Write `PROOF.md` with telemetry excerpts | G10 |

---

## Gates (pass/fail)

| Gate | Assertion | Artifact |
|------|-----------|----------|
| **G0** | Backups exist under `backups/` | file list |
| **G1** | Baseline health JSON written | `gates/01-baseline-health.json` |
| **G2** | Non-MTP absent from `all_models_loaded` | health after unload |
| **G3** | Non-MTP absent from user_models + recipe_options | greps |
| **G4** | Hermes config contains MTP default, no non-MTP default | config snapshot |
| **G5** | HermesCOBOL `.env` MTP only for chat model | env snapshot |
| **G6** | Catalog: zero models matching `Qwen3.6-35B-A3B-GGUF` without `MTP` | models list |
| **G7** | Loaded LLMs: only allowed set (MTP 35B, Hermes-3) | health |
| **G8** | Completion probe with MTP succeeds (HTTP 200) | `gates/08-mtp-completion.json` |
| **G9** | Completion/request with bare non-MTP id fails (404 or not loaded) | `gates/09-nonmtp-negative.json` |
| **G10** | `PROOF.md` + `gates/RESULTS.json` all pass | final |

---

## Rollback

Restore files from `tmp/mtp-cleanup/backups/`. Re-register non-MTP in Lemonade UI only if intentionally needed.

---

## Execution log

| Step | Status | Notes |
|------|--------|-------|
| 0 Backups | DONE | 5 files under `backups/` |
| 1 Baseline | DONE | `gates/00-pre-cleanup-evidence.json`, `01-baseline-*` |
| 2 Unload/delete non-MTP | DONE | Lemonade DELETE 200; health no non-MTP |
| 3 Scrub registries | DONE | user_models clean; recipe_options key removed |
| 4 Pin Hermes config | DONE | MTP + auxiliary pins in `~/.hermes/config.yaml` |
| 5 HermesCOBOL .env | DONE | Already MTP; verified |
| 6 Automated gates | DONE | `run_gates.py` → 9/9 PASS exit 0 |
| 7 PROOF.md | DONE | This package |

**Final validation command:** `python tmp/mtp-cleanup/run_gates.py` → exit 0.

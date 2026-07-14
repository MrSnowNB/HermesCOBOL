# PROOF — MTP-only Qwen cleanup complete

**Verdict: ALL GATES PASSED (9/9)**  
**Run timestamp (UTC):** `2026-07-14T16:00:25.769890+00:00`  
**Machine:** Windows host with Lemonade 10.6.0 + Hermes agent  

**Artifact root:** `C:\work\HermesCOBOL\tmp\mtp-cleanup\`  
**Machine-readable results:** `gates/RESULTS.json`  
**Human summary table:** `gates/RESULTS.md`

---

## 1. What was wrong (pre-cleanup telemetry)

Documented before cleanup in `gates/00-pre-cleanup-evidence.json` and live investigation:

| Issue | Evidence |
|-------|----------|
| Both 35B variants resident in VRAM | Lemonade health listed `Qwen3.6-35B-A3B-MTP-GGUF` **and** `Qwen3.6-35B-A3B-GGUF` (backend `:8004`) |
| Non-MTP registered as user model | `~/.cache/lemonade/user_models.json` key `Qwen3.6-35B-A3B-GGUF` |
| Non-MTP recipe options | `recipe_options.json` key `user.Qwen3.6-35B-A3B-GGUF` |
| Hermes aux still named non-MTP | Agent log: `Auxiliary title_generation: using custom (user.Qwen3.6-35B-A3B-GGUF)` |
| Hermes had no model pin | `~/.hermes/config.yaml` only skin/TTS |

---

## 2. What we changed

| Action | Target |
|--------|--------|
| DELETE non-MTP from Lemonade | `POST /api/v1/delete` + `/api/v0/delete` body `{"model_name":"Qwen3.6-35B-A3B-GGUF"}` → `"Deleted model: Qwen3.6-35B-A3B-GGUF"` (`gates/02-unload-delete-attempts.txt`) |
| Scrub recipe_options | Removed `user.Qwen3.6-35B-A3B-GGUF` (`gates/03-recipe_options-after.json`) |
| Confirm user_models clean | No non-MTP key (`gates/03-user_models-after.json`) |
| Pin Hermes | `~/.hermes/config.yaml` → `model.default: Qwen3.6-35B-A3B-MTP-GGUF`, provider `custom`, base `http://127.0.0.1:8000/api/v1`, aux pins for vision/compression/title (`gates/04-hermes-config-after.yaml`) |
| HermesCOBOL env | Already MTP — verified (`gates/05-HermesCOBOL.env.snapshot`) |
| Backups | `backups/*` (G0) |

**Not changed (by design):** Honcho deriver stays on `Hermes-3-Llama-3.1-8B-GGUF`; nomic embeddings stay loaded.

---

## 3. Gate results (authoritative)

| Gate | Result | Proof artifact |
|------|--------|----------------|
| G0 Backups | **PASS** | `backups/` (5 files) |
| G2 No non-MTP loaded | **PASS** | `gates/06-live-health.json` / RESULTS |
| G3 Registry scrubbed | **PASS** | `gates/03-*-after.json` |
| G4 Hermes config pinned | **PASS** | `gates/04-hermes-config-after.yaml` |
| G5 HermesCOBOL .env | **PASS** | `gates/05-HermesCOBOL.env.snapshot` |
| G6 Catalog no non-MTP 35B | **PASS** | `gates/06-live-models.json` |
| G7 Loaded LLM allowlist | **PASS** | health: MTP + Hermes-3 only |
| G8 MTP completion works | **PASS** | `gates/08-mtp-completion.json` |
| G9 Non-MTP cannot complete | **PASS** | `gates/09-nonmtp-negative.json` |

Full JSON: `gates/RESULTS.json` → `"all_pass": true`, `"passed": 9`, `"failed": 0`.

---

## 4. Telemetry excerpts (post-cleanup)

### 4a. Loaded models (health)

From gate G2/G7 detail:

```text
model_loaded: Qwen3.6-35B-A3B-MTP-GGUF
all_loaded:
  - nomic-embed-text-v2-moe-GGUF     (embedding)
  - Qwen3.6-35B-A3B-MTP-GGUF         (llm)   ← ONLY 35B chat
  - Hermes-3-Llama-3.1-8B-GGUF       (llm)   ← Honcho deriver (intentional)
non_mtp_loaded: []
```

Checkpoint for MTP (from `02-post-unload-health.json`):

```text
unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf
backend: http://127.0.0.1:8002/v1
```

**Before:** non-MTP also on `:8004` with `unsloth/Qwen3.6-35B-A3B-GGUF:Q4_K_M`.  
**After:** that process is gone.

### 4b. Catalog

G6: `non_mtp_ids: []`, `mtp_present: true`.  
Related 35B catalog entries now only: `Qwen3.5-35B-A3B-GGUF` (different product) + `Qwen3.6-35B-A3B-MTP-GGUF`.  
**No** `Qwen3.6-35B-A3B-GGUF`.

### 4c. Positive completion (MTP live)

`gates/08-mtp-completion.json`:

- HTTP **200**
- Requested model: `Qwen3.6-35B-A3B-MTP-GGUF`
- Response model field: underlying GGUF `Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf` (MTP checkpoint)
- Timings show **draft_n / draft_n_accepted** (MTP multi-token prediction path active):

```json
"timings": {
  "draft_n": 45,
  "draft_n_accepted": 44,
  "predicted_n": 64
}
```

(Assistant used reasoning tokens; gate accepts non-empty `reasoning_content` as proof of live inference.)

### 4d. Negative (stale non-MTP blocked)

`gates/09-nonmtp-negative.json`:

| Request model | Result |
|---------------|--------|
| `user.Qwen3.6-35B-A3B-GGUF` | **HTTP 404** `model_not_found` |
| `Qwen3.6-35B-A3B-GGUF` | No successful completion (timeout / not served as chat) |

Quoted 404 body:

```text
Model 'user.Qwen3.6-35B-A3B-GGUF' was not found.
requested_model: user.Qwen3.6-35B-A3B-GGUF
type: model_not_found
```

### 4e. Hermes pin

`gates/04-hermes-config-after.yaml` contains:

```yaml
model:
  default: "Qwen3.6-35B-A3B-MTP-GGUF"
  provider: "custom"
  base_url: "http://127.0.0.1:8000/api/v1"
auxiliary:
  title_generation:
    model: "Qwen3.6-35B-A3B-MTP-GGUF"
  compression:
    model: "Qwen3.6-35B-A3B-MTP-GGUF"
```

### 4f. HermesCOBOL `.env`

```text
OPENAI_MODEL=user.Qwen3.6-35B-A3B-MTP-GGUF
LEMONADE_CHAT_MODEL=user.Qwen3.6-35B-A3B-MTP-GGUF
```

---

## 5. How to re-verify anytime

```powershell
cd C:\work\HermesCOBOL
python tmp\mtp-cleanup\run_gates.py
# expect exit 0 and gates/RESULTS.json "all_pass": true
```

Or one-liner health check:

```powershell
(Invoke-RestMethod http://127.0.0.1:8000/api/v1/health).all_models_loaded.model_name
# must NOT include Qwen3.6-35B-A3B-GGUF without MTP
```

---

## 6. Residual notes (not failures)

1. **Hermes process** already running may need a **restart** to pick up `config.yaml` for live sessions (file on disk is proven correct; in-memory process may still hold old settings until restart).  
2. **Honcho** still loads Hermes-3 by design — not a dual-Qwen issue.  
3. **Qwen3.5-35B-A3B-GGUF** remains in Lemonade’s built-in catalog (different model family); gates only forbid **Qwen3.6-35B-A3B non-MTP**.  
4. Bare `Qwen3.6-35B-A3B-GGUF` completion sometimes **times out** rather than instant 404; still does not return successful non-MTP chat output (G9 pass).

---

## 7. Rollback

Restore from `tmp/mtp-cleanup/backups/` if needed, then re-add the non-MTP model in Lemonade UI only if intentionally required.

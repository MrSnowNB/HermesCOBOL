# Experiment run 20260715T170600Z — partial results & failure analysis

**Status:** Stopped by operator for handoff (not a full 30-cell finish)  
**Run ID:** `20260715T170600Z`  
**Model:** `Qwen3.6-35B-A3B-MTP-GGUF` (Lemonade / Hermes custom provider)  
**Timeout:** 600s per cell  
**Local artifacts (gitignored):** `experiment/results/run_20260715T170600Z/`  

---

## Scoreboard at stop

| Metric | Value |
|--------|------:|
| Cells finished | **12 / 30** |
| Runner `ok` (rc=0) | **9** |
| Runner FAIL | **3** (all **timeout**, rc=-1, 600s) |
| Interrupted | **B Q03** mid-flight (no `meta.json`) |
| Harness C | **0 / 10** (not started) |

### Per-cell

| Seq | Cell | Title | Result | Sec | Notes |
|-----|------|-------|--------|-----|-------|
| 1 | A Q01 | Paragraph purpose | rc=0 | 24 | **Quality FAIL** — Hermes asked for clarification instead of answering |
| 2 | A Q02 | Business rules SSN | rc=0 | 58 | Short; weak grounding (expected without IR) |
| 3 | A Q03 | Field data flow CUST-SSN | rc=0 | 23 | |
| 4 | A Q04 | Program summary | rc=0 | 32 | |
| 5 | A Q05 | Hallucination trap | rc=0 | 31 | |
| 6 | **A Q06** | Decision routing | **TIMEOUT** | 600 | See failures below |
| 7 | A Q07 | Signed amount validation | rc=0 | 258 | Long but finished |
| 8 | A Q08 | End-to-end update path | rc=0 | 93 | |
| 9 | A Q09 | SSN edge cases | rc=0 | 14 | |
| 10 | A Q10 | COBSWAIT honesty | rc=0 | 87 | |
| 11 | **B Q01** | Paragraph purpose | **TIMEOUT** | 600 | 30KB tool/verbose stdout; IR tool loop |
| 12 | **B Q02** | Business rules SSN | **TIMEOUT** | 600 | Agent drifted into writing `l0_benchmark.py` / clarify timeout |
| — | B Q03 | Field data flow | **INTERRUPTED** | — | User stop |
| — | B Q04–Q10 | — | not run | — | |
| — | C Q01–Q10 | — | not run | — | |

---

## Failure commentary

### 1. A Q06 — Decision routing (timeout)

- **Harness:** A (no Redis; baseline)
- **Question:** After map edit, how does COACTUPC decide next action? Which paragraph owns the decision?
- **Symptom:** `returncode=-1`, `elapsed_sec=600`, stderr timeout marker; stdout ~1KB (not a huge tool dump).
- **Interpretation:** Even without IR tools, Hermes spent the full budget (verbose mode / multi-step agent loop) and never returned a clean final answer within 600s.
- **Product lesson:** Baseline can still thrash. Timeout is an **execution** fail, not proof of wrong business logic.
- **Retry:** Raise timeout to 900–1200s **or** constrain Hermes toolsets / max turns for harness A.

### 2. B Q01 — Paragraph purpose (timeout)

- **Harness:** B (L0 IR GET + re-interpret at query time)
- **Question:** Business function of `1200-EDIT-MAP-INPUTS`
- **Symptom:** Full 600s; **~30KB stdout** with verbose tool/diff noise; stderr had Python `SyntaxWarning: invalid escape sequence '\w'` spam (tool path).
- **Interpretation:** Profile requires `ir_query.py` GETs. Agent entered a long tool-use loop (shell, review diff, etc.) and never closed within the runner budget. Partial work was in flight but **not** a finished BA answer.
- **Product lesson:** L0-at-query-time is **expensive and fragile** vs frozen L1 — this is exactly the comparison the experiment is meant to surface. 600s is often insufficient when Hermes has full shell toolsets.
- **Retry:** `--timeout 900`+; tighten profile to **only** allow `ir_query` / terminal for that script; consider `--no-verbose-hermes` to cut log bloat (keep runner audit).

### 3. B Q02 — Business rules SSN (timeout)

- **Harness:** B
- **Question:** Extract BRs from `1265-EDIT-US-SSN` as SHALL requirements with seq cites
- **Symptom:** 600s timeout; stdout shows Hermes **creating unrelated files** (`translations/l0_benchmark.py`, “clarify timed out after 120s”) instead of answering the BA question.
- **Interpretation:** Severe **task drift** — agent optimized for “benchmark L0 latency” rather than rule extraction. Runner correctly marks FAIL on wall-clock timeout.
- **Repo hygiene:** Side-effect files under `translations/l0_benchmark.py`, `tests/test_l0_ir_query_time.py`, `tests/timing_results/`, and `experiments/` may be **agent debris** from this cell — do not treat as intentional product without review.
- **Retry:** Stronger system constraint (“do not write new project files; only run ir_query and answer”); optional yolo/tool allowlist.

### 4. Quality note on A Q01 (rc=0 but weak)

Several harness A cells returned rc=0 with **meta-chat** (“what do you want me to do with this harness?”) rather than a business answer. For partner scoring, treat these as **rubric FAIL** even when the runner shows OK. Runner only measures process success, not answer quality (`docs/EXPERIMENT-QUESTIONS.md`).

### 5. Incomplete suite (not a cell fail)

- **18 cells remaining:** B Q03–Q10 + all of C  
- **Stop reason:** Operator handoff to another machine  
- Handoff files (local only): `HANDOFF.md`, `PROGRESS_AT_STOP.json` under the run directory  

---

## Root-cause summary

| Theme | Detail |
|-------|--------|
| Timeout budget | 600s too low for Hermes+tools on L0 path |
| Tool surface | Full Hermes tools encourage loops / file writes |
| Prompt framing | Profile+QUESTION sometimes parsed as meta-instructions (esp. A) |
| Inference-at-query (B) | Costly; timeouts support product thesis favoring L1 GET |
| L1 path (C) | Untested this run — highest priority on resume |

---

## Recommendations for resume (other machine)

1. **`--timeout 900`** (or 1200) for B and C.  
2. Prefer completing **C first** once Redis L1 is available (product path).  
3. Retries: `a/Q06`, `b/Q01`, `b/Q02` with constrained tools.  
4. Score with `docs/EXPERIMENT-QUESTIONS.md`; do not equate runner OK with rubric PASS.  
5. Copy local `experiment/results/run_20260715T170600Z/` — **not** in git (see `.gitignore`).  

```powershell
python experiment_runner.py --harness c --timeout 900 --verbose
python experiment_runner.py --harness b --questions Q03,Q04,Q05,Q06,Q07,Q08,Q09,Q10 --timeout 900
```

---

## Related code/docs in this commit

- `experiment_runner.py` — auditable `run_<id>/` layout, verbose RUN.log, cell packs  
- `experiment/README.md` — artifact map  
- `scripts/monitor_experiment*.ps1` — 10-minute stall recovery helpers  
- `docs/EXPERIMENT-QUESTIONS.md` — rubric  
- `docs/PARTNER-QUICKSTART.md` — partner entry  

---

## One-line takeaway

> Failures so far are **timeouts and agent drift on L0/tool-heavy paths**, not Redis data loss; L1 (harness C) was never reached — completing C is the next evidence milestone for the “inference at ingestion” claim.

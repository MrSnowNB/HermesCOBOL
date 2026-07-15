# Experiment — Harness A / B / C

Comparison experiment for the COBOL → English business-logic engine.

| Harness | Meaning |
|---------|---------|
| **A** | Baseline: LLM only, no Redis COBOL dictionary |
| **B** | L0 IR GET + re-interpret at query time |
| **C** | L1 English/rules GET only (product path) |

## Files

| Path | Role |
|------|------|
| `profiles/{a,b,c}/AGENTS.md` | Per-harness agent rules |
| `questions.json` | Machine-readable Q01–Q10 |
| `results/` | Runner output (`run_*.jsonl`) |
| `../docker-compose-harness-{a,b,c}.yml` | Stack contracts |
| `../docs/EXPERIMENT-QUESTIONS.md` | Rubric |
| `../experiment_runner.py` | Batch runner |

## Do not run full suite until

1. Phase 2 L1 coverage ≥ 95% (`python experiment_runner.py --list`)
2. Smoke passes: `python experiment_runner.py --smoke --harness c`
3. Explicit user confirmation to execute A/B/C experiment

# Phase 2 Completion Report — English Ingestion Worker (COACTUPC pilot)

**Date:** 2026-07-14  
**Gate:** Docker alpha Phase 2 (COACTUPC only — full 31-program corpus deferred)  
**Status:** **COMPLETE**  

Living plan: `docs/PHASE2-ENGLISH-WORKER-PLAN.md`  
Run log: `docs/phase2_coactupc_run.log`

---

## 1. COACTUPC paragraph count processed

| Metric | Value |
|--------|--------|
| `COACTUPC:index` length | **85** |
| Paragraphs attempted | **85** |
| Model | `Qwen3.6-35B-A3B-MTP-GGUF` |
| Base URL | `http://127.0.0.1:8000/api/v1` |
| Timeout | 180s / paragraph |
| Workers | 1 |

---

## 2. DONE / SKIP / FAIL / ERROR counts

```text
Phase 2 complete: 85 paragraphs attempted
DONE: 84  SKIP: 1  FAIL: 0  ERROR: 0
L1 keys written: 168 (84 english + 84 rules)
Elapsed: 26m 22s
```

| Status | Count | Notes |
|--------|-------|--------|
| DONE | 84 | New L1 writes this production run |
| SKIP | 1 | `1200-EDIT-MAP-INPUTS` (pilot already present) |
| FAIL | 0 | No timeouts |
| ERROR | 0 | No LLM/Redis errors |

**Effective L1 coverage:** 85 english + 85 rules (pilot + production run).

---

## 3. DBSIZE before and after Phase 2

| When | DBSIZE |
|------|--------|
| Before full COACTUPC run (after pilot) | **1132** |
| After full COACTUPC run | **1300** |
| Delta | **+168** (= 84 × 2 keys) |

L0 IR keys untouched. Write path only `:english:` / `:rules:`.

---

## 4. Sample `:english:` — `1200-EDIT-MAP-INPUTS` (first 20 lines of document)

**Provenance:**

```json
{
  "paragraph": "1200-EDIT-MAP-INPUTS",
  "program": "COACTUPC",
  "source_key": "COACTUPC:para:1200-EDIT-MAP-INPUTS",
  "ir_schema_version": "1.4",
  "generator_id": "phase2_english_worker/v1",
  "generated_at": "2026-07-14T18:14:38.011681+00:00",
  "model_id": "Qwen3.6-35B-A3B-MTP-GGUF",
  "word_count": 868
}
```

**Document head:**

```text
01|PARAGRAPH: 1200-EDIT-MAP-INPUTS
02|PROGRAM: COACTUPC
03|SOURCE LINES: [3734, 3982]
04|
05|PURPOSE (2-3 sentences):
06|This paragraph orchestrates the validation of new account and customer data provided during an edit transaction. It ensures that all mandatory fields meet format and business constraints before allowing the update to proceed. The logic isolates invalid data by setting specific error flags for downstream processing.
07|
08|PRECONDITIONS:
09|The system must have access to the new account details and customer information via the program communication area. The `ACUP-DETAILS-NOT-FETCHED` flag determines if initial account retrieval logic is required.
10|
11|BUSINESS LOGIC (numbered steps):
12|1. Initialize the input status to valid and check if account details need fetching; if so, perform account retrieval and reset old data [seq 209-212].
13|2. If no search criteria were provided, mark the process as having no criteria and exit immediately [seq 213-215].
14|3. Confirm that the account and customer are found in the master file and set their validity flags to true [seq 217-221].
15|4. Compare old and new data; if no changes are detected, clear non-key flags and exit [seq 222-225].
16|5. Validate the new account status as a Yes/No value and store the result [seq 226-230].
17|6. Validate the new open date format and store the validation flags [seq 231-234].
18|7. Validate the new credit limit as a signed number and store the validation flags [seq 235-238].
19|8. Validate the new expiry date format and store the validation flags [seq 239-242].
20|9. Validate the new cash credit limit as a signed number and store the validation flags [seq 243-246].
```

Full blob also in `docs/phase2_pilot_english_1200.json`.

**Quality note:** `word_count` 868 exceeds the Prompt 3 400-word budget (known gap; content structure and seq cites are present).

---

## 5. Sample `:rules:` — `1265-EDIT-US-SSN` (all BRs)

```json
{
  "paragraph": "1265-EDIT-US-SSN",
  "program": "COACTUPC",
  "rules": [
    {
      "id": "BR-1",
      "text": "The system SHALL validate that the first three characters of the SSN contain only numeric digits [seq 587].",
      "seq": 587
    },
    {
      "id": "BR-2",
      "text": "The system SHALL validate that the fourth and fifth characters of the SSN contain only numeric digits [seq 600].",
      "seq": 600
    },
    {
      "id": "BR-3",
      "text": "The system SHALL validate that the last four characters of the SSN contain only numeric digits [seq 605].",
      "seq": 605
    },
    {
      "id": "BR-4",
      "text": "The system SHALL set the global INPUT-ERROR flag to TRUE if any SSN segment fails numeric validation [seq 592].",
      "seq": 592
    },
    {
      "id": "BR-5",
      "text": "The system SHALL record specific failure flags for each SSN segment (Part 1, Part 2, Part 3) in the edit flags storage [seq 593, 601, 606].",
      "seq": null
    }
  ],
  "source_key": "COACTUPC:para:1265-EDIT-US-SSN",
  "ir_schema_version": "1.4",
  "generator_id": "phase2_english_worker/v1",
  "generated_at": "2026-07-14T18:30:26.801739+00:00",
  "model_id": "Qwen3.6-35B-A3B-MTP-GGUF"
}
```

---

## 6. Test D (missing key)

| Probe | Result |
|-------|--------|
| `GET COACTUPC:english:1200-EDIT-MAP-INPUTS` | Full JSON present |
| `GET COACTUPC:english:9999-NONEXISTENT` | **nil** / null — no invented document |

---

## 7. `ir_query.py --english` / `--rules` tests

```text
# L1 English
py translations/ir_query.py COACTUPC 1200-EDIT-MAP-INPUTS --english
→ Layer: english
→ Key: COACTUPC:english:1200-EDIT-MAP-INPUTS
→ Method: GET
→ document starts with PARAGRAPH: 1200-EDIT-MAP-INPUTS

# L1 Rules
py translations/ir_query.py COACTUPC 1200-EDIT-MAP-INPUTS --rules
→ Key: COACTUPC:rules:1200-EDIT-MAP-INPUTS
→ rules: 10

# Missing L1 (no silent :para: fallback)
py translations/ir_query.py COACTUPC 9999-NONEXISTENT --english
→ L1 key not found — run phase2_english_worker.py
→ exit 1
```

---

## 8. Failures

**None.** FAIL: 0, ERROR: 0, no timeouts at 180s.

SKIP only: `1200-EDIT-MAP-INPUTS` (pre-existing pilot; intentional).

---

## Artifacts delivered

| File | Role |
|------|------|
| `phase2_english_worker.py` | Phase 2 batch generator |
| `translations/ir_query.py` | L0 + L1 GET (`--english` / `--rules`) |
| `docs/phase2_coactupc_run.log` | Full production run log |
| `docs/phase2_pilot_english_1200.json` | Pilot english sample |
| `docs/phase2_pilot_rules_1200.json` | Pilot rules sample |
| `docs/PHASE2-ENGLISH-WORKER-PLAN.md` | Living plan |
| `docs/PHASE2-COMPLETION-REPORT.md` | This report |

---

## Proposed commit (Morty Law — not auto-committed)

**Message:**

```text
Phase 2 English worker + ir_query L1 GET support
```

**Suggested paths to include:**

```text
phase2_english_worker.py
translations/ir_query.py
docs/PHASE2-ENGLISH-WORKER-PLAN.md
docs/PHASE2-COMPLETION-REPORT.md
docs/phase2_coactupc_run.log
docs/phase2_pilot_english_1200.json
docs/phase2_pilot_rules_1200.json
```

Also related product docs if not yet committed:

```text
docs/ENGLISH-BUSINESS-LOGIC-ENGINE.md
docs/ENGLISH-QUALITY-EVAL.md
docs/CANONICAL-REDIS-DICT-PLAN.md
docs/CANONICAL-REDIS-MIGRATION-REPORT.md
docker-compose-cobol-db.yml
ingest_redis_canonical.py
archive/vector_experiment/*
```

---

## Alpha gate status

| Gate | Status |
|------|--------|
| Phase 1 L0 Redis dictionary | **DONE** (31 programs / 518 paras) |
| Phase 2 L1 English/rules for **COACTUPC** | **DONE** (85/85) |
| Query path GET-only L1 | **DONE** (`ir_query --english/--rules`) |
| Fail closed on missing L1 | **DONE** |
| Full 31-program Phase 2 corpus | **Deferred** (separate decision) |

**Phase 2 COACTUPC pilot quality gate: PASSED** (with known word-count overshoot on some paragraphs).

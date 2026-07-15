# Experiment Questions — Harness A / B / C Comparison

**Status:** Scaffolding only — **do not run** `experiment_runner.py` full suite until
Phase 2 L1 coverage ≥95% and smoke tests pass.  
**Date:** 2026-07-14  
**Primary program:** COACTUPC (flagship; richest statement IR + L1 pilot)  
**Scoring:** human or rubric PASS/FAIL per harness; runner stores raw answers only.

---

## Design

| Harness | Data path | Inference |
|---------|-----------|-----------|
| **A** | No Redis COBOL dictionary | LLM re-interprets at query time (partner baseline) |
| **B** | Redis L0 `:para:` / `:meta:` / `:index` | LLM re-interprets IR at query time |
| **C** | Redis L1 `:english:` / `:rules:` | Inference at ingestion; query is GET-only |

Same 10 questions × 3 harnesses = 30 runs. Same model preferred for fairness.

---

## Questions (Q01–Q10)

### Q01 — Paragraph purpose (Prompt 3 core)

```
What business function does COACTUPC paragraph 1200-EDIT-MAP-INPUTS perform?
Answer in plain English for a business analyst. No code dumps.
```

| Rubric | PASS if |
|--------|---------|
| A | May be vague or wrong; honest uncertainty OK |
| B | Grounded in L0 GET of `COACTUPC:para:1200-EDIT-MAP-INPUTS` |
| C | Uses L1 `COACTUPC:english:1200-EDIT-MAP-INPUTS`; cites key |

---

### Q02 — Business rules (Test A)

```
From COACTUPC paragraph 1265-EDIT-US-SSN, extract every business rule
as a numbered requirement: "BR-N: The system SHALL …"
Source each rule with a seq citation if available.
```

| Rubric | PASS if |
|--------|---------|
| A | Unverified estimates labeled, or refusal |
| B | Rules from IR statements/conditions; `[seq …]` when present |
| C | Rules from L1 `:rules:` or `:english:`; no invented BRs |

---

### Q03 — Field data flow (Test B)

```
Explain to a non-technical business analyst what COMMAREA field CUST-SSN
does in COACTUPC. Which paragraphs read or write it, and what business
event triggers each access? No COBOL syntax in the prose.
```

| Rubric | PASS if |
|--------|---------|
| B/C | Names real paragraphs from IR/English; field label CUST-SSN OK |
| A | Likely invents flow — fail if claims specific paras without caveat |

---

### Q04 — Program summary (Test C)

```
Write a one-page business description of COACTUPC:
- What business process does it implement?
- What are the 5 most important paragraphs and what does each do?
- What external systems does it interact with?
- What data does it own vs receive?
No code. Cite paragraph names.
```

| Rubric | PASS if |
|--------|---------|
| B | Used `:meta` / `:index` GET |
| C | English docs or meta; coherent process narrative |
| A | Generic credit-card boilerplate without COACTUPC-specific paras → FAIL |

---

### Q05 — Hallucination trap (Test D)

```
What does COACTUPC paragraph 9999-NONEXISTENT-PARA do?
Retrieve evidence first. If missing, do not invent business logic.
```

| Rubric | PASS if |
|--------|---------|
| All | Refuses / reports not found — **does not invent** logic for 9999 |
| C | Explicit L1 miss message preferred |

---

### Q06 — Decision / routing

```
In COACTUPC, after map inputs are edited, how does the program decide
what action to take next? Which paragraph owns that decision, and what
business outcomes can result?
```

Expected anchor: `2000-DECIDE-ACTION` (and related).

---

### Q07 — Numeric / signed validation

```
What business rules apply when COACTUPC validates a required signed
decimal amount (paragraph 1250-EDIT-SIGNED-9V2 or equivalent)?
List constraints a BA would put in a requirements doc.
```

---

### Q08 — Cross-paragraph chain

```
Describe the end-to-end business path when a user updates account data
on the COACTUPC screen: from receiving the map, through validation,
decision, and write-back. Name the key paragraphs in order.
```

Expected anchors include: `1100-RECEIVE-MAP`, `1200-EDIT-MAP-INPUTS`,
`2000-DECIDE-ACTION`, `9600-WRITE-PROCESSING` (and related).

---

### Q09 — Risk / edge cases

```
What edge cases or risks should a developer not miss in
COACTUPC 1265-EDIT-US-SSN (blank vs null, short-circuit, partial SSN)?
Use only retrieved evidence.
```

---

### Q10 — Missing L1 / offline honesty (multi-harness stress)

```
What does COBSWAIT paragraph MAIN do as a business process?
If you cannot retrieve documentation or IR, say so explicitly.
```

| Rubric | PASS if |
|--------|---------|
| A | Admits no dictionary / estimates |
| B | L0 GET result (COBSWAIT may have 0 paras — report empty) |
| C | L1 miss or empty program handled without fabrication |

---

## Machine-readable list

See `experiment/questions.json` (same IDs/text for the runner).

---

## Scoring sheet (fill after run)

| Q | A | B | C | Notes |
|---|---|---|---|-------|
| Q01 | | | | |
| Q02 | | | | |
| Q03 | | | | |
| Q04 | | | | |
| Q05 | | | | **Must PASS all** for alpha honesty |
| Q06 | | | | |
| Q07 | | | | |
| Q08 | | | | |
| Q09 | | | | |
| Q10 | | | | |

**Gate:** Q05 FAIL on any harness blocks partner claim for that harness.  
**Product win condition:** C ≥ B ≥ A on grounded accuracy; C wins on refusal discipline for missing keys.

# English Quality Evaluation — Acid Burn Prompts & Test Suite

**Status:** Active eval contract for English documentation engine  
**Date:** 2026-07-14  
**Agent persona:** COBOL **business analyst**, not code translator  
**Ground truth:** Redis L0 IR (`cobol-ir-db`) via exact GET  

**Non-negotiable:** Every English fact traces to a specific IR **`seq`** (or to an explicit IR field when no seq applies, e.g. meta). Format: `[seq N]` or `[seq N-M]`.

---

## Setup (before any prompt)

```powershell
cd C:\work\HermesCOBOL
docker compose -f docker-compose-cobol-db.yml up -d
# L0 must be loaded
python ingest_redis_canonical.py   # if empty
py translations/ir_query.py --raw COACTUPC:para:1200-EDIT-MAP-INPUTS
```

Working directory for Hermes tools: **`C:\work\HermesCOBOL`**.  
Use: `py translations/ir_query.py …` (not bare `python ir_query.py` unless PATH is set).

---

## Prompt 3 (revised) — Paragraph → English business document

**Replace any prior “translate to Python” Prompt 3 with this.**

```
You are a COBOL business analyst, not a code translator.

Retrieve COACTUPC:para:1200-EDIT-MAP-INPUTS from Redis:
  py translations/ir_query.py COACTUPC 1200-EDIT-MAP-INPUTS --raw

Then produce a structured English business logic document with these sections:

PARAGRAPH: [name]
PROGRAM: COACTUPC
SOURCE LINES: [from IR source_lines field]

PURPOSE (2-3 sentences):
  What business function does this paragraph perform?
  Not what the code does — what the BUSINESS does.

PRECONDITIONS:
  What must be true before this paragraph runs?
  (from cfg predecessors and reads fields)

BUSINESS LOGIC (numbered steps):
  For each logical group of statements, one plain-English sentence.
  Do NOT translate line by line — group by intent.
  Cite the seq range for each step: [seq 209-211]

BUSINESS RULES (bullet list):
  Explicit rules embedded in the logic — conditions, validations,
  constraints. These are the sentences that belong in a requirements doc.

DATA FLOW:
  READS: [field names from IR reads array]
  WRITES: [field names from IR mutates array]
  CALLS: [paragraphs from IR performs array]

EDGE CASES AND RISKS:
  What would a developer miss if they didn't read this carefully?
  Any short-circuit logic, implicit defaults, blank-vs-null distinctions?

Keep the total output under 400 words. Do not show code.
Every fact must trace to the Redis IR — cite [seq N] for each rule.
```

### Pass criteria (Prompt 3)

| Check | Pass if |
|-------|---------|
| Retrieval | Tool ran exact GET; key `COACTUPC:para:1200-EDIT-MAP-INPUTS` |
| No code | No Python/COBOL source dumps |
| Structure | All sections present |
| Seq cites | Business logic steps and rules cite `[seq N]` or `[seq N-M]` |
| Length | ≤ ~400 words |
| Business voice | PURPOSE is business function, not “moves fields” |

---

## Tier 2 — English quality tests

### Test A — Business rule extraction

```
From COACTUPC:para:1265-EDIT-US-SSN, extract every business rule
as a numbered requirement statement.
Format each as: "BR-[N]: The system SHALL [rule]"
Source each rule with its seq number.
```

| Check | Pass if |
|-------|---------|
| GET first | Shows retrieval of `COACTUPC:para:1265-EDIT-US-SSN` |
| Format | `BR-n: The system SHALL …` |
| Seq | Every BR has `[seq …]` |
| No code | No COBOL verb dumps as the answer body |

---

### Test B — Data flow plain English

```
Explain to a non-technical business analyst what COMMAREA field
CUST-SSN does in the COACTUPC program.
Which paragraphs read it, which write it, in what order, and what
business event triggers each access?
Use only Redis IR data — no code, no COBOL syntax in the answer.
```

| Check | Pass if |
|-------|---------|
| IR-only claim | Uses Redis IR (para/meta/index; scan performs/reads/mutates) |
| Audience | Non-technical language |
| No COBOL syntax | No PIC/MOVE/PERFORM in the prose (names like CUST-SSN OK as field labels) |
| Traceability | Cites paragraph keys `[COACTUPC:para:…]` and/or seq where statements exist |

---

### Test C — Program summary

```
Retrieve COACTUPC:meta and COACTUPC:index from Redis.
Write a one-page business description of the COACTUPC program:
- What business process does it implement?
- What are the 5 most important paragraphs and what does each do?
- What external systems does it interact with?
- What data does it own vs what does it receive?
No code. Plain English. Cite paragraph names as [COACTUPC:para:NAME].
```

| Check | Pass if |
|-------|---------|
| GET meta + index | Explicit retrieval shown |
| Structure | Four bullets addressed |
| Citations | `[COACTUPC:para:NAME]` form |
| No code | Pass |

---

### Test D — Hallucination trap (unchanged intent)

```
What does COACTUPC paragraph 9999-NONEXISTENT-PARA do?
Attempt Redis GET first, show the result, do not infer if key missing.
```

| Check | Pass if |
|-------|---------|
| GET attempted | Key miss shown (or SCAN candidates without inventing the para) |
| No inference | Does **not** invent business logic for 9999 |
| Refusal | Clear “does not exist / not in IR” |

---

## Scoring rubric (session log)

| Test | PASS / FAIL | Notes / evidence |
|------|-------------|------------------|
| Prompt 3 (1200 English doc) | | |
| A (1265 BRs) | | |
| B (CUST-SSN data flow) | | |
| C (COACTUPC one-pager) | | |
| D (9999 trap) | | |

**Session alpha gate:** D must PASS; Prompt 3 + A recommended PASS before claiming English quality.

---

## Docker alpha — production pipeline (inference at ingestion)

```
Phase 1 — Offline, deterministic (DONE)
  COBOL source → canonical IR JSON → Redis :para: / :meta: / :index

Phase 2 — First load (LLM-assisted, one-time per paragraph)
  Redis IR → Hermes English generation (Prompt 3) → SET :english: / :rules:
  Frozen artifacts — NOT re-generated per user query

Query time — Zero IR reinterpretation
  User question → GET :english: or :rules: → answer
  Hermes may synthesize across multiple stored keys only
  Never re-interpret raw :para: into new business meaning at query time
  Test D: missing key → show miss, do not invent
```

| Phase | When | Inference? | Status |
|-------|------|------------|--------|
| 1 | Offline / image build | None | **Done** (L0) |
| 2 | First load / IR change | Once per paragraph | **Not built** (Prompt 3 = generator template) |
| Query | Every partner question | GET + multi-key synthesis only | L0 GET works; L1 keys empty until Phase 2 |

**Prompt 3 is an ingestion-time generator**, not the production query path.  
Acid Burn runs Prompt 3 today to **validate English quality**; production must **SET** `:english:` / `:rules:` and answer only from those keys at query time.

---

## Related

- Product thesis: `docs/ENGLISH-BUSINESS-LOGIC-ENGINE.md`  
- Redis migration: `docs/CANONICAL-REDIS-MIGRATION-REPORT.md`  
- Agent startup contract: `C:\work\hermes-agent\AGENTS.md`  

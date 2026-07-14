# Product Thesis — COBOL → English Business Logic Documentation Engine

**Status:** Architecture locked (product direction)  
**Date:** 2026-07-14  
**Related:** Redis dictionary (`cobol-ir-db`), `data/canonical/`, inference boundary  

---

## What we are building

**Not** a COBOL-to-Python compiler.  
**Yes** a **COBOL-to-English business logic documentation engine** where the LLM is the **consumer and querier**, not the executor of business logic.

| Wrong product | Right product |
|---------------|---------------|
| Generate Python that re-implements paragraphs | Generate **auditable English** that describes purpose, rules, data flow, calls |
| LLM executes / simulates at query time from fuzzy memory | LLM **GETs pre-materialized docs** (and can cite IR underneath) |
| Success = code compiles | Success = SME / LLM can answer “what if SSN is blank?” from stored English |

Python translation (`translations/`) remains an **optional side product** for demos/regression—not the primary alpha deliverable for partners.

---

## Output shape (target English document)

Per paragraph (example: `1200-EDIT-MAP-INPUTS`):

```text
PARAGRAPH: 1200-EDIT-MAP-INPUTS
PROGRAM: COACTUPC
SOURCE LINES: [from IR source_lines]
PURPOSE: business function (not “what the code does”)
PRECONDITIONS: …
BUSINESS LOGIC: numbered steps, grouped by intent — each cites [seq N-M]
BUSINESS RULES: requirements-style bullets with [seq N]
DATA FLOW: READS / WRITES / CALLS from IR arrays
EDGE CASES AND RISKS: short-circuit, blank-vs-null, …
```

**Seq provenance rule:** every English sentence (or rule) that asserts a behavior must cite a specific IR **`seq`** number (or range). No orphan claims.

Canonical eval prompts: **`docs/ENGLISH-QUALITY-EVAL.md`** (Prompt 3 + Tests A–D).

---

## Production pipeline — inference at ingestion, not at query time

**Key insight:** Partners’ stacks run expensive, error-prone interpretation on **every query**. We run it **once** when IR is loaded, freeze the result, and at query time only **GET** (plus light multi-key synthesis).

```
Phase 1 — Offline, deterministic (no LLM)
  COBOL source → extractors → data/canonical/*.canonical.json
       → ingest_redis_canonical.py → Redis {PROG}:para:{NAME}  (+ meta/cfg/index)

Phase 2 — First load / IR version change (LLM-assisted, one-time per paragraph)
  Redis :para: → Hermes English generation (Prompt 3 schema, [seq N] cites)
       → Redis {PROG}:english:{NAME}
       → Redis {PROG}:rules:{NAME}
  Stored as fixed artifacts. Not re-generated per user question.

Query time — Zero interpretation of raw IR
  User question → GET :english: and/or :rules: (and maybe :meta / :index)
  Hermes may synthesize across multiple stored keys (e.g. several paragraphs)
  Hermes must NOT re-interpret :para: into new business meaning at query time
  Missing L1 key → run Phase 2 for that paragraph (or fail closed), not invent
```

| When | What | Inference? |
|------|------|------------|
| Phase 1 | Parse COBOL → IR dict | **None** (deterministic) |
| Phase 2 | IR → English / rules | **Once per paragraph / IR version** |
| Query | GET + route / multi-key synthesis | **No IR reinterpretation** |

**Lossless + auditable:** English is *derived* from IR with `[seq N]` provenance; IR remains ground truth. Wrong English → re-run Phase 2 for that key only.

---

## Redis key schema (three layers)

Container: `cobol-ir-db` · port `6380` · password `cobol123`

| Layer | Key pattern | Role | Writer |
|-------|-------------|------|--------|
| **L0 IR** | `{PROG}:para:{NAME}` | Parsed structured IR (source of truth in Redis) | `ingest_redis_canonical.py` only |
| **L0 meta/cfg** | `{PROG}:meta`, `:cfg:…`, `:index`, `cobol:manifest` | Navigation | same |
| **L1 English** | `{PROG}:english:{NAME}` | Full natural-language paragraph document | English generator (future) |
| **L1 Rules** | `{PROG}:rules:{NAME}` | Extracted business rules only (query-dense) | English generator (future) |

```
COACTUPC:para:1200-EDIT-MAP-INPUTS       ← raw parsed IR
COACTUPC:english:1200-EDIT-MAP-INPUTS    ← generated English document
COACTUPC:rules:1200-EDIT-MAP-INPUTS      ← business rules only
```

### Write permissions

| Store | Hermes agent | Batch generator | IR loader |
|-------|--------------|-----------------|-----------|
| `:para:` / meta / cfg | **READ only** | no | **WRITE** |
| `:english:` / `:rules:` | **READ only** (prefer for Q&A) | **WRITE** (versioned) | no |
| Honcho session memory | read/write (conversation) | optional | no |

Agents **must not** overwrite IR or English keys ad-hoc during chat.

---

## Inference boundary (updated)

1. **Below the line (deterministic):** COBOL → extractors → `data/canonical/` → Redis `:para:`  
2. **On the line (ingestion-time inference only):** `:para:` → English generator → `:english:` / `:rules:` (**once**, frozen)  
3. **Above the line (query time):** **GET only** of English/rules; optional multi-key synthesis; **never** re-read raw IR to invent new business meaning

Query-time path for “What does 1200 do?”:

```text
1. GET COACTUPC:english:1200-EDIT-MAP-INPUTS   # required for production path
2. If miss → Phase 2 generate-and-store, then GET again (or fail closed in strict mode)
3. Do NOT free-form reinterpret :para: as a substitute for stored English
4. Cite keys used (:english: / :rules: primary; :para: only for audit if asked)
```

---

## Generation contract (for implementers)

When building the English generator:

1. **Input:** only Redis `:para:` (and optional layout/CFG keys)—not free-form chat history.  
2. **Output:** fixed template sections (PURPOSE, BUSINESS LOGIC, DATA FLOW, RULES, CALLS).  
3. **Provenance fields** in every English/rules JSON or markdown blob:
   - `source_key`, `ir_schema_version`, `generator_id`, `generated_at`, `model_id` (if LLM used)
4. **Idempotent:** re-run overwrites with new version stamp; keep IR unchanged.  
5. **Validation gates:** every PERFORM target named exists in `:index`; every READ/WRITE field string appears in IR or layout when available.  
6. **Seq cites:** every BUSINESS LOGIC step and BUSINESS RULE cites `[seq N]` or `[seq N-M]` present in the source `:para:` payload.

---

## Docker alpha — two-phase pipeline

```
Phase 1 — Offline (once)
  COBOL → parse → data/canonical/ → Redis :para: / :meta: / :index     [DONE]
  (later) batch Prompt-3 style generation → :english: / :rules:

Phase 2 — Online (every query)
  GET :english: or :rules:  (preferred)
  else GET :para: + analyst prompt with [seq N] cites
  Hallucination trap: missing key → refuse (Test D)
```

Until L1 keys are batch-loaded, session-time Prompt 3 materializes English from L0 IR.

---

## Relationship to existing code

| Asset | Role under this thesis |
|-------|------------------------|
| `data/canonical/` | Disk IR truth |
| `ingest_redis_canonical.py` | L0 materializer (**done**) |
| `translations/ir_query.py` | L0 GET client — extend for `:english:` / `:rules:` |
| `translations/coactupc_*.py` | Optional Python port demos — **not** primary product |
| Honcho | Session memory / skills — not business-rule SoT |
| Partner Docker alpha | Phase 1 + Phase 2 on first boot; query path GET-only |

---

## Next implementation slices (not done yet)

1. Spec English + rules JSON/Markdown schemas (+ seq provenance)  
2. **Ingestion worker:** for each `:para:` missing `:english:`, run Prompt 3, `SET` english/rules  
3. Extend `ir_query.py`: `--english` / `--rules` GET  
4. Hermes skill: query path **only** hits L1; Phase 2 is a load job, not chat  
5. Gate: regenerate L1 when IR content hash changes  
6. Docker entrypoint: wait for Redis → load L0 → enqueue Phase 2 → health when L1 complete (or progressive)

---

## One-line partner pitch

> Inference runs once at ingestion—not on every query. We freeze English business docs from a deterministic IR dictionary; at query time the system only retrieves them. Partners re-interpret COBOL with stacked models on every request—we already did that work offline and locked the answer.

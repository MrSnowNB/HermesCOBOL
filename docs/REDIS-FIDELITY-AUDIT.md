# REDIS DICTIONARY FIDELITY AUDIT — HermesCOBOL

**Date:** 2026-07-14  
**Scope:** L0 Redis (`cobol-ir-db`) vs `data/canonical/*.canonical.json`  
**Mode:** Query-only (no Redis writes, no LLM inference)  
**Overall verdict:** **PASS**  
**Ready for Phase 2 English generation:** **YES** (already run for COACTUPC; audit confirms L0 foundation)

---

```
╔══════════════════════════════════════════════════════╗
║  REDIS DICTIONARY FIDELITY AUDIT — HermesCOBOL      ║
║  Date: 2026-07-14                                    ║
╚══════════════════════════════════════════════════════╝
```

## MANIFEST

| Field | Expected | Found |
|-------|----------|--------|
| Programs expected / found | 31 / 31 | **31 / 31** |
| Paragraphs expected / found | 518 / 518 | **518 / 518** |
| Schema version | `"1.4"` | **`"1.4"`** |
| Store | `canonical-ir-dictionary` | **`canonical-ir-dictionary`** |
| DBSIZE | ≥ 1130 | **1300** (L0 + COACTUPC L1 english/rules; L0 alone was 1130) |

`cobol:manifest` JSON is valid and consistent with program list totals.

---

## STEP 1 — Key schema confirmed

| Pattern | Confirmed |
|---------|-----------|
| `{PROG}:para:{NAME}` | Yes |
| `{PROG}:index` | Yes |
| `{PROG}:meta` | Yes |
| `cobol:manifest` | Yes |
| Also in live schema | `{PROG}:cfg:{NAME}`, `{PROG}:cfg:summary` |

Sources: `docs/ENGLISH-BUSINESS-LOGIC-ENGINE.md`, `translations/ir_query.py`, live manifest `redis_key_schema`.

---

## PROGRAM INDEX COMPLETENESS (Step 3)

| Program | Redis :index | Disk canonical | Match? |
|---------|--------------|----------------|--------|
| CBACT01C | 16 | 16 | ✓ |
| CBACT02C | 5 | 5 | ✓ |
| CBACT03C | 5 | 5 | ✓ |
| CBACT04C | 22 | 22 | ✓ |
| CBCUS01C | 5 | 5 | ✓ |
| CBEXPORT | 21 | 21 | ✓ |
| CBIMPORT | 16 | 16 | ✓ |
| CBSTM03A | 25 | 25 | ✓ |
| CBSTM03B | 14 | 14 | ✓ |
| CBTRN01C | 18 | 18 | ✓ |
| CBTRN02C | 26 | 26 | ✓ |
| CBTRN03C | 26 | 26 | ✓ |
| **COACTUPC** | **85** | **85** | ✓ |
| COACTVWC | 34 | 34 | ✓ |
| COADM01C | 8 | 8 | ✓ |
| COBIL00C | 16 | 16 | ✓ |
| COBSWAIT | 0 | 0 | ✓ |
| COCRDLIC | 39 | 39 | ✓ |
| COCRDSLC | 9 | 9 | ✓ |
| COCRDUPC | 13 | 13 | ✓ |
| COMEN01C | 7 | 7 | ✓ |
| CORPT00C | 10 | 10 | ✓ |
| COSGN00C | 6 | 6 | ✓ |
| COTRN00C | 16 | 16 | ✓ |
| COTRN01C | 9 | 9 | ✓ |
| COTRN02C | 18 | 18 | ✓ |
| COUSR00C | 16 | 16 | ✓ |
| COUSR01C | 9 | 9 | ✓ |
| COUSR02C | 11 | 11 | ✓ |
| COUSR03C | 11 | 11 | ✓ |
| CSUTLDTC | 2 | 2 | ✓ |
| **TOTAL** | **518** | **518** | ✓ |

- Programs with perfect match: **31 / 31**  
- Programs with mismatch: **none**  
- Missing/extra paragraph names: **none**

---

## CONTENT SPOT CHECK (Step 4)

Programs checked: **5**  
Fields verified per paragraph: **9** (with notes where disk lacks enrichment fields)

| Program | First :index paragraph | Status |
|---------|------------------------|--------|
| COACTUPC | 0000-MAIN | **PASS** |
| CBACT01C | 0000-ACCTFILE-OPEN | **PASS** |
| CBCUS01C | 0000-CUSTFILE-OPEN | **PASS** |
| CBTRN02C | 0000-DALYTRAN-OPEN | **PASS** |
| COTRN01C | CLEAR-CURRENT-SCREEN | **PASS** |

Mismatches on structural fields shared by disk + Redis (`name`, `last_verb`, `terminator`, `reachable`, `performs` count): **none**.

**Note (not a fidelity failure):** Redis COACTUPC paragraphs may carry **statement-level enrichment** (`statements[]`, `source_lines`, `reads`, `mutates`, `statement_count`) from Honcho Load Manifest v2. Disk `data/canonical/*.canonical.json` is structural schema 1.4 without per-statement arrays. Enrichment is **additive** on Redis; it does not corrupt or diverge structural fields.

---

## STATEMENT INTEGRITY — COACTUPC (Step 5)

| Check | Result |
|-------|--------|
| Paragraphs checked | **85** |
| Missing keys | **0** |
| Count mismatches (`statement_count` vs `statements[]` when both set) | **0** |
| Seq ordering issues | **0** |
| Missing verb/raw | **0** |
| Paragraphs with `statements[]` present | **39 / 85** (non-EXIT enriched units) |
| Overall | **PASS** |

---

## BUSINESS LOGIC QUERIES (Step 6)

IR-only answers (no LLM inference).

### Q1 — Entry point — **PASS**

| | |
|--|--|
| Keys | `COACTUPC:meta`, `COACTUPC:para:0000-MAIN` |
| Fields | index[0], `reachable` |
| Answer | First paragraph is **`0000-MAIN`** (`:index[0]`, key exists, `reachable=true`). Meta has no separate `entry_point` field. |

### Q2 — Call graph for 1200 — **PASS**

| | |
|--|--|
| Key | `COACTUPC:para:1200-EDIT-MAP-INPUTS` |
| Fields | `performs[]` (empty in structural IR), `statements[]` PERFORMs |
| Answer | `performs[]` is **[]** on both disk-shaped IR and Redis structural fields. **Statement enrichment** lists PERFORM targets including **`1210-EDIT-ACCOUNT`**, `1205-COMPARE-OLD-NEW`, edit helpers, etc. Business call graph is recoverable from `statements[]` without LLM. |

### Q3 — First write in 1200 — **PASS**

| | |
|--|--|
| Key | `COACTUPC:para:1200-EDIT-MAP-INPUTS` |
| Fields | `statements[0]` |
| Answer | **seq 209**, verb **SET**, raw **`SET INPUT-OK TO TRUE`** — first logical write targets **INPUT-OK**. |

### Q4 — 0000-MAIN reachable — **PASS**

| | |
|--|--|
| Key | `COACTUPC:para:0000-MAIN` |
| Field | `reachable` |
| Answer | **true** |

### Q5 — 1200 terminator — **PASS**

| | |
|--|--|
| Key | `COACTUPC:para:1200-EDIT-MAP-INPUTS` |
| Fields | `terminator`, `falls_through_to` |
| Answer | **`terminator=implicit`**, **`falls_through_to=1200-EDIT-MAP-INPUTS-EXIT`** (fall-through, not STOP RUN). |

---

## CROSS-PROGRAM ISOLATION (Step 7)

| Metric | Value |
|--------|--------|
| Programs with paragraph name `0000-MAIN` | **3** (COACTUPC, COACTVWC, COCRDLIC) |
| Isolation check | **PASS** |

Most programs use different entry names (e.g. `0000-ACCTFILE-OPEN`), not `0000-MAIN`. Each `0000-MAIN` is stored under a **program-prefixed key** (`{PROG}:para:0000-MAIN`). Retrieval never crosses programs.

| Program | source_lines | stmts | last_verb | terminator |
|---------|--------------|-------|-----------|------------|
| COACTUPC | [3164, 3325] | 47 | GO TO | goto |
| COACTVWC | None | 0 | GO TO | goto |
| COCRDLIC | None | 0 | GO TO | goto |

COACTUPC is distinct (enriched statements + source_lines). COACTVWC/COCRDLIC share structural signature but remain key-isolated.

---

## OVERALL VERDICT: **PASS**

**Ready for Phase 2 English generation: YES**

(Phase 2 for COACTUPC already completed successfully; this audit confirms L0 fidelity so scale-out of Phase 2 remains justified.)

---

## ISSUES REQUIRING ATTENTION

1. **Structural vs statement IR (documentation, not blocker):** Disk canonical is schema 1.4 structural; Redis COACTUPC includes optional statement enrichment. 1:1 fidelity holds for shared structural fields and for full paragraph name coverage. Statement arrays exist on **39/85** COACTUPC paragraphs only (by design of enrichment source).  
2. **`performs[]` often empty on structural IR** while PERFORM targets appear in `statements[]` — consumers needing call graphs should read statements when present, or re-derive from enrichment.  
3. **DBSIZE 1300** includes L1 English/rules for COACTUPC; pure L0 was 1130. Audit did not write any keys.

**None of the above are L0 fidelity failures against disk canonical index/content for shared fields.**

---

## Method notes

- No Redis writes during audit.  
- No LLM used for answers.  
- Hierarchy used: Redis L0 vs `data/canonical/` primary; business queries used Redis enrichment where structural fields alone were incomplete for call targets.  

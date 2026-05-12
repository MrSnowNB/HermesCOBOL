# AiFirst Protocol — HermesCOBOL Edition

> **Protocol Version:** `aifirst/3.0-hermes`
> **Status:** ACTIVE
> **Adapted from:** `aifirst/2.2` (CarDemo/Fractal_Claws origin)
> **Removed:** syncd toolchain, SYNC-MANIFEST.yaml, BRANCH-SCOPE.md, wave model
> **Scope:** HermesCOBOL deterministic COBOL extraction pipeline

---

## Core Mandate

Every non-trivial task must pass through the first-principles loop before
any file is touched. The scratchpad is the execution surface. The loop is
not optional. Symptoms are never the unit of work.

---

## Design Principles

- **Problem-frame first** — fill every field of PROBLEM FRAME in scratchpad.md
  before acting. If any field is "unknown" you are not ready.
- **First-principles decomposition** — what is the irreducible unit? What are
  its inputs, invariants, proof of correct, proof of wrong?
- **Evidence over memory** — every claim cites the exact command + output
  that proves it. "As I recall" is a protocol violation.
- **Halt-on-failure, re-decompose** — BLOCKED means rewrite PROBLEM FRAME,
  not patch the action. Never fix symptoms.
- **Scratchpad is ground truth** — if scratchpad CURRENT STATE disagrees
  with disk, fix scratchpad before doing anything else.
- **Frozen contracts are inviolable** — FROZEN GROUND TRUTH entries are
  never edited. Any action that would violate them halts immediately.
- **One action at a time** — CURRENT STATE always has exactly one NEXT ACTION.
  Not a list. One step.
- **Scope respect** — do not touch files outside the declared task scope.
  Out-of-scope edits are rolled back, not kept.

---

## The First-Principles Loop

```text
READ scratchpad
      ↓
Fill PROBLEM FRAME (all 8 fields — concrete, no hand-waving)
      ↓
      ├─ Any field is vague? → STOP. Investigate. Then re-fill.
      ↓
ACT (one step from NEXT ACTION)
      ↓
      ├─ PASS → update CURRENT STATE → set next NEXT ACTION → loop
      │
      └─ FAIL → write BLOCKED in CURRENT STATE
               → write REVISED ASSUMPTION
               → rewrite PROBLEM FRAME from scratch
               → DO NOT patch forward
               → DO NOT proceed until PROBLEM FRAME is complete again
```

**The critical rule:** BLOCKED always forces a PROBLEM FRAME rewrite.
Never a patch. This is what breaks the symptom-chasing loop.

---

## Gate Structure (lightweight, no syncd)

For HermesCOBOL tasks, the six-gate model is replaced with a
three-checkpoint model. Gate files live in `.clinerules/runs/<task_id>/`.

### G0 — DECOMPOSE
Fill PROBLEM FRAME in scratchpad. All 8 fields concrete.
**Pass criteria:** Human confirms the frame is correct.

### G1 — EXECUTE
Take the single NEXT ACTION. Update CURRENT STATE.
Repeat until PROBLEM FRAME is resolved.
**Pass criteria:** Proof of correct command returns expected output.

### G2 — COMMIT
Push to branch. Update scratchpad SESSION LOG.
Clear PROBLEM FRAME. Set status to IDLE.
**Pass criteria:** Git confirms push. Scratchpad updated.

---

## PROBLEM FRAME Fields (mandatory, all 8)

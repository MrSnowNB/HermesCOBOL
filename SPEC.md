# SPEC: Stage 5-H Phase 2 — Referential Integrity Rules for Canonical IR Paragraphs

**Version:** 1.0  
**Date:** 2026-05-18  
**Status:** Draft — awaiting explicit approval  
**Author:** Grok (following spec-writer protocol)  
**Related:** REVIEW.md (2026-05-13), previous Stage 5-H Phase 1 migration, validate_canonical_ir.py current stubs

---

## Intent (one sentence)

Implement the 3 stubbed referential integrity rules in `scripts/validate_canonical_ir.py` so that the Stage 5-H gate enforces semantic correctness of paragraph cross-references, not just field presence.

---

## Background

`validate_canonical_ir.py` currently validates structural presence of the six required paragraph fields (`name`, `terminator`, `falls_through_to`, `performs`, `goto_targets`, `reachable`) plus basic completeness and CICS/preprocess consistency.

Three semantic rules were intentionally left as stubs in `CONSISTENCY_RULES` / `PARAGRAPHS_RULES` after Phase 1:

1. **performs_referential_integrity**  
   Every name appearing in any paragraph’s `performs[]` array must resolve to a real paragraph name defined in the same program’s canonical IR.  
   (Current data shows 0 broken references, but no enforcement exists.)

2. **terminator_enum**  
   The `terminator` field on every paragraph must be exactly one of the eight documented legal values (see Implementation Requirements).  
   `None` / `null` / any other string is invalid.

3. **falls_through_to_referential_integrity**  
   When `falls_through_to` is non-null, the target name must exist as a paragraph in the same program.  
   `null` is always legal (last paragraph or explicit terminators).

These rules close the “known gaps” documented at the end of Phase 1 and make the canonical IR a trustworthy contract for downstream consumers (CobolProgramDict, walkers, semantic enrichment, etc.).

CICS structural-only programs (`cics_present=True` and `preprocess_available=False`) must also pass; their canonical records are already known to be well-formed in this regard.

---

## Implementation Requirements

- All three rules must be implemented **inside the existing `check_paragraphs()` / paragraph loop** in `validate_canonical_ir.py`.  
  **Do not** create new top-level helper functions for the rules themselves.

- Failure record rule names (exact):
  - `"performs_referential_integrity"`
  - `"terminator_enum"`
  - `"falls_through_to_referential_integrity"`

- All three failures must carry `severity: "error"`.

- Add the three rule names to the `PARAGRAPHS_RULES` set so that the grouped console output correctly shows `paragraphs=FAIL` when any violation occurs.

- **No exemptions** for CICS programs. The rules apply uniformly.

- The implementation must be placed so that the existing `_get_status_for_group` logic and summary reporting continue to work without modification.

- Single file changed: `scripts/validate_canonical_ir.py` only.

---

## Acceptance Criteria (all must be observable and pass)

**GATE 1 — Rule implementation check**  
`Select-String -Path scripts\validate_canonical_ir.py -Pattern "performs_referential_integrity"`  
Expected: at least 2 matches (one in `PARAGRAPHS_RULES`, one in a failure record).

**GATE 2 — Terminator enum check**  
`Select-String -Path scripts\validate_canonical_ir.py -Pattern "terminator_enum"`  
Expected: at least 2 matches.

**GATE 3 — falls_through_to check**  
`Select-String -Path scripts\validate_canonical_ir.py -Pattern "falls_through_to_referential_integrity"`  
Expected: at least 2 matches.

**GATE 4 — Stage 5-H gate run**  
`python scripts/validate_canonical_ir.py`  
Expected: `31/31 programs passed Stage 5-H` (all `PASS`).  
If any program reports `FAIL`, the full failure JSON for that program must be captured and the process halted for review.

**GATE 5 — Roundtrip validator (no regression)**  
`python scripts/validate_roundtrip.py`  
Expected: `Pass 31, Fail 0`.

**GATE 6 — Full test suite (no regression)**  
`python -m pytest tests/ -q --tb=short` (using the Python interpreter that contains the test environment)  
Expected: 136 passed.

**GATE 7 — Terminator value audit (diagnostic, not hard gate)**  
Run the exact one-liner audit script supplied in the request.  
Expected output: `ALL terminators valid`.  
If any invalid terminators are discovered, they must be reported immediately (do not treat as automatic failure of the SPEC; investigate with Mark).

---

## Out of Scope

- `check_cross_source_consistency()` remains a stub (not implemented or called).
- No work on `CobolProgramDict`, walkers, or semantic enrichment layers.
- No changes to `assemble_canonical.py`, `extract_facts.py`, `cobol_parse_utils.py`, `extract_cfg_local.py`, or any test file.
- No modification of any artifact under `data/cfg/`, `data/facts/`, `data/canonical/`, `data/fallthrough/`, or `validation/`.
- No CICS translator or semantic CICS enrichment.
- No updates to `SCRIPTS_INVENTORY.md` or documentation beyond what is required by the gates.

---

## Plan (execute in strict order)

1. **Draft & present this SPEC** (current step).  
   The SPEC is written and shown to the user. No source file has been read for editing.

2. **Await explicit approval.**  
   Do **not** read `scripts/validate_canonical_ir.py`, do **not** run any gate command, and do **not** make any code change until the user replies with “approved”, “go”, or “LGTM” (or supplies edits to this SPEC).

3. **On approval** — first read of the target file.  
   Read `scripts/validate_canonical_ir.py` (once) to locate the exact paragraph validation loop and the `PARAGRAPHS_RULES` constant.

4. **Implement the three rules** (single file only).  
   Add the three checks inside the existing paragraph iteration.  
   Add the three rule names to `PARAGRAPHS_RULES`.  
   Produce clean failure records with `severity: "error"` using the exact rule names listed above.  
   No new top-level functions for the rules.

5. **Run the verification gates in order** (only after the edit is complete and saved):
   - GATE 1–3 (Select-String / grep checks)
   - GATE 4 (`validate_canonical_ir.py`)
   - GATE 5 (`validate_roundtrip.py`)
   - GATE 6 (pytest)
   - GATE 7 (terminator audit)
   Capture full stdout/stderr for every command.

6. **Post-gate hygiene**  
   If all gates pass, capture `git diff scripts/validate_canonical_ir.py`.  
   Update the journal with a `kind: "decision"` entry.

7. **Hand-off for review (Morty Law)**  
   Present the diff + full transcripts of all seven gates to Mark.  
   **Never** run `git commit`, `git add`, or `git push` locally.  
   Only after explicit review sign-off may the exact commit message below be used.

---

## Risks & Mitigations

- **Risk:** The current canonical IR for one or more of the 31 programs actually contains a violation that Phase 1 did not catch (e.g., a stray `None` terminator or a `falls_through_to` pointing at a noise token that survived into the final list).  
  **Mitigation:** GATE 4 will surface it immediately. The SPEC explicitly instructs to stop and report the full failure JSON rather than “fix” data.

- **Risk:** CICS programs behave differently (empty `performs[]`, special terminators).  
  **Mitigation:** The request states that CICS records are already known-good; the uniform rule application is intentional and will be proven by GATE 4.

- **Risk:** The three new rules are added to `PARAGRAPHS_RULES` but the console formatting or summary logic breaks.  
  **Mitigation:** The rules are simple string membership checks identical to the existing ones (`missing_paragraph_fields`, etc.). The `_get_status_for_group` helper is unchanged.

- **Risk:** Someone later expects `check_cross_source_consistency()` to be implemented at the same time.  
  **Mitigation:** Explicitly listed in Out of Scope; the SPEC scope is deliberately narrow.

- **Risk:** Violating Morty Law by committing without review.  
  **Mitigation:** This SPEC, the Plan, and the final hand-off step all forbid local commit. The GitHub MCP `push_files` tool will also not be used until Mark approves.

---

## References

- User “SPEC REQUEST: Stage 5-H Phase 2” message (this document’s source of truth).
- [REVIEW.md](REVIEW.md) — documented the three gaps at Phase 1 close-out.
- `scripts/validate_canonical_ir.py` (current stubbed state — read only after approval).
- `data/canonical/*.canonical.json` (known-good artifacts produced by Phase 1).
- Previous Phase 1 migration SPEC and commit (`refactor(extract_cfg_local)...`).

---

## Approval

- [ ] SPEC reviewed for completeness and correctness.
- [ ] Explicit approval given (“approved”, “go”, or “LGTM”).
- Once approved, the implementing agent may read the target file and begin the edit.

---

*This SPEC was generated strictly from the detailed request supplied by the user. It adds the required policy scaffolding (structured sections, observable gates, explicit “do not read until approved” rule) while preserving every technical constraint and acceptance criterion verbatim.*

**Ready for your review.**  
Reply with **"approved"** (or edits) when you are satisfied. I will not read `validate_canonical_ir.py` or run any command that touches source until that signal.
# SPEC: Fix extract_fallthrough.py — END-* scope terminators leaking into falls_through_to field

**Version:** 1.0  
**Date:** 2026-05-18  
**Status:** Draft — awaiting explicit approval  
**Related Work:** Stage 5-H Phase 2 referential integrity rules (validate_canonical_ir.py), previous extract_cfg_local.py unification

---

## Intent (one sentence)

Fix `extract_fallthrough.py` so that COBOL scope terminators (END-STRING, END-REWRITE, and all other END-* tokens) are never written into the `falls_through_to` field of fallthrough output, by filtering candidate names through the authoritative `PARAGRAPH_NOISE` and `RESERVED_WORDS` sets from `cobol_parse_utils`.

---

## Background

The newly activated Stage 5-H Phase 2 referential integrity rules in `validate_canonical_ir.py` (specifically `falls_through_to_referential_integrity`) surfaced three real violations in the current corpus:

- CBACT04C: `1300-B-WRITE-TX` → `falls_through_to: END-STRING`
- CBSTM03A: `5000-CREATE-STATEMENT` → `falls_through_to: END-STRING`
- CBTRN02C: `2800-UPDATE-ACCOUNT-REC` → `falls_through_to: END-REWRITE`

Upstream audit (GATE 8) traced the root cause to `data/fallthrough/*.json` produced by `extract_fallthrough.py`. These `END-*` tokens are COBOL scope terminators (e.g., `END-STRING`, `END-REWRITE`, `END-PERFORM`, etc.) and are explicitly listed in `cobol_parse_utils.PARAGRAPH_NOISE`. They are never valid paragraph names.

A similar class of bug (weak local paragraph detection allowing noise tokens) was already fixed in `extract_cfg_local.py` by importing and using the authoritative filter sets from `cobol_parse_utils`. The same defensive pattern must now be applied to the `falls_through_to` assignment path(s) in `extract_fallthrough.py`.

The `terminator` field logic must remain untouched — only `falls_through_to` is in scope.

---

## Implementation Requirements

1. Add import to `extract_fallthrough.py` (after existing imports):
   ```python
   from cobol_parse_utils import PARAGRAPH_NOISE, RESERVED_WORDS
   ```

2. Locate every code path that assigns a value to `falls_through_to`. Before any candidate name is written into that field, apply the filter:
   ```python
   if candidate not in PARAGRAPH_NOISE and candidate not in RESERVED_WORDS:
       falls_through_to = candidate
   else:
       falls_through_to = None
   ```

3. The filter must be applied at **every** assignment site for `falls_through_to`. Do not patch only one location if the field is assigned in multiple places.

4. Do **not** alter terminator classification or any `terminator` field logic.

5. Single file changed only: `scripts/extract_fallthrough.py`.

---

## Acceptance Criteria (all 8 gates must pass — observable and repeatable)

**GATE 1 — Import present**  
`Select-String -Path scripts\extract_fallthrough.py -Pattern "PARAGRAPH_NOISE"`  
Expected: at least 2 matches (import line + at least one filter usage).

**GATE 2 — Regenerate fallthrough data**  
`python scripts/extract_fallthrough.py` (or with `--all` if supported)  
Expected: completes successfully, exit code 0, no errors.

**GATE 3 — Reassemble canonical IR**  
`python scripts/assemble_canonical.py`  
Expected: "31/31 complete", exit code 0.

**GATE 4 — Stage 5-H validation gate**  
`python scripts/validate_canonical_ir.py`  
Expected: **31/31 PASS**.  
The three previously failing programs (CBACT04C, CBSTM03A, CBTRN02C) must now report `paragraphs=OK`. Any new failures must be reported immediately and the process halted.

**GATE 5 — Roundtrip validator (no regression)**  
`python scripts/validate_roundtrip.py`  
Expected: Pass 31, Fail 0.

**GATE 6 — Full test suite (no regression)**  
`python -m pytest tests/ -q --tb=short` (using the Python that contains the test deps)  
Expected: 136 passed.

**GATE 7 — Verify END-* tokens gone from fallthrough data**  
Run the exact audit script provided in the request.  
Expected: `CLEAN — no noise tokens in any falls_through_to`

**GATE 8 — Confirm the 3 previously failing programs are now clean**  
Run the exact three-program verification script provided in the request.  
Expected:
```
CBACT04C: CLEAN
CBSTM03A: CLEAN
CBTRN02C: CLEAN
```

---

## Out of Scope

- No changes to `validate_canonical_ir.py`, `assemble_canonical.py`, `cobol_parse_utils.py`, `extract_cfg_local.py`, `extract_facts.py`, or any test file.
- No work on `CobolProgramDict`, CICS semantic enrichment, or `check_cross_source_consistency()`.
- No modification of existing `terminator` classification logic.
- No updates to data artifacts except those produced by running the approved gates.
- No changes to `SCRIPTS_INVENTORY.md` unless required by a later review step.

---

## Plan (execute only after explicit "approved")

1. **Present this SPEC** (current step). No source files have been read or modified for implementation.

2. **Await explicit approval.**  
   Do **not** read `scripts/extract_fallthrough.py` for editing, do **not** run any gate, and do **not** make any code change until the user replies with "approved", "go", or "LGTM" (or supplies edits).

3. **On approval** — first read of the target.  
   Read `scripts/extract_fallthrough.py` once to locate all `falls_through_to` assignment sites.

4. **Implement the fix** (single file only).  
   Add the required import.  
   Apply the `PARAGRAPH_NOISE` + `RESERVED_WORDS` filter at every location where a value is assigned to `falls_through_to`.  
   Leave all terminator logic untouched.

5. **Execute the 8 gates in strict order**, capturing full output for each:
   - GATE 1 (Select-String count)
   - GATE 2 (regenerate fallthrough)
   - GATE 3 (reassemble canonical)
   - GATE 4 (Stage 5-H validator)
   - GATE 5 (roundtrip)
   - GATE 6 (pytest)
   - GATE 7 (noise audit)
   - GATE 8 (three-program verification)

6. **Post-gate verification**  
   Capture `git diff scripts/extract_fallthrough.py`.  
   Confirm only the intended file was changed.

7. **Journal anchor** (`kind: "decision"` + `kind: "done"`).

8. **Review hand-off (Morty Law)**  
   Present the diff + complete transcripts of all 8 gates to Mark.  
   **Never** run `git commit`, `git add`, or `git push` locally.  
   Only after explicit review sign-off may the exact commit message below be used.

---

## Risks & Mitigations

- **Risk:** Multiple assignment sites for `falls_through_to` exist; missing one leaves the bug partially fixed.  
  **Mitigation:** The implementation requirement explicitly mandates checking **every** assignment path. The review will verify via diff + GATE 7/8.

- **Risk:** Filtering changes `falls_through_to` values for some paragraphs, which could theoretically affect downstream consumers.  
  **Mitigation:** The change is a correctness fix (removing invalid noise tokens). Gates 4–6 will prove no regression in the primary contracts. The three affected programs are expected to move from FAIL to PASS in GATE 4.

- **Risk:** The filter is applied too aggressively and incorrectly turns a legitimate (rare) paragraph name into `None`.  
  **Mitigation:** `PARAGRAPH_NOISE` and `RESERVED_WORDS` are the authoritative, already-vetted sets used everywhere else in the pipeline (including the recent `extract_cfg_local.py` fix). No real paragraph names should ever match them.

- **Risk:** Violating Morty Law by reading/editing before approval or committing without review.  
  **Mitigation:** This SPEC hard-codes the "wait for approved" gate and the "no local commit" rule in the Plan.

---

## References

- User SPEC REQUEST message (source of truth for all gates and constraints).
- Previous Stage 5-H Phase 2 work that exposed the three violations.
- `cobol_parse_utils.py` — `PARAGRAPH_NOISE` and `RESERVED_WORDS` definitions (the single source of truth).
- `extract_fallthrough.py` current logic (to be read only after approval).
- `data/fallthrough/*.json` (current noisy state).

---

## Approval

- [ ] SPEC reviewed for completeness and correctness.
- [ ] Explicit approval given ("approved", "go", or "LGTM").
- Once approved, the implementing agent may read `extract_fallthrough.py` and begin the fix.

---

*This SPEC was generated directly from the detailed request supplied by the user. It adds the required policy scaffolding (structured sections, 8 observable gates, explicit Morty Law constraints) while preserving every technical detail verbatim.*

**Ready for your review.**  
Reply with **"approved"** (or edits) when you are satisfied. I will not read `extract_fallthrough.py` or run any gate until that signal arrives.
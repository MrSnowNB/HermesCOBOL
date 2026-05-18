# SPEC: Fix extract_fallthrough.py — Filter noise tokens from internal paragraph list

**Version:** 1.0  
**Date:** 2026-05-18  
**Status:** Draft — awaiting explicit approval  
**Related:** Previous fallthrough noise fix (END-* in falls_through_to), Stage 5-H Phase 2 referential integrity, extract_cfg_local.py unification

---

## Intent (one sentence)

Filter `PARAGRAPH_NOISE` and `RESERVED_WORDS` at the point where paragraph names are added to the internal tracked list in `extract_fallthrough.py`, so that `data/fallthrough/` reports exactly 518 paragraphs (matching facts and canonical IR).

---

## Background

After the recent fix that prevented `END-*` scope terminators from being written into the `falls_through_to` field, `data/fallthrough/*.json` still contains 531 paragraph entries while `data/facts/` and the canonical IR correctly report 518.

The 13 extra entries are noise tokens (from `PARAGRAPH_NOISE` and `RESERVED_WORDS`) that the Pass-1 annotations are surfacing as "paragraphs". These are being added to the internal `first` / `last` / `ordered` structures in `extract_fallthrough.py`.

`PARAGRAPH_NOISE` and `RESERVED_WORDS` were already imported in the previous fix. The same filtering pattern successfully applied to `extract_cfg_local.py` must now be applied to the paragraph *detection / tracking* logic here (not just the `falls_through_to` assignment).

This is the final upstream cleanup needed before `CobolProgramDict` can treat the paragraph universe as stable.

---

## Implementation Requirements

- The import `from cobol_parse_utils import PARAGRAPH_NOISE, RESERVED_WORDS` is already present — do not duplicate it.
- Locate every place in `extract_fallthrough.py` where a paragraph name (from annotations) is added to a tracked collection (`first`, `last`, `ordered`, or the final output list).
- Add the guard before adding the name:
  ```python
  if name not in PARAGRAPH_NOISE and name not in RESERVED_WORDS:
      # add to tracked structure
  ```
- The filter must be applied at the **detection / collection** stage so that the final `paragraphs` array written to `data/fallthrough/<PROG>.json` contains only valid names.
- Do **not** change terminator classification logic.
- Do **not** change any other file.
- Single file changed: `scripts/extract_fallthrough.py` only.

---

## Acceptance Criteria

**GATE 1** — Regenerate fallthrough data  
`python scripts/extract_fallthrough.py --all`  
Expected: 31/31 complete, exit 0

**GATE 2** — Reassemble canonical IR  
`python scripts/assemble_canonical.py`  
Expected: 31/31 complete, exit 0

**GATE 3** — Stage 5-H validator  
`python scripts/validate_canonical_ir.py`  
Expected: 31/31 PASS

**GATE 4** — Roundtrip validator  
`python scripts/validate_roundtrip.py`  
Expected: Pass 31, Fail 0

**GATE 5** — Test suite  
`python -m pytest tests/ -q --tb=short` (using the Python that contains the test dependencies)  
Expected: 136 passed

**Verification** — Fallthrough paragraph count  
Run:
```python
import json, glob
total = sum(len(json.load(open(p)).get('paragraphs',[])) 
            for p in glob.glob('data/fallthrough/*.json'))
print(f'Total fallthrough paragraphs: {total}')
print('PASS' if total == 518 else f'FAIL — expected 518 got {total}')
```
Expected: `Total fallthrough paragraphs: 518` and `PASS`

---

## Out of Scope

- No changes to `validate_canonical_ir.py`, `assemble_canonical.py`, `cobol_parse_utils.py`, or any test file.
- No changes to `terminator` classification or `falls_through_to` filtering logic (already fixed).
- No work on `CobolProgramDict`.
- No updates to data artifacts except those produced by running the approved gates.

---

## Plan (execute only after explicit "approved")

1. Present this SPEC (current step). No source file has been read or modified.

2. **Await explicit approval.**  
   Do **not** read `scripts/extract_fallthrough.py`, do **not** run any gate, and do **not** make any code change until the user replies with "approved", "go", or "LGTM".

3. On approval — first read of the target.  
   Read `scripts/extract_fallthrough.py` to locate all sites where paragraph names from annotations are collected.

4. Implement the filter.  
   Add the `PARAGRAPH_NOISE` + `RESERVED_WORDS` guard at every paragraph detection / addition point so the final output list contains only clean names.

5. Execute the gates in order:
   - GATE 1 (`extract_fallthrough.py --all`)
   - GATE 2 (`assemble_canonical.py`)
   - GATE 3 (`validate_canonical_ir.py`)
   - GATE 4 (`validate_roundtrip.py`)
   - GATE 5 (pytest)
   - Final verification script

6. Capture `git diff` and full gate output.

7. Journal anchor (`kind: "decision"` + `kind: "done"`).

8. Review hand-off (Morty Law).  
   Present diff + complete gate transcripts.  
   **Never** run `git commit`, `git add`, or `git push`.  
   Use the exact commit message only after explicit review sign-off.

---

## Risks & Mitigations

- **Risk:** Filtering changes the `ordered` list and could affect C-5 source-order checks or downstream consumers of the fallthrough JSON.  
  **Mitigation:** The C-5 check operates on line numbers, not names. The canonical IR (the authoritative consumer) will continue to use facts for its paragraph list. Gates 3–5 will surface any regression.

- **Risk:** Some legitimate paragraph names in this corpus might accidentally match the noise sets (unlikely but possible).  
  **Mitigation:** The same filter sets have already been applied in `extract_cfg_local.py` and the previous fallthrough fix without removing real paragraphs. The verification gate will confirm we land at exactly 518.

- **Risk:** Violating Morty Law.  
  **Mitigation:** This SPEC explicitly requires waiting for "approved" before any read or edit.

---

## References

- User request message (this SPEC's source of truth).
- Previous fallthrough fix SPEC and implementation.
- `extract_cfg_local.py` (reference implementation of the filter pattern).
- `data/facts/` and `data/canonical/` (the 518-paragraph ground truth).

---

## Approval

- [ ] SPEC reviewed.
- [ ] Explicit approval given ("approved", "go", or "LGTM").
- Once approved, the agent may read `extract_fallthrough.py` and begin the fix.

---

*This SPEC follows the exact structure and constraints requested. All Morty Law requirements are embedded in the Plan.*

**Ready for your review.**  
Reply with **"approved"** when you are satisfied. No source files will be touched until then.
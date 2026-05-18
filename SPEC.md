# SPEC: Refactor extract_cfg_local.py to use authoritative paragraph extractor

**Version:** 1.0  
**Date:** 2026-05-13  
**Status:** Draft — awaiting approval  
**Related:** Stage 5-H Phase 1 close-out, REVIEW.md findings on duplicated paragraph detection

---

## Intent (one sentence)

Replace the ad-hoc, incomplete local `extract_paragraphs()` implementation inside `scripts/extract_cfg_local.py` with the authoritative filtering logic and constant sets from `cobol_parse_utils`, eliminating noise tokens (END-*, SECTION names, etc.) from the CFG paragraph lists while preserving source order and all existing reachability / flow analysis behaviour.

---

## Acceptance Criteria (all must be observable / testable)

- The local `def extract_paragraphs(text: str) -> list[str]:` (≈lines 67-82) is completely removed from `extract_cfg_local.py`.
- `from cobol_parse_utils import (extract_paragraphs as _extract_paragraphs_authoritative, PARAGRAPH_NOISE, RESERVED_WORDS)` is present after the config import.
- In `run_single()`, paragraph discovery now produces an ordered list by scanning the preprocessed source and filtering every candidate with `if name not in PARAGRAPH_NOISE and name not in RESERVED_WORDS` (no `sorted()`, source order preserved). The call site becomes `paras = list(...)` or equivalent ordered construction.
- Inside `analyze_flow()`, the inline paragraph detector applies the same `PARAGRAPH_NOISE + RESERVED_WORDS` filter before assigning `current_para`.
- After `python scripts/extract_cfg_local.py --all`:
  - `data/cfg/*.json` contain **zero** entries whose `name` is in the noise set used by `cobol_parse_utils.PARAGRAPH_NOISE` (verified by GATE 6 script).
  - Paragraph counts per program are equal to or smaller than before (only noise removed; no real paragraphs lost).
- `python scripts/assemble_canonical.py` succeeds and the resulting `data/canonical/*.canonical.json` are identical in their authoritative `paragraphs[]` lists (the 518 records) and in `cfg_paragraphs` content (now cleaner).
- `python scripts/validate_canonical_ir.py` → 31/31 PASS (gate_status PASS, no new failures).
- `python scripts/validate_roundtrip.py` → Pass 31, Fail 0.
- `python -m pytest tests/ -q --tb=short` → 136 passed (or the exact count present at start of session).
- The noise-verification one-liner prints exactly: `CLEAN — no noise tokens in any CFG paragraph list`.
- Only `scripts/extract_cfg_local.py` is modified (no other source, no data files committed, no docs except optional inventory note).
- SCRIPTS_INVENTORY.md may be lightly updated to note the unification (optional, non-blocking).

---

## Out of Scope

- Any change to `extract_cfg_summary.py` (the smojol path — REFERENCE only).
- Changes to `cobol_parse_utils.py`, `assemble_canonical.py`, validators, or tests.
- Adding unit tests for the new path (deferred).
- Updating `data/cfg/*.json` or `data/canonical/*` in git (they are gitignored outputs; regeneration is part of verification only).
- CICS semantic work, CobolProgramDict, or any Phase 2 referential integrity rules.
- Commit of the change (Morty Law: review by Mark required first; use project /commit if present).

---

## Plan (exact steps — follow in order)

1. **Draft / present this SPEC.md** (current step). Do not touch `extract_cfg_local.py` until user explicitly says "approved", "go", or equivalent.

2. **Read the two source files** to obtain exact line numbers and surrounding context for safe edit:
   - `scripts/extract_cfg_local.py` (full)
   - `scripts/cobol_parse_utils.py` (the three symbols being imported)

3. **Edit `scripts/extract_cfg_local.py`** (atomic, using search/replace or precise patch):
   - Add the three-line import block immediately after the existing `from config import ...` line.
   - Delete the entire local `def extract_paragraphs(...)` (the 15-line function).
   - In `run_single()`: replace the call and the construction of `paras` so that an **ordered** list is built by line scan, filtering each candidate name through the two authoritative frozensets. Do **not** use `set` iteration or `sorted()`.
   - In `analyze_flow()`: wrap the `current_para = m.group(1).upper()` assignment with the same `if name not in PARAGRAPH_NOISE and name not in RESERVED_WORDS` guard.
   - Verify the rest of the file (especially `analyze_flow` callers, reachability worklist, `run_single` output) still compiles and behaves identically for real paragraphs.

4. **Run the full gated verification protocol** (all six gates) using the safe-bash wrapper for every shell invocation:
   - GATE 1: `python scripts/extract_cfg_local.py --all`
   - GATE 2: `python scripts/assemble_canonical.py`
   - GATE 3: `python scripts/validate_canonical_ir.py`
   - GATE 4: `python scripts/validate_roundtrip.py`
   - GATE 5: `python -m pytest tests/ -q --tb=short`
   - GATE 6: the exact `python -c "..."` noise-cleanliness script provided in the migration request.
   - Capture full stdout/stderr for each. Any non-zero exit or unexpected output → BLOCK and do not proceed.

5. **Post-gate checks**:
   - Confirm only `scripts/extract_cfg_local.py` was edited (use `git status --porcelain` or equivalent, filtered).
   - (Optional) Add a one-line note to `scripts/SCRIPTS_INVENTORY.md` under the `extract_cfg_local.py` entry: "Paragraph detection now delegates to `cobol_parse_utils` filter sets (unified with facts / data_flow)."
   - Run `python scripts/schema.py` (as required by CLAUDE.md after facts-related changes — even though CFG is not facts, it is good hygiene).

6. **Journal & hand-off**:
   - Append a `kind: "decision"` + `kind: "done"` anchor via journal-anchor skill describing the successful migration + gate results.
   - Do **not** run `git commit`, `git add`, or any commit-proposing command.
   - Present the diff (`git diff scripts/extract_cfg_local.py`) and the six gate transcripts to Mark for review.
   - Only after explicit approval + review sign-off may a commit message be proposed (the exact message supplied in the request is the candidate).

---

## Risks & Mitigations

- **Risk: Paragraph count drops for some programs** (noise was previously counted as paragraphs).  
  **Mitigation:** Acceptance criteria explicitly allow "equal or smaller". The canonical authoritative list (from facts) is unchanged; only `cfg_paragraphs` and internal CFG structures become cleaner. Reachability for real paragraphs is unaffected because the worklist and `analyze_flow` still see the same real names.

- **Risk: Source-order changes** if the new filter logic is implemented incorrectly (e.g. using set).  
  **Mitigation:** The plan mandates "build the ordered list by scanning lines ... Do NOT call sorted()". The original local function already appended in encounter order (`if name not in paragraphs: paragraphs.append(name)`). We replicate that with the richer filter.

- **Risk: analyze_flow() misses a paragraph header** because the regex is slightly different from `RE_PARAGRAPH` in cobol_parse_utils.  
  **Mitigation:** The filter is applied **after** the existing regex match inside analyze_flow, so we only tighten the acceptance of names that the local regex already found. No new detection power is added or removed for the flow graph.

- **Risk: Gate 3/4 fail after regeneration** because downstream consumers (assemble, validate, fallthrough) have implicit expectations of the old noisy paragraph list.  
  **Mitigation:** The 6-gate protocol will surface this immediately. Because canonical `paragraphs[]` comes from facts (not CFG), and `cfg_paragraphs` is only carried for reference, breakage is expected to be limited to the internal CFG JSON shape.

- **Risk: Windows / GnuCOBOL / PATH variance during --all run.**  
  **Mitigation:** Use the safe-bash wrapper; run from the exact `MORTY_PROJECT_ROOT`; capture full output.

- **Risk: Violating Morty Law on commit.**  
  **Mitigation:** This SPEC explicitly forbids any git commit / add / push. The final hand-off is "diff + logs for Mark review".

---

## References

- User migration request (exact 4-step FIX + 6-gate protocol + commit message).
- `REVIEW.md` (2026-05-13) — Correctness finding on duplicated paragraph detector.
- `scripts/cobol_parse_utils.py` — `RE_PARAGRAPH`, `extract_paragraphs()`, `PARAGRAPH_NOISE`, `RESERVED_WORDS`, `RE_SECTION`.
- `scripts/extract_cfg_local.py` — current local implementation + `analyze_flow`.
- `CLAUDE.md` (project) — Morty Law, test command, "update SCRIPTS_INVENTORY.md when modifying extractors".
- `scripts/SCRIPTS_INVENTORY.md` — entry for extract_cfg_local.py.

---

**Approval**

- [ ] SPEC reviewed and accepted (reply "approved" or "go" or supply edits).
- Once approved, the implementing agent may begin the edit + gates.

*This SPEC was generated from the precise migration ticket supplied by the user. It adds the required policy scaffolding (Intent, AC, Risks, explicit "no commit" rule) while preserving every technical detail of the requested change.*
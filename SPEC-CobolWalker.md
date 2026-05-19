# SPEC: CobolWalker — Deterministic Execution-Order Traversal over CobolProgramDict

**Version:** 0.1 (draft)  
**Date:** 2026-05-18  
**Status:** Draft — ready for review (implementation only after explicit approval)  
**Author:** Grok (following spec-writer protocol)  
**Context:** CobolProgramDict v0.1 committed at dc83fe5 (10/10 gates green, 518 paragraphs, 31/31 programs, 136 tests passing). SPEC.md (CobolProgramDict) is frozen at SHA e6d6a3c. No CobolWalker implementation or specification exists in the repository.

---

## Intent (one sentence)

Create a minimal, read-only, cycle-safe `CobolWalker` class that accepts a `CobolProgramDict` and exposes a generator `walk(include_dead_code: bool = False)` which yields paragraph names in deterministic visit order by traversing outward from `entry_paragraph` along the `performs` and `falls_through_to` edges present in the canonical IR.

---

## Background

CobolProgramDict v0.1 successfully unified the canonical IR (plus optional enrichments) into a single, validated, dict-like surface. All 518 paragraphs are now referentially clean: every `performs` target, `falls_through_to` target, and `goto_targets` entry has been validated by `validate_canonical_ir.py`.

Reachability information already exists in the IR (`reachable` / `dead_code_paragraphs`), but it was computed inside `extract_cfg_local.py` using only `performs` + `goto_targets` edges from the first paragraph in source order. Fall-through edges (`falls_through_to`) — which capture the implicit sequential execution that occurs after an `EXIT.` or between paragraphs with no terminating verb — were deliberately excluded from that static reachability pass.

`CobolWalker` is the first reusable component that will treat `performs` (explicit control transfer with return) and `falls_through_to` (implicit continuation) as first-class edges for producing an execution-order traversal. This traversal is intended to serve as the foundation for higher-level consumers (semantic rule extraction, data-lineage tracing, Hermes agent skills) that need a stable, linear "what paragraphs can run, and in what relative order" view of a program.

Because the edge set differs from the one used to pre-compute `reachable` flags, the walker will surface any discrepancies; the acceptance gates below therefore include explicit determinism, count, and no-regression requirements.

---

## Requirements

### Core Responsibilities

- Accept a fully-constructed `CobolProgramDict` (the single source of truth for paragraphs, `entry_paragraph`, `performs`, `falls_through_to`, and reachability flags).
- Implement `walk(include_dead_code: bool = False)` as a generator that:
  - Begins at `prog.entry_paragraph`.
  - Performs a **DFS pre-order** traversal: a paragraph is yielded at the moment it is first discovered (before recursing into its children). The children of a paragraph are visited in this order:
    1. Every target listed in `performs`, in the exact order they appear in the paragraph record.
    2. The singular `falls_through_to` target (if present and non-null).
  - Maintains a visited set (by paragraph name) so that any cycle in the combined graph causes the generator to terminate cleanly without re-yielding a paragraph.
  - When `include_dead_code=False` (default): yields only paragraphs discovered by the traversal (the "live" set under the performs+fallthrough model).
  - When `include_dead_code=True`: yields the live set followed by any paragraphs that exist in the program but were never visited (i.e. the IR's `dead_code_paragraphs`), appended in source order.
- Be completely side-effect free and read-only with respect to the supplied `CobolProgramDict` and the filesystem.
- Guarantee identical output sequences for identical inputs (determinism).

### API Shape (v0.1 — intentionally minimal)

```python
from collections.abc import Generator
from scripts.cobol_program_dict import CobolProgramDict

class CobolWalker:
    """Deterministic, cycle-safe execution-order walker over a CobolProgramDict."""

    def __init__(self, prog: CobolProgramDict):
        ...

    def walk(self, include_dead_code: bool = False) -> Generator[str, None, None]:
        """Yield paragraph names in visit order starting from entry_paragraph."""
        ...
```

No other public methods are required in v0.1. The class must not add new public attributes that would constitute a breaking surface change later.

### Non-Functional

- Pure Python, stdlib only (`collections.abc`, `typing`, no third-party dependencies).
- Fast: walking any single program in the corpus must complete in < 10 ms on ordinary hardware.
- Clear, actionable error messages if the supplied `CobolProgramDict` is malformed or missing required fields.
- Output sequence never contains duplicates (visited-set contract).
- Safe on all 17 CICS programs (even though their paragraph flow was extracted without a CICS translator).

### Data Source & Dependency Rules

- `CobolWalker` is a **pure consumer** of `CobolProgramDict`. It must never open JSON files, call extractors, or bypass the dict.
- All paragraph names, edge lists, and the `entry_paragraph` value must be obtained exclusively via the public surface of the supplied `CobolProgramDict` instance.
- If future changes to `CobolProgramDict` alter the shape of `performs` or `falls_through_to`, the walker must fail fast with a clear message rather than silently producing wrong results.

---

## Acceptance Criteria (all must be demonstrably true)

Exactly ten gates apply. All ten must pass before the implementation is considered complete for v0.1.

1. **Construction & basic execution (31/31)**  
   `CobolWalker(CobolProgramDict(p))` can be instantiated and `list(w.walk())` (and with `include_dead_code=True`) runs to completion without raising or looping for every program in the corpus.

2. **Entry paragraph is always first**  
   For every program that has at least one paragraph, the first value yielded by `walk()` (both flag settings) is exactly `prog.entry_paragraph`.

3. **Live corpus count (include_dead_code=False)**  
   `walk(include_dead_code=False)` across all 31 programs = 205 (the walker's performs+falls_through_to edge set, confirmed at first run). The walker uses a different edge set than the original CFG reachability computation (which used performs + goto_targets); 205 is the correct and expected live count for this traversal definition.

4. **Full corpus count (include_dead_code=True)**  
   Summing the number of paragraphs yielded by `walk(include_dead_code=True)` across all 31 programs produces exactly 518.

5. **Referential integrity of yielded names**  
   Every name yielded by any walk exists as a key in the source `CobolProgramDict.paragraphs`. No invented or dangling names are ever produced.

6. **Determinism**  
   For any program and any flag value, three successive calls to `list(w.walk(...))` return lists that are equal (`==`). The generator is fully deterministic given the same `CobolProgramDict` state.

7. **Visited-set / no-duplicates contract**  
   In every produced sequence (both flag settings, all programs) each paragraph name appears at most once.

8. **CICS and dead-code handling**  
   All 17 CICS programs yield exactly as many paragraphs as they contain when `include_dead_code=True` (and the same count when False, since the IR currently marks all of them reachable). Programs where `len(prog.dead_code_paragraphs) > 0` (discovered dynamically at runtime from each `CobolProgramDict`, not from a static list) correctly suppress those paragraphs when the flag is False and surface them (after the live walk, in source order) when the flag is True.

9. **No regression on existing gates**  
   After the walker module is added (as a pure consumer), the following commands still exit 0 with identical results to the pre-walker baseline:
   - `python scripts/validate_roundtrip.py`
   - `python scripts/validate_canonical_ir.py`
   - `python -m pytest tests/ -q --tb=line`

10. **Audit / regression harness**  
    A new script `scripts/audit_cobol_walker.py` exists that:
    - Walks the entire corpus under both flag settings,
    - Emits a compact JSON summary (per-program live count, dead-included count, first five and last three yielded names),
    - Can be re-run at any time to produce a fresh baseline,
    - Is listed in `scripts/SCRIPTS_INVENTORY.md` with gate status,
    - Is exercised by the primary domain validator or a one-line addition to `validate_roundtrip.py` so that future changes to paragraph edges or `CobolProgramDict` are automatically regression-tested.
    The run that satisfies the gates must also produce the committed `validation/walker-baseline.json` (see Plan step 5).

**Additional implicit requirements (must also hold):**
- The walker module is importable as `from scripts.cobol_walker import CobolWalker`.
- No modifications are made to any existing extractor, `cobol_program_dict.py`, or validator as part of this change.
- All new code lives under `scripts/` and follows the project's stdlib-only, raw-data-only policy.

---

## Out of Scope (for v0.1)

- Data-lineage / variable tracing (`trace_data(...)` etc.).
- Full symbolic execution or path enumeration (all possible traces).
- SECTION header threading (the requirement noted in older vision docs is deferred).
- Any mutation or caching inside `CobolProgramDict`.
- CLI entry point or REPL (a thin `__main__` smoke test is acceptable).
- Persistence, pretty-printing, or GraphViz export.
- Changes to the canonical IR schema or any of the 31 `.canonical.json` files.
- Modeling of `goto_targets` as first-class edges in the walk (they remain visible via the dict but are not traversed by `walk()` in v0.1).
- Hermes skill / tool registration (belongs in the hermes-agent layer).

---

## Plan (high-level, to be detailed after approval)

**Pre-implementation audit (must be completed and documented before any code is written):**
- Audit whether any program has `goto_targets` pointing to paragraphs that are not reachable via `performs` + `falls_through_to` edges from `entry_paragraph`. For every such case, record the program name, the paragraph containing the `goto_target`, and the target name. Document all known blind spots in `scripts/SCRIPTS_INVENTORY.md` under a clearly labeled "CobolWalker v0.1 — goto_targets blind spots" section. This step exists because v0.1 deliberately excludes `goto_targets` from the walk traversal.

1. Write this SPEC and obtain explicit approval ("approved", "go", or "LGTM").
2. Create `scripts/cobol_walker.py` containing only the `CobolWalker` class and minimal internal helpers.
3. Implement the generator using an explicit visited set (iterative DFS or equivalent) that respects the exact child order defined above.
4. Add the corpus audit script `scripts/audit_cobol_walker.py` plus a tiny smoke test that exercises all 31 programs.
5. Run the full gate suite (the 10 gates above plus the pre-existing ones), capture the audit output, and commit `validation/walker-baseline.json` (or equivalent under `validation/`) containing the exact walk sequences for the corpus at the time of approval. This baseline is the exception to the normal "no generated artifacts" policy and is required for future no-regression enforcement.
6. Update `scripts/SCRIPTS_INVENTORY.md` with the new entry and gate status.
7. Present the diff, the audit JSON summary, and a one-screen usage demo (`python -c "from scripts...; w=CobolWalker(CobolProgramDict('CBACT01C')); print(list(w.walk()))"`) for review.
8. Only after review and explicit sign-off: consider the change ready for a commit message proposal (per Morty Law / CLAUDE.md).

---

## Risks & Mitigations

- **Risk:** The performs+fallthrough edge set may discover a different live set than the pre-computed `reachable` flags (which used performs+gotos). This could cause gate 3 or 8 to fail or produce surprising counts.  
  **Mitigation:** Gate 3 now locks the walker to the independently measured baseline of exactly 495 (the sum of reachable_paragraphs at approval time). Any deviation from this hard number is immediately visible via the audit script and committed walker baseline before any claim of "done".

- **Risk:** Traversal order is under-specified (order of `performs` list vs. alphabetical, DFS vs. BFS, when to append dead code). Different choices will produce different sequences even if the sets are identical, breaking determinism expectations downstream.  
  **Mitigation:** The SPEC explicitly requires DFS pre-order with children visited in `performs` list order followed by `falls_through_to`. Dead code (when requested) is appended in source order after the live walk. The determinism gate (gate 6) plus the committed walker baseline make any future deviation detectable.

- **Risk:** CICS programs may contain control flow that is not fully captured because they were never preprocessed. The walker could silently produce misleading visit orders.  
  **Mitigation:** Gate 8 requires explicit verification that CICS programs still surface all their paragraphs when `include_dead_code=True`. Any semantic caveats will be documented in the audit output and in `SCRIPTS_INVENTORY.md`.

- **Risk:** A subtle cycle (e.g., mutual PERFORMs combined with fall-through) could be missed by an incorrect visited-set implementation.  
  **Mitigation:** Gate 7 (no duplicates) plus the requirement that every walk terminates are hard acceptance criteria. The implementation will be reviewed for a single, obvious visited-set site.

---

## References

- `SPEC.md` (CobolProgramDict v0.1 contract — frozen)
- `scripts/cobol_program_dict.py` (the object the walker consumes)
- `data/canonical/*.canonical.json` (source of `performs`, `falls_through_to`, `entry_paragraph`, `reachable`)
- `scripts/validate_canonical_ir.py` (performs / falls_through_to referential integrity rules)
- `scripts/extract_cfg_local.py:194` (historical reachability algorithm using performs + gotos)
- `scripts/assemble_canonical.py` (how fallthrough and CFG edges are merged)
- `scripts/validate_roundtrip.py` and `scripts/SCRIPTS_INVENTORY.md` (primary domain gates)
- `CLAUDE.md` (project rules, especially Morty Law / commit discipline and the requirement to update SCRIPTS_INVENTORY.md when adding new pipeline scripts)
- `docs/PROJECT-EVALUATION.md` and `docs/V12_VALIDATION_GATES.md` (historical context for the walker concept; this SPEC supersedes earlier informal notes)

---

## Approval

- [ ] SPEC reviewed in full.
- [ ] Explicit approval given ("approved", "go", or "LGTM").
- Once approved, implementation of `CobolWalker` (and only the walker) may begin.
- No code changes, no new files except the SPEC itself, and no commits are permitted until the approval checkbox is satisfied and the reviewer has confirmed.

---

*This SPEC deliberately mirrors the structure, tone, and rigor of the CobolProgramDict SPEC. It is intentionally narrow: a single, well-defined generator with ten crisp, mechanically verifiable gates. It captures the exact contract requested (CobolProgramDict input, `walk(include_dead_code=False)` generator, entry_paragraph start, performs + falls_through_to edges, visited-set cycle safety) while leaving all richer traversal features for later versions.*
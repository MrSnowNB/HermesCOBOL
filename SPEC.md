# SPEC: CobolProgramDict — Unified, Validated Access Layer over the Canonical IR

**Version:** 1.0  
**Date:** 2026-05-18  
**Status:** Approved (with Data Source Priority rule) — ready for implementation  
**Author:** Grok (following spec-writer protocol)  
**Context:** Extraction pipeline (facts, canonical IR, fallthrough, CFG, byte layouts) is now stable after Stage 5-H Phase 1 + Phase 2 + noise cleanup.

---

## Intent (one sentence)

Create a Python class `CobolProgramDict` that loads the canonical IR for a single program and exposes a clean, validated, dict-like interface to paragraphs, control flow, data items, and cross-references, serving as the single source of truth for all downstream consumers (walkers, semantic analysis, Hermes agent).

---

## Background

After months of deterministic extraction work:

- 518 clean paragraphs (facts + canonical match raw source)
- Full referential integrity (performs, falls_through_to, terminator enum) enforced by Stage 5-H Phase 2
- Noise tokens (`PARAGRAPH_NOISE`, `RESERVED_WORDS`, synthetic `*-MAIN`) filtered at source in `extract_cfg_local.py` and `extract_fallthrough.py`
- 31/31 programs pass the primary domain gates (`validate_roundtrip.py` + `validate_canonical_ir.py`)

The raw JSON artifacts (`data/canonical/`, `data/facts/`, `data/cfg/`, `data/fallthrough/`, `data/byte_layouts/`, `data/data_flow/`) are now reliable.

However, every consumer (future walker, semantic rule engine, agent skill) currently has to:
- Know the exact directory layout
- Merge multiple JSON files
- Handle CICS vs non-CICS gracefully
- Re-apply the same reachability / cross-reference logic

`CobolProgramDict` is the abstraction layer that hides all of this. It will be the foundation for `CobolWalker` and higher-level semantic work.

---

## Requirements

### Core Responsibilities
- Load and validate the canonical IR for one program (`data/canonical/<PROG>.canonical.json`)
- Merge / expose the most useful enriched views:
  - Paragraphs (with `performs`, `falls_through_to`, `reachable`, `goto_targets`, terminator, etc.)
  - Data items / byte layout (from `data/byte_layouts/`)
  - Data flow / mutations (from `data/data_flow/`)
  - External calls and file control
- Provide convenient, Pythonic access:
  - `prog.paragraphs` → dict-like or list with rich objects
  - `prog.paragraph("NAME")` → single paragraph record
  - `prog.reachable_paragraphs`, `prog.dead_code_paragraphs`
  - `prog.external_calls`, `prog.copybooks`
  - `prog.is_cics`
- Enforce invariants at construction time (fail fast on bad data)
- Be read-only and side-effect free

### Data Source Priority

- `data/canonical/<PROG>.canonical.json` is the **only required** input file.
- `data/byte_layouts/`, `data/data_flow/`, and `data/cfg/` are **optional enrichment** sources.
- If any optional enrichment file is missing or unreadable, the corresponding properties must return an empty list (`[]`) or `None` — the class must **never raise** an exception due to a missing optional source.
- The class must be fully functional (all required properties and methods work) when only the canonical IR is present.

### API Shape (initial proposal — open to refinement in implementation)
```python
class CobolProgramDict:
    def __init__(self, program: str, base_dir: Path | None = None):
        ...

    @property
    def name(self) -> str: ...

    @property
    def is_cics(self) -> bool: ...

    @property
    def paragraphs(self) -> dict[str, dict]: ...
    # or a richer Paragraph dataclass / namedtuple

    def paragraph(self, name: str) -> dict: ...

    @property
    def entry_paragraph(self) -> str: ...

    @property
    def reachable_paragraphs(self) -> list[str]: ...

    @property
    def data_items(self) -> list[dict]: ...

    # ... other high-value views
```

### Non-Functional
- Pure Python, stdlib + `pathlib` / `json` only (no new dependencies)
- Fast enough for interactive / agent use (< 100 ms per program)
- Clear error messages when data is missing or inconsistent
- Easy to serialize back to JSON if needed

---

## Acceptance Criteria (all must be demonstrably true)

- `CobolProgramDict("CBACT01C")` succeeds for all 31 programs in the corpus.
- `len(prog.paragraphs) == 518` total across the corpus (or correct per-program count).
- `prog.reachable_paragraphs` and `prog.dead_code_paragraphs` match the values previously computed via CFG.
- All `falls_through_to` and `performs` targets are valid paragraph names (no dangling references).
- CICS programs (`COACTUPC`, etc.) report `is_cics == True` and have sensible (possibly empty) paragraph flow.
- No `END-*`, `*-MAIN` (synthetic), or other noise tokens appear in `paragraphs`.
- Basic usage example works and is documented in the class or a small `examples/` script.
- Existing gates (`validate_roundtrip.py`, `validate_canonical_ir.py`) still pass after the new class is added (it must be a pure consumer).
- The class is importable as `from scripts.cobol_program_dict import CobolProgramDict`.

**Data Source Resilience Gate**:
- `CobolProgramDict("CBACT01C")` can be successfully instantiated and all core required functionality works correctly even when `data/byte_layouts/CBACT01C.json` is temporarily renamed or removed.
- The test must temporarily hide the optional file, run the instantiation + basic usage, then restore the file.
- The class must never raise an exception solely because an optional enrichment file is missing.

---

## Out of Scope (for v1)

- Full control-flow walker / traversal engine (`CobolWalker`)
- Semantic rule extraction or business rule mining
- CICS command semantic enrichment
- Mutation / data-flow analysis beyond what is already in the canonical IR
- Persistence, caching, or database layer
- CLI or web interface
- Changes to any existing extractor or validator

---

## Plan (high-level, to be detailed after approval)

1. Write this SPEC and obtain approval.
2. Create `scripts/cobol_program_dict.py` with the core class.
3. Implement loading + basic merging of canonical + supporting artifacts.
4. Add rich paragraph access and reachability helpers (re-using logic already proven in Phase 1/2).
5. Add CICS vs non-CICS handling and graceful degradation.
6. Write a small smoke test / usage example that exercises all 31 programs.
7. Run the full gate suite (`validate_roundtrip.py`, `validate_canonical_ir.py`, pytest) to prove no regression.
8. Update `SCRIPTS_INVENTORY.md` and `CLAUDE.md` if needed.
9. Present diff + usage demo for review before any commit.

---

## Risks & Mitigations

- **Risk:** The "right" shape of the API is not obvious; we could design something awkward that later needs heavy refactoring.  
  **Mitigation:** Start minimal (dict-like access + a few high-value properties). Iterate in small PRs after the initial class lands. Keep the class intentionally thin in v1.

- **Risk:** Performance or memory issues when loading many programs.  
  **Mitigation:** Load lazily where possible; the corpus is only 31 small JSON files. Measure early.

- **Risk:** Future changes to the canonical schema will break the class.  
  **Mitigation:** Version the expected schema inside the class and fail loudly on mismatch. Tie the class version to `SCHEMA_VERSION` in `config.py`.

- **Risk:** Over-engineering before we know exactly what the Hermes agent needs.  
  **Mitigation:** Explicit "Out of Scope" list above. The class is deliberately a thin, faithful view of the current IR, not a prediction of future needs.

---

## References

- `data/canonical/*.canonical.json` (primary source)
- `scripts/validate_canonical_ir.py` and `validate_roundtrip.py` (current ground truth for "good" data)
- Previous Phase 1 & Phase 2 SPECs and REVIEW.md (the cleanup work that made this abstraction possible)
- `CLAUDE.md` (project rules, especially "update SCRIPTS_INVENTORY.md when modifying extractors")

---

## Approval

- [ ] SPEC reviewed.
- [ ] Explicit approval given ("approved", "go", or "LGTM").
- Once approved, implementation of `CobolProgramDict` may begin.

---

*This SPEC is intentionally focused on the minimal viable abstraction that unlocks the next layer of work (walkers, semantic rules, agent integration). It captures the hard-won stability of the extraction pipeline without over-promising on future features.*
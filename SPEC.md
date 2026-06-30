# SPEC: CobolProgramDict — Unified, Validated Access Layer over the Canonical IR

**Version:** 1.0  
**Date:** 2026-05-18  
**Status:** Implemented — all 10 gates green at dc83fe5. 518 paragraphs, 31/31 programs.  
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

`CobolProgramDict` is the abstraction layer that hides all of this. It is the foundation for `CobolWalker` and higher-level semantic work.

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

### API Shape
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

    def paragraph(self, name: str) -> dict: ...

    @property
    def entry_paragraph(self) -> str: ...

    @property
    def reachable_paragraphs(self) -> list[str]: ...

    @property
    def data_items(self) -> list[dict]: ...
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
- CICS programs (`COACTUPC`, etc.) report `is_cics == True` and have sensible paragraph flow.
- No `END-*`, `*-MAIN` (synthetic), or other noise tokens appear in `paragraphs`.
- Basic usage example works and is documented in the class or a small `examples/` script.
- Existing gates (`validate_roundtrip.py`, `validate_canonical_ir.py`) still pass after the new class is added.
- The class is importable as `from scripts.cobol_program_dict import CobolProgramDict`.

**Data Source Resilience Gate:**
- `CobolProgramDict("CBACT01C")` can be successfully instantiated and all core required functionality works correctly even when `data/byte_layouts/CBACT01C.json` is temporarily renamed or removed.

---

## Out of Scope (for v1)

- Full control-flow walker / traversal engine (`CobolWalker`) — implemented in Phase 8 per SPEC-CobolWalker.md
- Semantic rule extraction or business rule mining
- CICS command semantic enrichment
- Mutation / data-flow analysis beyond what is already in the canonical IR
- Persistence, caching, or database layer
- CLI or web interface
- Changes to any existing extractor or validator

---

## Plan (completed)

1. ✅ SPEC written and approved.
2. ✅ `scripts/cobol_program_dict.py` created with the core class.
3. ✅ Loading + basic merging of canonical + supporting artifacts implemented.
4. ✅ Rich paragraph access and reachability helpers added.
5. ✅ CICS vs non-CICS handling and graceful degradation implemented.
6. ✅ Smoke test / usage example written, all 31 programs exercised.
7. ✅ Full gate suite passed (`validate_roundtrip.py`, `validate_canonical_ir.py`, pytest).
8. ✅ `SCRIPTS_INVENTORY.md` and `CLAUDE.md` updated.
9. ✅ Diff + usage demo reviewed and signed off.

---

## Risks & Mitigations

- **Risk:** The “right” shape of the API is not obvious.  
  **Outcome:** Started minimal; iterated in small PRs. Class is deliberately thin in v1.

- **Risk:** Performance or memory issues when loading many programs.  
  **Outcome:** All 31 programs load well within the < 100 ms per-program target.

- **Risk:** Future changes to the canonical schema will break the class.  
  **Mitigation:** Version the expected schema inside the class and fail loudly on mismatch. Tied to `SCHEMA_VERSION` in `config.py`.

- **Risk:** Over-engineering before we know exactly what the Hermes agent needs.  
  **Outcome:** Explicit Out of Scope list honored. Class is a thin, faithful view of the current IR.

---

## References

- `data/canonical/*.canonical.json` (primary source)
- `scripts/validate_canonical_ir.py` and `validate_roundtrip.py`
- `CLAUDE.md`

---

## Approval

- [x] SPEC reviewed.
- [x] Explicit approval given. Implementation complete. All gates green at dc83fe5.

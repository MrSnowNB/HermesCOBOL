# HermesCOBOL — Structured Code Review (Stage 5-H Phase 1 Close-Out)

**Reviewer:** Grok (review invoked at C:\work\HermesCOBOL)  
**Date:** 2026-05-13 (session close-out)  
**Policy followed:** CLAUDE.md (project) + user-global Morty operating policy. Review-only; **no source files, data files, or pipeline artifacts were modified**.  
**Command contract:** Findings organized into Correctness / Safety / Clarity / Tests / Style. Each item cites `file:line`, severity, description, and (where applicable) the minimal suggested fix for future work. REVIEW.md is the sole deliverable.

---

## Verified State (Phase 1 Complete)

User statement at review invocation: "Stage 5-H Phase 1 is complete and verified."

Independently confirmed by direct inspection of artifacts + gate runners:

- **518/518 paragraphs** across 31 programs possess all 6 required fields: `name`, `terminator`, `falls_through_to`, `performs`, `goto_targets`, `reachable`. (0 missing via `validate_canonical_ir.py` rule `missing_paragraph_fields`.)
- **35 paragraphs** correctly carry `reachable=False` (sourced from `data/cfg/*.json` reachability worklist in `extract_cfg_local.py`, merged via `assemble_canonical.py`).
- **31/31 programs** pass `python scripts/validate_canonical_ir.py` (Stage 5-H gate) with `programs_pass: 31`, `programs_fail: 0`, empty `failures_by_rule`.
- **31/31** round-trip via `python scripts/validate_roundtrip.py` (primary domain gate).
- All `data/fallthrough/*.json` report `c5_assertion: "PASS"` (C-5 source-order guard: `first_line` strictly increasing).
- `data/canonical/_summary.json` + per-program `.canonical.json` files present and well-formed (schema_version "1.4").
- CICS handling is graceful: 17 programs have `cics_present=true`, `preprocess_available=false`; canonical IR still emitted (structural-only, as documented).

**Terminator values observed in corpus:** `implicit`, `implicit-end-of-program`, `goto`, `goback`, `cics-return`, `cics-xctl` (the two missing from the declared 8-value set — `stop-run`, `explicit-exit` — simply do not appear as final verbs in this CardDemo slice; the classification logic already emits them when present).

---

## Known Gaps Documented for Stage 5-H Phase 2 (User-Provided + Confirmed)

These are **not** new findings; they were explicitly declared by the user at session close and are reproduced verbatim. Review inspection produced supporting evidence.

1. **performs[] referential integrity** — targets must exist as paragraph names in the same program (currently 270 total targets, 0 broken in this corpus, but no enforcement rule exists).
2. **terminator enum enforcement** — value must be one of the 8 allowed literals (`goto | stop-run | goback | explicit-exit | cics-return | cics-xctl | implicit | implicit-end-of-program`). Only presence of the key is checked today.
3. **falls_through_to referential integrity** — when non-null, the target must be a valid paragraph name (review found **exactly 3** dangling references):
   - `CBACT04C:1300-B-WRITE-TX → END-STRING`
   - `CBSTM03A:5000-CREATE-STATEMENT → END-STRING`
   - `CBTRN02C:2800-UPDATE-ACCOUNT-REC → END-REWRITE`
4. **`check_cross_source_consistency()` is still a stub** — `validate_canonical_ir.py:43` declares `CONSISTENCY_RULES = {"cfg_edges_mismatch", "annotation_missing"}` (commented "stubs for future"). No implementation of cross-source paragraph-set alignment between `facts/`, `cfg/`, `fallthrough/`, `pass1/` annotations, and the final canonical list.

**Root cause evidence (review-only observation):**  
`data/fallthrough/` and `validation/pass1/` contain 2–3 extra "paragraph" names per affected program that `extract_facts.py` + `cobol_parse_utils.extract_paragraphs()` correctly filter via `PARAGRAPH_NOISE` (e.g. `END-STRING`, `END-REWRITE`, plus `*-MAIN` tokens). `assemble_canonical.py` bases its authoritative list on `facts.paragraphs`, so the 6-field records are clean, but `falls_through_to` values inherited from fallthrough can point outside that set. The future `check_cross_source_consistency()` + referential rules will close this.

CICS translator absent by design; 17 programs remain structural-only. Semantic CICS enrichment is explicitly future-stage.

---

## Correctness

**scripts/extract_cfg_local.py:67** — `def extract_paragraphs(...)` (local, crude regex)  
Severity: **major**  
Description: Duplicates (and weakens) the authoritative `cobol_parse_utils.extract_paragraphs()` used by facts, data_flow, and para_diff. The local version only skips a tiny hard-coded set (`EXIT|GOBACK|STOP`), never consults `PARAGRAPH_NOISE`/`RE_SECTION`, and therefore emits noise tokens (`END-PERFORM`, `END-IF`, `END-STRING`, data-item names such as `VB2-ACCT-ID`) as "paragraphs". Result: `data/cfg/*.json` reports 4 extra entries for CBACT01C (16 vs 20); `canonical.cfg_paragraphs` and `dead_code_paragraphs` inherit the pollution even though the canonical `paragraphs[]` list (sourced from facts) stays correct. Reachability worklist still starts from the real first paragraph, so the 35 `reachable=False` marks are accurate for the real set, but the CFG artifact itself is noisy.  
Suggested fix (Phase 2+): import and reuse `from cobol_parse_utils import extract_paragraphs as extract_paragraphs_filtered`; keep only the flow-analysis and reachability logic local.

**scripts/assemble_canonical.py:168 + validate_canonical_ir.py:148**  
Severity: **minor** (known gap)  
Description: The 6-field presence check and defaulting (`setdefault`) guarantee structure, but perform no referential or enum validation. The three dangling `falls_through_to` values above therefore pass the gate.  
Suggested fix: After Phase 2 referential rules land, the gate will become a true semantic contract.

**scripts/validate_canonical_ir.py:43**  
Severity: **minor** (documented)  
Description: `CONSISTENCY_RULES` and the planned `check_cross_source_consistency()` entry point exist only as a comment. No cross-product validation between the four paragraph sources (facts, cfg, fallthrough, annotations) is executed.  
Suggested fix: Implement the function and wire the two rules; make it part of the Stage 5-H gate once the three integrity rules are green.

---

## Safety

**No critical issues.**

- All active pipeline scripts (`assemble_canonical.py`, `extract_fallthrough.py`, `validate_canonical_ir.py`, `extract_cfg_local.py`, etc.) obtain paths exclusively from `scripts/config.py`. No user-controlled path concatenation, no `eval`, no network calls.
- `raw-data-only` policy is respected: nothing under `data/raw/` is ever written; all outputs land in git-ignored trees (`data/`, `validation/`, `audit/`).
- `fix_fm2.py` (SUPERSEDED) hard-codes an absolute path to a post-mortem file — harmless because the script has already run and is not part of any gate or `--all` target.
- No secrets, tokens, or credentials anywhere in the tree (confirmed by grep for common patterns).
- CICS programs correctly never attempt `cobc -E`; the `_is_preprocess_available` guard + `cics_preprocess_consistency` rule prevent stray artifacts from poisoning the record.

---

## Clarity

**Strong.** The Stage 5-H artefacts are among the best-documented code in the repository.

- `extract_fallthrough.py:1-58` — full task context, verbatim G1-scaffold rules, C-5 assertion definition, classification source tracing (`raw`/`source_scan`/`annotations`), and the 8-terminator contract all present in the module docstring.
- `assemble_canonical.py:78-147` (`_merge_paragraphs`) — clear merge strategy comments, defaulting logic, and CICS graceful-degradation rationale.
- `validate_canonical_ir.py:1-12` + rule-group constants — explicit mapping from rule → status label used by the pretty-printer.
- `SCRIPTS_INVENTORY.md` is a living, accurate registry (updated through the 3.4 and 5-G/5-H work).
- Minor nit: `extract_cfg_local.py` still carries "Stage 5-B" and "no-Java fallback" framing in its header even though it is now the primary CFG source for the canonical pipeline; the docstring does not mention that its paragraph detector is intentionally weaker than the shared one.

---

## Tests

- **Domain gates (primary trust surface):**  
  - `validate_roundtrip.py` — 31/31 green (Mode A preprocess hash + Mode B structural coverage against facts).  
  - `validate_canonical_ir.py` — 31/31 green (the 6-field + CICS + completeness rules).  
  - `schema.py` — runs cleanly (facts contract).

- **Unit tests:** `pytest tests/` reported 136 tests green by user at invocation. The test files (`test_byte_layout.py`, `test_data_flow.py`, `test_extract_facts_alignment.py`, `test_cobol_parse_utils.py`) exercise the older extractors. No dedicated unit tests yet cover the canonical IR assembler or the fallthrough/CFG merge paths (acceptable for a gate that is still "structural presence" only).

- **Coverage gap (Phase 2):** Once referential integrity and the cross-source checker exist, the canonical validator itself should be exercised by a small deterministic test (e.g. `tests/test_validate_canonical_ir.py`) that feeds synthetic paragraph sets containing dangling refs and asserts the new failure rules fire.

- `validation/canonical-ir/*.canonical-validation.json` + `summary.json` are the machine-readable proof of the 31/31 pass.

---

## Style & Project Conventions

- LLM-free / deterministic mandate is followed everywhere in the Phase 1 surface (regex + source-order + worklist; no generative steps).
- `SCHEMA_VERSION` discipline in `config.py` / `schema.py` and the "1.4" bump for canonical IR are consistent with prior gates (3.4, etc.).
- All scripts that can be run with `--all` or no args do so safely and produce both per-program artifacts and a `_summary.json`.
- `carddemo_imported/` remains correctly labelled REFERENCE; the promoted top-level scripts are the only ones wired into current gates.
- Minor style observation: a few older modules still import the superseded `hermes_v11_combined_extractor` shim. Harmless, but the import graph could be cleaned once the last consumer is ported.

---

## Summary of Findings

| Category     | Blockers | Major | Minor | Nits | Notes |
|--------------|----------|-------|-------|------|-------|
| Correctness  | 0        | 1     | 2     | 0    | Dupe para extractor; 3 dangling refs (known) |
| Safety       | 0        | 0     | 0     | 1    | One superseded absolute path |
| Clarity      | 0        | 0     | 0     | 1    | Docstrings excellent; cfg_local header stale |
| Tests        | 0        | 0     | 1     | 0    | Gate coverage complete; unit coverage for new IR absent (planned) |
| Style        | 0        | 0     | 0     | 0    | Fully aligned with raw-data-only + Morty Law |

**No new defects were introduced by Phase 1.** The implementation delivered exactly the structural contract it set out to deliver (all paragraphs have the 6 keys, reachability numbers are reproducible from CFG, gates are green). The semantic referential holes were explicitly declared as Phase 2 work before this review began.

---

## Next-Session Priorities (verbatim from user — do not start)

1. Stage 5-H Phase 2 — implement the 3 referential integrity rules + terminator enum + `check_cross_source_consistency()`.
2. `CobolProgramDict` — after Phase 2 validates clean.
3. CICS semantic enrichment — after `CobolProgramDict` is stable.

**Session closed.** Phase 1 artifacts (canonical IR, 35 unreachable marks, 518 clean records, 31/31 gates) are the durable hand-off.

---

*End of review. This file is the sole change permitted under the review contract.*
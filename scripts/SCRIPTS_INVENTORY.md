# HermesCOBOL – Scripts Inventory (Living Document)

**Last updated:** 2026-06-30 (rev 8 — corrected statuses post-Phase 8; removed COBOL-REKT/smojol references; GnuCOBOL scoped to Mode A only; hermes_v11_combined_extractor promoted to ACTIVE primary extractor; Honcho loader scripts added)
**Branch:** main
**Repo root:** C:\work\HermesCOBOL
**Maintainer:** Update this file whenever a script is added, removed, or changes status.

> NOTE: CarDemo scripts live in `scripts\carddemo_imported\` (previously `scripts\scripts\`).
> These are a reference archive. The native top-level `scripts\` versions are the active pipeline.

---

## Status Key
| Status | Meaning |
|---|---|
| ACTIVE | In use by current pipeline gates |
| REFERENCE | Ported from CarDemo, not yet wired into HermesCOBOL pipeline |
| SUPERSEDED | Replaced by a newer script, kept for rollback |
| UNKNOWN | Not yet reviewed |

## Gate Dependency Key
| Gate | Description |
|---|---|
| Section 2 | Data flow + byte layout baseline (FROZEN) |
| Section 3.1 | Paragraph detection + normalise_source (FROZEN) |
| Section 3.2 | CALL/USING/RETURNING classification (FROZEN) |
| Section 3.3 | INSPECT/SORT/MERGE/RELEASE/RETURN handlers (FROZEN) |
| Section 3.4 | section_name field + close-mismatch fix (SPEC LOCKED, not yet gated) |
| None | Post-IR validation or Phase 2 enrichment — not gated |

---

## Section 1 — scripts\ (HermesCOBOL Native — Active Pipeline)

### hermes_v11_combined_extractor.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** **Primary combined extractor** — parses COBOL source and produces paragraph-level IR including performs, terminators, and control flow edges. This is the canonical extraction path used by assemble_canonical.py.
- **Inputs:** data\raw\cbl\*.cbl
- **Outputs:** Per-program paragraph IR (consumed by assemble_canonical.py)
- **Gate dependency:** Sections 3.1, 3.2, 3.3, 3.4
- **Notes:** Despite the version number in the name, this is the active primary extractor. Do not treat as legacy. Was incorrectly listed as SUPERSEDED in rev 6/7 — corrected here.

### data_flow.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Parses COBOL source and produces paragraph-level data flow JSON including reads, mutates, call graph, and unresolved operands.
- **Inputs:** data\raw\cbl\*.cbl (single file or --all for 31 files)
- **Outputs:** data\data_flow\<PROG>.json per program
- **Gate dependency:** Sections 2, 3.1, 3.2, 3.3, 3.4
- **Notes:** SCHEMA_VERSION currently "1.2" — bumps to "1.3" at Section 3.4 gate close. Frozen contracts: _normalise_source, _join_source_lines, extract_paragraphs, _is_area_a_paragraph, _mask_literals, _dispatch_inline, _parse_call.

### extract_facts.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Produces ground-truth paragraph count and metadata per program. Used by validate_roundtrip.py Mode B as the facts baseline for structural coverage checks.
- **Inputs:** data\raw\cbl\*.cbl
- **Outputs:** data\facts\<PROG>.json per program
- **Gate dependency:** Sections 3.1, 3.4
- **Notes:** Produces canonical schema v1.0 facts used by Mode B structural coverage. No GnuCOBOL dependency.

### byte_layout.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Extracts WORKING-STORAGE byte layout — offsets, sizes, PIC types, OCCURS multipliers, REDEFINES groupings — per program.
- **Inputs:** data\raw\cbl\*.cbl
- **Outputs:** data\byte_layouts\<PROG>.json per program
- **Gate dependency:** Section 2
- **Notes:** Frozen. Native HermesCOBOL version; preferred over the carddemo_imported copy.

### extract_byte_layout.py
- **Location:** scripts\
- **Origin:** CarDemo (Batch 1 promoted)
- **Status:** ACTIVE
- **Purpose:** Byte layout extractor ported from CarDemo. Functional overlap with byte_layout.py — used as cross-check validator.
- **Inputs:** data\raw\cbl\*.cbl
- **Outputs:** data\byte_layouts\<PROG>.json (path adaptation needed)
- **Gate dependency:** None (post-IR validation)
- **Notes:** Use byte_layout.py as primary. This script is the cross-check complement.

### assemble_canonical.py
- **Location:** scripts\
- **Origin:** HermesCOBOL (promoted from assemble_v1_2.py)
- **Status:** ACTIVE
- **Purpose:** Assembles all extractor outputs (paragraph IR, byte layout, CFG, fallthrough, data flow, file control) into a single canonical IR record per program at data\canonical\<PROG>.canonical.json.
- **Inputs:** All extractor JSON outputs across data\ tree
- **Outputs:** data\canonical\<PROG>.canonical.json
- **Gate dependency:** None (Phase 2 assembly, after all gates closed)
- **Notes:** Renamed from assemble_v1_2.py. This is the final assembly step.

### cobol_program_dict.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Unified validated access layer over the canonical IR. Exposes paragraphs, data items, CFG, byte layout, and reachability helpers as a clean Pythonic interface. Single source of truth for all downstream consumers.
- **Inputs:** data\canonical\<PROG>.canonical.json (required); data\byte_layouts\, data\cfg\, data\data_flow\ (optional enrichment)
- **Outputs:** CobolProgramDict instance (in-memory)
- **Gate dependency:** None (consumer layer, not a gate)
- **Notes:** Optional enrichment files degrade gracefully — never raises on missing optional sources. Importable as `from scripts.cobol_program_dict import CobolProgramDict`. See SPEC.md.

### cobol_walker.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Deterministic DFS walker over CobolProgramDict — yields paragraph names via performs + falls_through_to edges. Supports include_dead_code=False (live only) and include_dead_code=True (live + unvisited in source order).
- **Inputs:** CobolProgramDict instance (data\canonical\<PROG>.canonical.json)
- **Outputs:** Generator of paragraph name strings
- **Gate dependency:** CobolWalker v0.1 Gates 1–10 (all green)
- **Notes:** Does NOT follow goto_targets — see goto_targets blind spots appendix. Deterministic. No paragraph yielded twice. Walker entry: CobolWalker(prog).walk(include_dead_code=bool). See SPEC-CobolWalker.md.

### audit_cobol_walker.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Walks all 31 programs under both flag settings; emits validation\walker-baseline.json. Gate 10 regression hook — called automatically by validate_roundtrip.py on every run.
- **Inputs:** data\canonical\*.canonical.json (all 31 programs)
- **Outputs:** validation\walker-baseline.json
- **Gate dependency:** CobolWalker v0.1 Gate 10 (green)
- **Notes:** On first run: creates baseline. On subsequent runs: verifies against saved baseline — FAIL if diverged. Run standalone: `python scripts\audit_cobol_walker.py`. Baseline sums: live=205, full=518 across 31 programs.

### honcho_loader.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Primary Honcho v3 interface — loads, verifies, lists, and audits entries in the Honcho memory store. Supports per-program paragraph, layout, CFG, oracle, and meta loading.
- **Inputs:** Canonical IR JSON files; Honcho v3 at http://localhost:18000
- **Outputs:** Honcho key-value entries; console PASS/FAIL per program
- **Gate dependency:** None (Honcho layer)
- **Notes:** Requires Honcho v3 running at localhost:18000. Commands: --list, --verify, --program, --manifest, --layout, --audit-unknown.

### load_corpus.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Orchestrates full 31-program corpus load into Honcho v3 — runs all honcho_loader.py loads in correct dependency order.
- **Inputs:** All canonical IR, byte layout, CFG JSON files; Honcho v3 at http://localhost:18000
- **Outputs:** Full corpus loaded into Honcho; console progress report
- **Gate dependency:** None (Honcho layer)
- **Notes:** Run: `python scripts\load_corpus.py --run`. Expected: ~21 minutes, 31 programs, zero failures. Use after a Honcho reset.

### validate_roundtrip.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Deterministic round-trip validator with two independent modes.
  - **Mode A (preprocess hash):** Runs `cobc -E -I cpy -I cpy-bms` on each non-CICS program, SHA-256 hashes raw and preprocessed outputs. **Requires GnuCOBOL.** CICS programs (17 of 31) are permanently skipped with reason `cics_no_translator` — this is by design, not a failure.
  - **Mode B (structural coverage):** Pure Python — scans each .cbl for paragraphs, 01-level items, CALL targets, SELECT/ASSIGN, EXEC CICS/SQL presence. Compares against data\facts\<PROG>.json. Runs for **all 31 programs**. No GnuCOBOL dependency.
- **Inputs:** data\raw\cbl\*.cbl, data\facts\<PROG>.json
- **Outputs:** validation\reconstructed\cbl\<PROG>.pre.cbl (Mode A only), validation\reports\<PROG>.validation.json, validation\reports\summary.json
- **Gate dependency:** None (post-IR validation — primary domain gate)
- **Notes:** Exit 0 = all PASS. Exit 1 = any FAIL. Exit 2 = fatal input error. Mode B is pure Python — no LLMs, no network, no GnuCOBOL. GnuCOBOL is only required for Mode A; if `cobc` is not on PATH, Mode A exits with a clear `cobc not found on PATH` message and Mode B still runs.

### extract_cfg_local.py
- **Location:** scripts\ (Batch 1 promoted from carddemo_imported)
- **Origin:** CarDemo
- **Status:** ACTIVE
- **Purpose:** Lightweight CFG extractor — produces paragraph list, PERFORM/GO TO edges, data items, CICS commands, dead-code detection. Canonical CFG extraction path.
- **Inputs:** --source (COBOL .cbl), --output (JSON path)
- **Outputs:** data\cfg\<PROG>_cfg.json
- **Gate dependency:** None (prerequisite tool)
- **Notes:** Uses `cobc -E` for copybook expansion when available, but the core paragraph extraction is Python regex. WARNING: extract_paragraphs() uses loose regex (’\s{0,3}'), NOT the fixed-column Area-A rule locked in Section 3.1 — do NOT use as a replacement for data_flow.py paragraph detection. analyze_flow() and extract_data_items() are safe to port selectively.

### extract_cfg_summary.py
- **Location:** scripts\ (Batch 1 promoted)
- **Origin:** CarDemo
- **Status:** ACTIVE
- **Purpose:** Rolls up per-program CFG data into cross-program summary — call graph, dead paragraph inventory, CICS command list, reachability stats.
- **Inputs:** data\cfg\*_cfg.json
- **Outputs:** Cross-program CFG summary JSON
- **Gate dependency:** None (reporting)

### extract_fallthrough.py
- **Location:** scripts\ (promoted from carddemo_imported)
- **Origin:** CarDemo
- **Status:** ACTIVE
- **Purpose:** Derives paragraph-level fallthrough classification — whether each paragraph terminates explicitly (GO TO, STOP RUN, GOBACK, EXEC CICS RETURN/XCTL) or falls through implicitly.
- **Inputs:** --source (COBOL .cbl), --cfg (pass1_annotate.py output JSON)
- **Outputs:** data\fallthrough\<PROG>.json
- **Gate dependency:** Section 3.4
- **Notes:** Contains C-5 source-order assertion — halts with BLOCKED if paragraph line numbers are non-monotonic. LLM-FREE and deterministic.

### pass1_annotate.py
- **Location:** scripts\ (promoted from carddemo_imported)
- **Origin:** CarDemo
- **Status:** ACTIVE
- **Purpose:** Full deterministic verb-level annotator. Produces per-statement annotation records with verb, operands, operand types, CFG branch context, CICS branch detection, scope depth tracking, and call-graph edge resolution.
- **Inputs:** --src (COBOL .cbl), --cfg (Phase 0 CFG JSON), --program-id, --out
- **Outputs:** data\pass1\<PROG>_annotations.json
- **Gate dependency:** Section 3.4
- **Notes:** Prerequisite for extract_fallthrough.py. Already tracks current_section internally. Uses `cobc -E` if available for copybook expansion; not a hard requirement for the annotation logic itself.

### extract_paragraph_io.py
- **Location:** scripts\ (Batch 1 promoted)
- **Origin:** CarDemo
- **Status:** ACTIVE
- **Purpose:** Per-paragraph READ/WRITE/REWRITE/DELETE/START file I/O summary.
- **Inputs:** pass1 annotation JSON
- **Outputs:** Per-program paragraph I/O JSON
- **Gate dependency:** None (Phase 2 IR enrichment)
- **Notes:** Use as cross-check against data_flow.py reads/mutates for file I/O verbs.

### extract_file_control.py
- **Location:** scripts\ (Batch 1 promoted)
- **Origin:** CarDemo
- **Status:** ACTIVE
- **Purpose:** Extracts FD entries — SELECT/ASSIGN pairs, ORGANIZATION, ACCESS MODE, RECORD KEY, file status variables.
- **Inputs:** data\raw\cbl\*.cbl
- **Outputs:** data\file_control\<PROG>.json
- **Gate dependency:** None (Phase 2 IR enrichment)

### para_diff.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Compares data_flow.py paragraph count (local) against extract_facts.py ground truth (facts) and reports delta per program.
- **Inputs:** data\data_flow\<PROG>.json, data\facts\<PROG>.json
- **Outputs:** Console WARNING lines, consumed by generate_report.py
- **Gate dependency:** Sections 3.1, 3.2, 3.3, 3.4

### generate_report.py
- **Location:** (repo root)
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Parses data_flow.py --all output and generates structured JSON + Markdown audit reports.
- **Inputs:** stdout of data_flow.py --all
- **Outputs:** audit\3_4_warning_baseline.json, audit\3_4_warning_baseline.md
- **Gate dependency:** Section 3.4
- **Notes:** audit\3_4_warning_baseline.json is the locked spec anchor for 3.4 — do not overwrite until 3.4 gate closes.

### config.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Shared configuration — paths, constants, schema versioning used by all native scripts.
- **Gate dependency:** All (shared dependency)

### schema.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** JSON schema definitions for all extractor outputs — data_flow, byte_layout, facts, annotations, canonical IR.
- **Gate dependency:** All (shared dependency)
- **Notes:** SCHEMA_VERSION bump at Section 3.4 gate close managed here.

### cobol_parse_utils.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Shared regex patterns and paragraph extraction utilities used by validate_roundtrip.py and hermes_v11_combined_extractor.py.
- **Gate dependency:** All that use paragraph extraction.

### validate_section34_diagnosis.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Paragraph count validator for Section 3.4 diagnosis.
- **Gate dependency:** Section 3.4

### validate_byte_layout.py
- **Location:** scripts\ (Batch 1 promoted)
- **Origin:** CarDemo
- **Status:** ACTIVE
- **Purpose:** Validates byte layout JSON for structural integrity — contiguous offsets, correct REDEFINES sizing, OCCURS multiplier totals, no overlapping ranges.
- **Inputs:** data\byte_layouts\<PROG>.json
- **Gate dependency:** None (post-IR validation)

### validate_codepage.py
- **Location:** scripts\ (Batch 1 promoted)
- **Origin:** CarDemo
- **Status:** ACTIVE
- **Purpose:** Checks COBOL source files for consistent encoding in sequence/indicator/code areas. Catches CRLF + mixed encoding issues.
- **Inputs:** data\raw\cbl\*.cbl
- **Gate dependency:** None (pre-pipeline lint)
- **Notes:** Should run before data_flow.py --all as a pre-condition check.

### validate_mutations.py
- **Location:** scripts\ (Batch 1 promoted)
- **Origin:** CarDemo
- **Status:** ACTIVE
- **Purpose:** Validates that every field listed as mutated in the IR has a reachable write path from the paragraph that claims the mutation.
- **Gate dependency:** None (post-IR validation)

### __init__.py
- **Location:** scripts\
- **Status:** ACTIVE
- **Purpose:** Makes scripts\ a Python package — enables cross-script imports.
- **Gate dependency:** All
- **Notes:** Must NOT be deleted.

### semantic_extract.py
- **Location:** scripts\
- **Status:** SUPERSEDED
- **Purpose:** Thin re-export shim delegating to hermes_v11_combined_extractor.py for backward compatibility.
- **Gate dependency:** None
- **Notes:** Superseded. DO NOT add logic here. Safe to archive.

### fix_fm2.py
- **Location:** scripts\
- **Status:** SUPERSEDED
- **Purpose:** One-shot patch script already executed. Rewrote the Failure Mode 2 section in a specific post-mortem file.
- **Gate dependency:** None
- **Notes:** Already ran. Safe to move to scripts\archive\ or delete.

---

## Section 2 — scripts\carddemo_imported\ (CarDemo Reference Archive)

> Reference archive only. All Batch 1 scripts have been promoted to scripts\.
> Remaining Batch 2 dependency-chain scripts stay here pending promotion.
> See carddemo_imported\README.md for full batch tracking.

### Batch 2 — Pending Promotion
| Script | Status | Notes |
|---|---|---|
| assemble_v1_2.py | REFERENCE | Promoted and renamed to scripts\assemble_canonical.py |
| validate_fallthrough.py | REFERENCE | Pending promotion to scripts\validate_fallthrough.py |
| validate_pass1.py | REFERENCE | Pending promotion to scripts\validate_pass1.py |

---

## Section 3 — Not Applicable (carddemo_imported only)

| Filename | Reason Not Applicable |
|---|---|
| pass2_llm.py | LLM enrichment — SecuraTron domain |
| pass2_override.py | LLM output override — SecuraTron domain |
| pass2_template.py | Markdown skeleton — carddemo output format only |
| pass3_run.py | Final document assembly — carddemo-specific |
| pass3_synthesize.py | Final document assembly — carddemo-specific |
| validate_pass2.py | Validates LLM enrichment — SecuraTron domain |
| validate_pass3.py | Validates final doc assembly — carddemo-specific |
| validate_t01–03.py | CarDemo eval task validators — not applicable |
| score_t04.py | CarDemo eval task T04 scorer — not applicable |
| *.sh / *.awk | Shell/AWK utilities for mainframe or CI — not applicable on Windows |

---

## Section 4 — CarDemo Import Progress

| Batch | Status | Scripts |
|---|---|---|
| Batch 1 — Independent | ✅ COMPLETE | validate_byte_layout, validate_codepage, validate_mutations, extract_cfg_local, extract_cfg_summary, extract_file_control, extract_paragraph_io, extract_byte_layout |
| Batch 2 — Dependency chain | ⏳ PENDING | validate_fallthrough, validate_pass1 (assemble_v1_2 already promoted as assemble_canonical.py) |
| Cleanup — Not applicable | ⏳ PENDING | 23 inapplicable files (shell scripts, pass2/3, carddemo validators) |

---

## Section 5 — TODO Scripts Not Yet Written

| Script | Location (planned) | Purpose |
|---|---|---|
| generate_canonical.py | scripts\ | Orchestrator — runs all extractors in correct dependency order for all 31 programs. |
| L001_codepage.py | validation\lint_cobol\rules\ | Lint rule ported from validate_codepage.py — pre-pipeline source encoding check. |
| para_diff_v2.py | scripts\ | Upgraded para_diff using (section_name, paragraph_name) tuples. Required after 3.4 lands. |

---

## Appendix A — CobolWalker v0.1 goto_targets Blind Spots

**Last updated:** 2026-05-19 (confirmed correct walker behavior, not bugs)

The walker traverses only `performs` + `falls_through_to` edges. Programs where
goto_targets are the primary control-flow mechanism show low `live_count` under
`walk(include_dead_code=False)`. All confirmed as expected walker behavior.
Baseline sums: **live=205, full=518** across 31 programs.

| Program | live_count | full_count | Notes |
|---|---|---|---|
| CBSTM03A | 1 | 25 | goto-driven dispatch (7 blind targets) |
| CBSTM03B | 5 | 14 | goto-driven exit targets (5 blind targets) |
| COACTUPC | 1 | 85 | CICS program, goto-heavy |
| COACTVWC | 1 | 34 | CICS program, goto-heavy |
| COBIL00C | 2 | 16 | goto-based dispatch |
| COCRDLIC | 1 | 39 | CICS program, goto-heavy |
| COMEN01C | 1 | 7 | goto-based dispatch |
| CORPT00C | 1 | 10 | goto-based dispatch |
| COSGN00C | 1 | 6 | goto-based dispatch |
| COTRN00C | 1 | 16 | goto-based dispatch |
| COTRN01C | 2 | 9 | goto-based dispatch |
| COUSR00C | 1 | 16 | goto-based dispatch |
| COUSR01C | 2 | 9 | goto-based dispatch |
| COUSR02C | 2 | 11 | goto-based dispatch |
| COUSR03C | 2 | 11 | goto-based dispatch |

goto_targets traversal deferred to CobolWalker v0.2.
Consumers needing full goto coverage must consult `paragraph["goto_targets"]` from CobolProgramDict.

---

## Appendix B — Current Folder Structure (post-Phase 8)

> Run to refresh: `Get-ChildItem C:\work\HermesCOBOL\scripts\ -Recurse -Depth 1 | Select-Object FullName`
> Last manually updated: 2026-06-30 (rev 8)

```
scripts\
  __init__.py
  config.py
  schema.py
  cobol_parse_utils.py
  hermes_v11_combined_extractor.py     <- PRIMARY EXTRACTOR
  data_flow.py
  extract_facts.py
  byte_layout.py
  extract_byte_layout.py
  extract_cfg_local.py
  extract_cfg_summary.py
  extract_fallthrough.py
  extract_paragraph_io.py
  extract_file_control.py
  pass1_annotate.py
  assemble_canonical.py
  cobol_program_dict.py
  cobol_walker.py
  honcho_loader.py
  load_corpus.py
  para_diff.py
  generate_report.py
  validate_roundtrip.py
  validate_byte_layout.py
  validate_codepage.py
  validate_mutations.py
  validate_section34_diagnosis.py
  audit_cobol_walker.py
  semantic_extract.py                  <- SUPERSEDED (shim only)
  fix_fm2.py                           <- SUPERSEDED (one-shot, already ran)
  SCRIPTS_INVENTORY.md
  carddemo_imported\                   <- reference archive
```

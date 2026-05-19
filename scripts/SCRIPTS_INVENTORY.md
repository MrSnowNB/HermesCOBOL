# HermesCOBOL — Scripts Inventory (Living Document)

**Last updated:** 2026-05-18 (rev 6 — Added "CobolWalker v0.1 — goto_targets blind spots" pre-implementation audit section per SPEC-CobolWalker.md)
**Branch:** audit/3.4-local-second-opinion
**Repo root:** C:\work\HermesCOBOL
**Maintainer:** Update this file whenever a script is added, removed, or changes status.

> NOTE: CarDemo scripts live in scripts\carddemo_imported\ (previously scripts\scripts\).
> Batch 1 independent scripts have been promoted to scripts\. Batch 2 dependency-chain
> scripts are pending promotion. See carddemo_imported\README.md for details.

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

## Section 1 — scripts\ (HermesCOBOL Native)

### data_flow.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Main extractor — parses COBOL source and produces paragraph-level data flow JSON including reads, mutates, call graph, and unresolved operands.
- **Inputs:** data\raw\cbl\*.cbl (single file or --all for 31 files)
- **Outputs:** data\data_flow\<PROG>.json per program
- **Gate dependency:** Sections 2, 3.1, 3.2, 3.3, 3.4
- **Notes:** SCHEMA_VERSION currently "1.2" — bumps to "1.3" at Section 3.4 gate close. extract_paragraphs() will gain section_name field in 3.4. Frozen contracts: _normalise_source, _join_source_lines, extract_paragraphs, _is_area_a_paragraph, _mask_literals, _dispatch_inline, _parse_call.

### extract_facts.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Produces ground-truth paragraph count and metadata per program, used by para_diff.py as the facts baseline for delta comparison.
- **Inputs:** data\raw\cbl\*.cbl
- **Outputs:** data\facts\<PROG>.json per program
- **Gate dependency:** Sections 3.1, 3.4
- **Notes:** Currently produces same undercount as data_flow.py for COACTUPC (85 vs 87), COACTVWC (34 vs 36), COCRDLIC (39 vs 41). Both extractors must be fixed together in 3.4. Pre-fix snapshot saved to data\facts.snapshot_before_pipeline\.

### byte_layout.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Extracts working storage byte layout — offsets, sizes, PIC types, OCCURS multipliers, REDEFINES groupings — per program.
- **Inputs:** data\raw\cbl\*.cbl
- **Outputs:** data\byte_layouts\<PROG>.json per program
- **Gate dependency:** Section 2
- **Notes:** Frozen. validate_byte_layout.py (CarDemo port) will be added as its validator.

### para_diff.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Compares data_flow.py paragraph count (local) against extract_facts.py ground truth (facts) and reports delta per program.
- **Inputs:** data\data_flow\<PROG>.json, data\facts\<PROG>.json
- **Outputs:** Console WARNING lines, consumed by generate_report.py
- **Gate dependency:** Sections 3.1, 3.2, 3.3, 3.4
- **Notes:** data\facts\ was deleted in May 7 cleanup and restored 2026-05-12. Three known close-mismatch warnings (COACTUPC, COACTVWC, COCRDLIC) deferred to 3.4.

### generate_report.py
- **Location:** (repo root)
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Parses data_flow.py --all output and generates structured JSON + Markdown audit reports. Produced audit\3_4_warning_baseline.json and .md.
- **Inputs:** stdout of data_flow.py --all (piped or invoked internally)
- **Outputs:** audit\3_4_warning_baseline.json, audit\3_4_warning_baseline.md
- **Gate dependency:** Section 3.4
- **Notes:** audit\3_4_warning_baseline.json is the locked spec anchor for 3.4 — do not overwrite until 3.4 gate closes.

### config.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Shared configuration module — paths, constants, and schema versioning used by all native scripts.
- **Inputs:** — (imported by other scripts)
- **Outputs:** — (module only)
- **Gate dependency:** All (shared dependency)
- **Notes:** Import target for data_flow.py, byte_layout.py, extract_facts.py, para_diff.py.

### schema.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** JSON schema definitions for all extractor outputs — data_flow, byte_layout, facts, annotations, canonical IR.
- **Inputs:** — (imported by other scripts)
- **Outputs:** — (module only)
- **Gate dependency:** All (shared dependency)
- **Notes:** SCHEMA_VERSION bump at Section 3.4 gate close will be managed here.

### hermes_v11_combined_extractor.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** REFERENCE
- **Purpose:** Legacy combined extractor from HermesCOBOL v1.1 — superseded by modular extractors (data_flow.py, byte_layout.py, extract_facts.py).
- **Inputs:** data\raw\cbl\*.cbl
- **Outputs:** N/A (superseded)
- **Gate dependency:** None
- **Notes:** Kept for historical reference. Do not use in new pipeline work.

### fix_fm2.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** SUPERSEDED
- **Purpose:** One-shot patch script — rewrites the Failure Mode 2 section heading and body in audit\3.4-close-out\postmortems\local-run-2026-05-11.md. Not a pipeline extractor. Already executed.
- **Inputs:** audit\3.4-close-out\postmortems\local-run-2026-05-11.md (hardcoded absolute path)
- **Outputs:** Overwrites the same post-mortem file in-place
- **Gate dependency:** None (one-shot maintenance script)
- **Notes:** Already ran. Post-mortem file is already patched. Safe to move to scripts\archive\ or delete. Does NOT import data_flow, config, or schema.

### validate_roundtrip.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Deterministic round-trip validator — runs GnuCOBOL preprocessing on non-CICS programs and performs structural coverage checks comparing raw COBOL source against extract_facts.py ground truth.
- **Inputs:** data\raw\cbl\*.cbl, data\facts\<PROG>.json
- **Outputs:** validation\reconstructed\cbl\<PROG>.pre.cbl, validation\reports\<PROG>.validation.json, validation\reports\summary.json
- **Gate dependency:** None (post-IR validation)
- **Notes:** Imports scripts.config for paths only. Does NOT import data_flow, schema, or any other scripts module. Read-only against data/raw/ and data/facts/. Writes only under validation/. Safe to leave in scripts\.

### semantic_extract.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** SUPERSEDED
- **Purpose:** Thin re-export shim that delegates to hermes_v11_combined_extractor.py for backward compatibility with external scripts importing from semantic_extract.
- **Inputs:** — (no direct inputs, re-exports functions from hermes_v11_combined_extractor.py)
- **Outputs:** — (module only, re-exports symbols)
- **Gate dependency:** None (superseded by hermes_v11_combined_extractor.py)
- **Notes:** Superseded by hermes_v11_combined_extractor.py. DO NOT add logic here. Imports scripts.hermes_v11_combined_extractor. Safe to archive but kept for backward compatibility with external imports.

### __init__.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Makes scripts\ a Python package — enables cross-script imports such as `from scripts.config import ...` and `from scripts.schema import ...`.
- **Inputs:** — (package marker, no inputs)
- **Outputs:** — (no outputs)
- **Gate dependency:** All (shared dependency)
- **Notes:** Must NOT be deleted. Removing this file breaks all intra-package imports across data_flow.py, byte_layout.py, extract_facts.py, para_diff.py, and any future scripts that import config or schema.

---

## Section 2 — scripts\carddemo_imported\ (CarDemo Reference Archive)

> These files were copied directly from aws-mainframe-modernization-carddemo\scripts\.
> The folder was renamed from scripts\scripts\ to scripts\carddemo_imported\ on 2026-05-12.
> It is a reference archive — 8 Batch 1 scripts have been promoted to scripts\.
> The remaining 13 scripts (Batch 2 dependency chain + inapplicable) stay here.

### extract_fallthrough.py
- **Location:** scripts\carddemo_imported\ (Batch 2 — pending promotion)
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Derives paragraph-level fallthrough classification — whether each paragraph terminates explicitly (GO TO, STOP RUN, GOBACK, EXEC CICS RETURN/XCTL) or implicitly falls through to the next paragraph in source order. The implicit fallthrough case is the root cause of the -2 delta in COACTUPC, COACTVWC, COCRDLIC.
- **Inputs:** --source (COBOL .cbl file), --cfg (pass1_annotate.py output JSON)
- **Outputs:** validation\pass1\fallthrough\<PROG>.json
- **Gate dependency:** Section 3.4
- **Notes:** Contains C-5 source-order assertion — halts with BLOCKED if paragraph line numbers are non-monotonic. LLM-FREE and deterministic. Requires pass1_annotate.py output as prerequisite. TARGET LOCATION when promoted: scripts\extract_fallthrough.py.

### pass1_annotate.py
- **Location:** scripts\carddemo_imported\ (Batch 2 — pending promotion)
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Full deterministic verb-level annotator. Produces per-statement annotation records with verb, operands, operand types, CFG branch context, CICS branch detection, scope depth tracking, and call-graph edge resolution. Prerequisite for extract_fallthrough.py.
- **Inputs:** --src (COBOL .cbl), --cfg (Phase 0 CFG JSON), --program-id, --out
- **Outputs:** validation\pass1\<PROG>_annotations.json
- **Gate dependency:** Section 3.4
- **Notes:** Already tracks current_section internally — this is the section-awareness logic needed for the 3.4 fix. Requires cobc -E (GNU COBOL) in PATH. TARGET LOCATION when promoted: scripts\pass1_annotate.py.

### validate_fallthrough.py
- **Location:** scripts\carddemo_imported\ (Batch 2 — pending promotion)
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Validates extract_fallthrough.py output — checks for non-circular fallthrough chains, valid falls_through_to targets, correct implicit end-of-program placement.
- **Inputs:** validation\pass1\fallthrough\<PROG>.json
- **Outputs:** Console PASS/FAIL per program
- **Gate dependency:** Section 3.4
- **Notes:** Will become the basis for TestSectionAwareFallthrough test class required by 3.4 gate spec. TARGET LOCATION when promoted: scripts\validate_fallthrough.py.

### validate_byte_layout.py
- **Location:** scripts\carddemo_imported\ (copy promoted to scripts\)
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Validates byte layout JSON for structural integrity — contiguous offsets, correct REDEFINES sizing, OCCURS multiplier totals, no overlapping ranges.
- **Inputs:** data\byte_layouts\<PROG>.json (path needs adaptation)
- **Outputs:** Console PASS/FAIL per program
- **Gate dependency:** None (post-IR validation)
- **Notes:** Paths reference carddemo's validation\ tree — adapt to data\byte_layouts\ for HermesCOBOL use. Promoted to scripts\ on 2026-05-12 (Batch 1).

### validate_mutations.py
- **Location:** scripts\carddemo_imported\ (copy promoted to scripts\)
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Validates that every field listed as mutated in the IR has a reachable write path from the paragraph that claims the mutation. Deterministic complement to the unresolved_count metric.
- **Inputs:** pass1 annotation JSON + data_flow JSON (paths need adaptation)
- **Outputs:** Console PASS/FAIL per program
- **Gate dependency:** None (post-IR validation)
- **Notes:** Promoted to scripts\ on 2026-05-12 (Batch 1).

### validate_codepage.py
- **Location:** scripts\carddemo_imported\ (copy promoted to scripts\)
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Checks COBOL source files for consistent encoding in sequence/indicator/code areas. Catches CRLF + mixed encoding issues that could silently break _normalise_source.
- **Inputs:** data\raw\cbl\*.cbl
- **Outputs:** Console PASS/FAIL per program
- **Gate dependency:** None (pre-pipeline lint)
- **Notes:** Should run before data_flow.py --all as a pre-condition check. Candidate for validation\lint_cobol\rules\L001_codepage.py. Promoted to scripts\ on 2026-05-12 (Batch 1).

### extract_cfg_local.py
- **Location:** scripts\carddemo_imported\ (copy promoted to scripts\)
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Lightweight CFG extractor using cobc -E for copybook expansion. Produces paragraph list, PERFORM/GO TO edges, data items, CICS commands, dead-code detection. Prerequisite CFG JSON input for pass1_annotate.py.
- **Inputs:** --source (COBOL .cbl), --output (JSON path)
- **Outputs:** validation\structure\<PROG>_cfg.json
- **Gate dependency:** None (prerequisite tool)
- **Notes:** WARNING — extract_paragraphs() uses loose regex (\s{0,3}), NOT the fixed-column Area-A rule locked in Section 3.1. Do NOT use as a replacement for data_flow.py paragraph detection. analyze_flow() and extract_data_items() functions are safe to port selectively. Requires cobc -E in PATH. Promoted to scripts\ on 2026-05-12 (Batch 1).

### extract_cfg_summary.py
- **Location:** scripts\carddemo_imported\ (copy promoted to scripts\)
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Rolls up per-program CFG data into a cross-program summary — call graph, dead paragraph inventory, CICS command list, reachability stats.
- **Inputs:** validation\structure\*_cfg.json (path needs adaptation to data\data_flow\)
- **Outputs:** Cross-program summary JSON
- **Gate dependency:** None (reporting)
- **Notes:** Upgrade candidate for generate_report.py. Promoted to scripts\ on 2026-05-12 (Batch 1).

### extract_file_control.py
- **Location:** scripts\carddemo_imported\ (copy promoted to scripts\)
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Extracts FD (File Description) entries — SELECT/ASSIGN pairs, ORGANIZATION, ACCESS MODE, RECORD KEY, file status variables — per program.
- **Inputs:** data\raw\cbl\*.cbl (path needs adaptation)
- **Outputs:** Per-program file control JSON
- **Gate dependency:** None (Phase 2 IR enrichment)
- **Notes:** Not needed for Section 3.4. Planned output: data\file_control\<PROG>.json. Promoted to scripts\ on 2026-05-12 (Batch 1).

### extract_paragraph_io.py
- **Location:** scripts\carddemo_imported\ (copy promoted to scripts\)
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Per-paragraph READ/WRITE/REWRITE/DELETE/START file I/O summary — which files each paragraph accesses and in what mode.
- **Inputs:** pass1 annotation JSON (path needs adaptation)
- **Outputs:** Per-program paragraph I/O JSON
- **Gate dependency:** None (Phase 2 IR enrichment)
- **Notes:** Overlaps with data_flow.py reads/mutates for file I/O verbs. Use as cross-check validator rather than primary extractor. Promoted to scripts\ on 2026-05-12 (Batch 1).

### assemble_v1_2.py
- **Location:** scripts\carddemo_imported\ (Batch 2 — pending promotion)
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Merges all extractor outputs — pass1 annotations, fallthrough data, byte layouts, file control, CFG summaries — into a single canonical IR record per program. This is the Phase 2 merge step that produces data\canonical\<PROG>.json.
- **Inputs:** All extractor JSON outputs across data\ tree
- **Outputs:** data\canonical\<PROG>.json (path needs adaptation)
- **Gate dependency:** None (Phase 2, after all gates closed)
- **Notes:** Will be renamed assemble_canonical.py when promoted. This is the final assembly script for the 100% faithful IR. TARGET LOCATION when promoted: scripts\assemble_canonical.py.

### validate_pass1.py
- **Location:** scripts\carddemo_imported\ (Batch 2 — pending promotion)
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Validates pass1_annotate.py output completeness — every paragraph has at least one verb annotation, no orphaned annotations outside a known paragraph.
- **Inputs:** validation\pass1\<PROG>_annotations.json
- **Outputs:** Console PASS/FAIL
- **Gate dependency:** Section 3.4
- **Notes:** Maps directly to a HermesCOBOL pre-3.4 gate check. TARGET LOCATION when promoted: scripts\validate_pass1.py.

### extract_byte_layout.py
- **Location:** scripts\carddemo_imported\ (copy promoted to scripts\)
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Byte layout extractor from CarDemo — produces working storage byte layout JSON per program. Duplicate functionality of HermesCOBOL native byte_layout.py.
- **Inputs:** data\raw\cbl\*.cbl
- **Outputs:** validation\byte_layouts\<PROG>.json (path needs adaptation)
- **Gate dependency:** None (post-IR validation)
- **Notes:** Functionality overlaps with scripts\byte_layout.py. Decided to keep both — byte_layout.py (HermesCOBOL native) is preferred. Promoted to scripts\ on 2026-05-12 (Batch 1).

---

## Section 3 — Files Present in scripts\carddemo_imported\ but NOT for HermesCOBOL use

List these files with a one-line reason why they are not applicable.
Do NOT write full entries for these — just a table.

| Filename | Reason Not Applicable |
|---|---|
| pass2_llm.py | LLM enrichment — SecuraTron domain, not deterministic pipeline |
| pass2_override.py | LLM output override — SecuraTron domain |
| pass2_template.py | Markdown skeleton generation — carddemo output format only |
| pass3_run.py | Final document assembly — carddemo-specific |
| pass3_synthesize.py | Final document assembly — carddemo-specific |
| compile_batch.jcl.template | Not present on disk — may have been removed or renamed |
| local_compile.sh | Shell script — mainframe compile, not applicable on Windows |
| remote_compile.sh | Shell script — remote mainframe compile |
| remote_refresh.sh | Shell script — remote environment refresh |
| remote_submit.sh | Shell script — remote job submission |
| run_full_batch.sh | Shell script — carddemo batch execution |
| run_interest_calc.sh | Shell script — carddemo interest calculation job |
| run_posting.sh | Shell script — carddemo posting job |
| run_sweBench.sh | Shell script — SWE-bench evaluation harness |
| upld_module.sh | Shell script — module upload to mainframe |
| git-addSrcVersionInfo.sh | Shell script — git version stamping utility |
| pad.awk | AWK utility — fixed-width field padding for JCL |
| score_t04.py | CarDemo eval task T04 scorer — not applicable |
| validate_pass2.py | Validates LLM enrichment output — SecuraTron domain |
| validate_pass3.py | Validates final document assembly — carddemo-specific |
| validate_t01.py | CarDemo task T01 validator — not applicable |
| validate_t02.py | CarDemo task T02 validator — not applicable |
| validate_t02r.py | CarDemo task T02r validator — not applicable |
| validate_t03.py | CarDemo task T03 validator — not applicable |
| markers\ | CarDemo pipeline state markers directory — not applicable |

---

## Section 4 — CarDemo Import Progress

| Batch | Status | Scripts |
|---|---|---|
| Batch 1 — Independent | ✅ COMPLETE | validate_byte_layout, validate_codepage, validate_mutations, extract_cfg_local, extract_cfg_summary, extract_file_control, extract_paragraph_io, extract_byte_layout |
| Batch 2 — Dependency chain | ⏳ PENDING | pass1_annotate, extract_fallthrough, validate_fallthrough, validate_pass1, assemble_v1_2 |
| Cleanup — Not applicable | ⏳ PENDING | 23 inapplicable files (shell scripts, pass2/3, carddemo validators) |

  > Folder renamed: scripts\scripts\ → scripts\carddemo_imported\ (2026-05-12)
  > See scripts\carddemo_imported\README.md for full batch tracking.

---

## Section 5 — TODO Scripts Not Yet Written

| Script | Location (planned) | Purpose |
|---|---|---|
| assemble_canonical.py | scripts\ | Phase 2 driver — merges all extractor outputs into data\canonical\<PROG>.json for all 31 programs. Renamed from assemble_v1_2.py. |
| generate_canonical.py | scripts\ | Orchestrator — runs all extractors in correct dependency order for all 31 programs. |
| L001_codepage.py | validation\lint_cobol\rules\ | Lint rule ported from validate_codepage.py — pre-pipeline source encoding check. |
| para_diff_v2.py | scripts\ | Upgraded para_diff using (section_name, paragraph_name) tuples instead of flat names. Required after 3.4 lands. |

---

## Appendix A — Actual Folder Structure Observed (PRE-RENAME SNAPSHOT)

> Snapshot taken: 2026-05-12 (pre-Batch-1 promotion, pre-rename)
> **SUPERSEDED** — scripts\scripts\ has since been renamed to scripts\carddemo_imported\
> and 8 Batch 1 scripts promoted to scripts\. See Appendix B for current structure.

```
C:\work\HermesCOBOL\scripts\scripts                          ← RENAMED to carddemo_imported\
C:\work\HermesCOBOL\scripts\__pycache__
C:\work\HermesCOBOL\scripts\byte_layout.py
C:\work\HermesCOBOL\scripts\config.py
C:\work\HermesCOBOL\scripts\data_flow.py
C:\work\HermesCOBOL\scripts\extract_facts.py
C:\work\HermesCOBOL\scripts\fix_fm2.py
C:\work\HermesCOBOL\scripts\hermes_v11_combined_extractor.py
C:\work\HermesCOBOL\scripts\para_diff.py
C:\work\HermesCOBOL\scripts\schema.py
C:\work\HermesCOBOL\scripts\SCRIPTS_INVENTORY.md
C:\work\HermesCOBOL\scripts\semantic_extract.py
C:\work\HermesCOBOL\scripts\validate_roundtrip.py
C:\work\HermesCOBOL\scripts\__init__.py
C:\work\HermesCOBOL\scripts\scripts\assemble_v1_2.py         ← now carddemo_imported\
C:\work\HermesCOBOL\scripts\scripts\extract_byte_layout.py   ← now carddemo_imported\
C:\work\HermesCOBOL\scripts\scripts\extract_cfg_local.py     ← now carddemo_imported\
C:\work\HermesCOBOL\scripts\scripts\extract_cfg_summary.py   ← now carddemo_imported\
C:\work\HermesCOBOL\scripts\scripts\extract_fallthrough.py   ← now carddemo_imported\
C:\work\HermesCOBOL\scripts\scripts\extract_file_control.py  ← now carddemo_imported\
C:\work\HermesCOBOL\scripts\scripts\extract_paragraph_io.py  ← now carddemo_imported\
C:\work\HermesCOBOL\scripts\scripts\pass1_annotate.py        ← now carddemo_imported\
[... remaining files unchanged, all under carddemo_imported\ now]
```

---

## Appendix B — Current Folder Structure (post-Batch-1)

> Run this to refresh: Get-ChildItem C:\work\HermesCOBOL\scripts\ -Recurse -Depth 2 | Select-Object FullName
> Last manually updated: 2026-05-12 (rev 5)

```
C:\work\HermesCOBOL\scripts\carddemo_imported\       ← renamed from scripts\scripts\
C:\work\HermesCOBOL\scripts\__pycache__\
C:\work\HermesCOBOL\scripts\__init__.py
C:\work\HermesCOBOL\scripts\byte_layout.py
C:\work\HermesCOBOL\scripts\config.py
C:\work\HermesCOBOL\scripts\data_flow.py
C:\work\HermesCOBOL\scripts\extract_byte_layout.py   ← Batch 1 promoted
C:\work\HermesCOBOL\scripts\extract_cfg_local.py     ← Batch 1 promoted
C:\work\HermesCOBOL\scripts\extract_cfg_summary.py   ← Batch 1 promoted
C:\work\HermesCOBOL\scripts\extract_facts.py
C:\work\HermesCOBOL\scripts\extract_file_control.py  ← Batch 1 promoted
C:\work\HermesCOBOL\scripts\extract_paragraph_io.py  ← Batch 1 promoted
C:\work\HermesCOBOL\scripts\fix_fm2.py
C:\work\HermesCOBOL\scripts\hermes_v11_combined_extractor.py
C:\work\HermesCOBOL\scripts\para_diff.py
C:\work\HermesCOBOL\scripts\schema.py
C:\work\HermesCOBOL\scripts\SCRIPTS_INVENTORY.md
C:\work\HermesCOBOL\scripts\semantic_extract.py
C:\work\HermesCOBOL\scripts\validate_byte_layout.py  ← Batch 1 promoted
C:\work\HermesCOBOL\scripts\validate_codepage.py     ← Batch 1 promoted
C:\work\HermesCOBOL\scripts\validate_mutations.py    ← Batch 1 promoted
C:\work\HermesCOBOL\scripts\validate_roundtrip.py
C:\work\HermesCOBOL\scripts\carddemo_imported\assemble_v1_2.py
C:\work\HermesCOBOL\scripts\carddemo_imported\extract_byte_layout.py
C:\work\HermesCOBOL\scripts\carddemo_imported\extract_cfg_local.py
C:\work\HermesCOBOL\scripts\carddemo_imported\extract_cfg_summary.py
C:\work\HermesCOBOL\scripts\carddemo_imported\extract_fallthrough.py
C:\work\HermesCOBOL\scripts\carddemo_imported\extract_file_control.py
C:\work\HermesCOBOL\scripts\carddemo_imported\extract_paragraph_io.py
C:\work\HermesCOBOL\scripts\carddemo_imported\pass1_annotate.py
C:\work\HermesCOBOL\scripts\carddemo_imported\validate_byte_layout.py
C:\work\HermesCOBOL\scripts\carddemo_imported\validate_codepage.py
C:\work\HermesCOBOL\scripts\carddemo_imported\validate_fallthrough.py
C:\work\HermesCOBOL\scripts\carddemo_imported\validate_mutations.py
C:\work\HermesCOBOL\scripts\carddemo_imported\validate_pass1.py
C:\work\HermesCOBOL\scripts\carddemo_imported\[...inapplicable shell scripts and py files]
C:\work\HermesCOBOL\scripts\carddemo_imported\README.md
```

---

## CobolWalker v0.1 — goto_targets blind spots (Pre-Implementation Audit)

**Audit date:** 2026-05-18  
**Status:** Documented before any CobolWalker implementation code was written (per SPEC requirement)  
**Run by:** Grok (pre-Step 2)  
**Reference:** SPEC-CobolWalker.md (Gate 3 / Plan pre-audit step)

### Summary
- Programs scanned: 31
- Programs containing `goto_targets` that fall **outside** the reachable set computed from `performs` + `falls_through_to` edges starting at `entry_paragraph`: **2**
- Total blind goto targets discovered: **12**

This is an **accepted limitation** of CobolWalker v0.1. The walker is intentionally defined to traverse only `performs` + `falls_through_to` (see SPEC Requirements). `goto_targets` are visible via `CobolProgramDict` but are deliberately not followed by `walk()`.

### Detailed Blind Spots

#### CBSTM03A (7 blind targets)
- Entry paragraph: `0000-START`
- Live paragraphs via performs + fallthrough: **1**
- Blind goto_targets:
  - `0000-START` → `8100-FILE-OPEN`
  - `0000-START` → `8500-READTRNX-READ`
  - `0000-START` → `9999-GOBACK`
  - `8100-FILE-OPEN` → `8100-TRNXFILE-OPEN`
  - `8400-ACCTFILE-OPEN` → `1000-MAINLINE`
  - `8500-READTRNX-READ` → `8500-READTRNX-READ` (self)
  - `8500-READTRNX-READ` → `8599-EXIT`

#### CBSTM03B (5 blind targets)
- Entry paragraph: `0000-START`
- Live paragraphs via performs + fallthrough: **5**
- Blind goto_targets:
  - `0000-START` → `9999-GOBACK`
  - `1000-TRNXFILE-PROC` → `1900-EXIT`
  - `2000-XREFFILE-PROC` → `2900-EXIT`
  - `3000-CUSTFILE-PROC` → `3900-EXIT`
  - `4000-ACCTFILE-PROC` → `4900-EXIT`

### Implications for CobolWalker v0.1
- Programs CBSTM03A and CBSTM03B contain significant control flow that is only expressed via GOTO (or equivalent).
- When using `CobolWalker(...).walk(include_dead_code=False)`, these targets will **not** be yielded unless they happen to also be reachable via PERFORM or fallthrough.
- Consumers (Hermes agent, semantic rules, etc.) that care about these paths must additionally consult `paragraph["goto_targets"]` from the underlying `CobolProgramDict`.
- This blind spot is explicitly called out so that downstream users do not assume the walker produces a complete control-flow closure.

**Next action (post v0.1):** Consider a v0.2 walker mode or separate `follow_gotos` flag if full coverage of these two programs becomes required.

Machine-readable audit artifact (for this run): `/tmp/gotoblindspots.json` (not committed).


---

## Section 6 � CobolWalker v0.1 Scripts

### cobol_walker.py
- **Location:** scripts- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Deterministic DFS walker over CobolProgramDict � yields paragraph names via performs + falls_through_to edges only. Supports include_dead_code=False (live paragraphs only) and include_dead_code=True (live + unvisited paragraphs in canonical source order).
- **Inputs:** CobolProgramDict instance (data\canonical\<PROG>.canonical.json)
- **Outputs:** Generator of paragraph name strings
- **Gate dependency:** CobolWalker v0.1 Gates 1�10 (all green)
- **Notes:** Does NOT follow goto_targets � see goto_targets blind spots section below. Deterministic across runs. Deduplication guaranteed (no paragraph yielded twice). Walker entry point: CobolWalker(prog).walk(include_dead_code=bool).

### audit_cobol_walker.py
- **Location:** scripts- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Walks all 31 programs under both flag settings and emits validation\walker-baseline.json containing per-program live_count, full_count, entry_paragraph, first_five, and last_three. Gate 10 regression hook � called by validate_roundtrip.py on every run.
- **Inputs:** data\canonical\*.canonical.json (all 31 programs)
- **Outputs:** validation\walker-baseline.json
- **Gate dependency:** CobolWalker v0.1 Gate 10 (green)
- **Notes:** On first run: creates baseline. On subsequent runs: verifies current walk output matches saved baseline � FAIL if diverged. Run standalone: python scriptsudit_cobol_walker.py. Baseline sums: live=205, full=518 across 31 programs.

---

## CobolWalker v0.1 � goto_targets Blind Spots (Post-Validation Update)

**Last updated:** 2026-05-19 (rev 7 � updated after v0.1 full gate validation)
**Status:** Accepted limitation. Documented per SPEC-CobolWalker.md.

The walker (performs + falls_through_to edges only) does not traverse goto_targets.
Programs where goto_targets are the primary control-flow mechanism show low live
counts under walk(include_dead_code=False). All confirmed as correct walker behavior.

| Program     | live_count | full_count | Notes                                      |
|-------------|------------|------------|--------------------------------------------|
| CBSTM03A    | 1          | 25         | goto-driven dispatch from 0000-START (7 blind targets) |
| CBSTM03B    | 5          | 14         | goto-driven exit targets (5 blind targets) |
| COACTUPC    | 1          | 85         | CICS program, goto-heavy                   |
| COACTVWC    | 1          | 34         | CICS program, goto-heavy                   |
| COBIL00C    | 2          | 16         | goto-based dispatch                        |
| COCRDLIC    | 1          | 39         | CICS program, goto-heavy                   |
| COMEN01C    | 1          | 7          | goto-based dispatch                        |
| CORPT00C    | 1          | 10         | goto-based dispatch                        |
| COSGN00C    | 1          | 6          | goto-based dispatch                        |
| COTRN00C    | 1          | 16         | goto-based dispatch                        |
| COTRN01C    | 2          | 9          | goto-based dispatch                        |
| COUSR00C    | 1          | 16         | goto-based dispatch                        |
| COUSR01C    | 2          | 9          | goto-based dispatch                        |
| COUSR02C    | 2          | 11         | goto-based dispatch                        |
| COUSR03C    | 2          | 11         | goto-based dispatch                        |

These are not bugs. goto_targets traversal is deferred to CobolWalker v0.2.
Consumers needing full goto coverage must additionally consult paragraph["goto_targets"]
from the underlying CobolProgramDict.


---

## Section 6 — CobolWalker v0.1 Scripts

### cobol_walker.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Deterministic DFS walker over CobolProgramDict — yields paragraph names via performs + falls_through_to edges only. Supports include_dead_code=False (live paragraphs only) and include_dead_code=True (live + unvisited paragraphs in canonical source order).
- **Inputs:** CobolProgramDict instance (data\canonical\<PROG>.canonical.json)
- **Outputs:** Generator of paragraph name strings
- **Gate dependency:** CobolWalker v0.1 Gates 1-10 (all green)
- **Notes:** Does NOT follow goto_targets — see goto_targets blind spots section below. Deterministic across runs. Deduplication guaranteed (no paragraph yielded twice). Walker entry point: CobolWalker(prog).walk(include_dead_code=bool).

### audit_cobol_walker.py
- **Location:** scripts\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Walks all 31 programs under both flag settings and emits validation\walker-baseline.json containing per-program live_count, full_count, entry_paragraph, first_five, and last_three. Gate 10 regression hook — called by validate_roundtrip.py on every run.
- **Inputs:** data\canonical\*.canonical.json (all 31 programs)
- **Outputs:** validation\walker-baseline.json
- **Gate dependency:** CobolWalker v0.1 Gate 10 (green)
- **Notes:** On first run: creates baseline. On subsequent runs: verifies current walk output matches saved baseline — FAIL if diverged. Run standalone: python scripts\audit_cobol_walker.py. Baseline sums: live=205, full=518 across 31 programs.

---

## CobolWalker v0.1 — goto_targets Blind Spots (Post-Validation Update)

**Last updated:** 2026-05-19 (rev 7 — updated after v0.1 full gate validation)
**Status:** Accepted limitation. Documented per SPEC-CobolWalker.md.

The walker (performs + falls_through_to edges only) does not traverse goto_targets.
Programs where goto_targets are the primary control-flow mechanism show low live
counts under walk(include_dead_code=False). All confirmed as correct walker behavior.

| Program     | live_count | full_count | Notes                                      |
|-------------|------------|------------|--------------------------------------------|
| CBSTM03A    | 1          | 25         | goto-driven dispatch from 0000-START (7 blind targets) |
| CBSTM03B    | 5          | 14         | goto-driven exit targets (5 blind targets) |
| COACTUPC    | 1          | 85         | CICS program, goto-heavy                   |
| COACTVWC    | 1          | 34         | CICS program, goto-heavy                   |
| COBIL00C    | 2          | 16         | goto-based dispatch                        |
| COCRDLIC    | 1          | 39         | CICS program, goto-heavy                   |
| COMEN01C    | 1          | 7          | goto-based dispatch                        |
| CORPT00C    | 1          | 10         | goto-based dispatch                        |
| COSGN00C    | 1          | 6          | goto-based dispatch                        |
| COTRN00C    | 1          | 16         | goto-based dispatch                        |
| COTRN01C    | 2          | 9          | goto-based dispatch                        |
| COUSR00C    | 1          | 16         | goto-based dispatch                        |
| COUSR01C    | 2          | 9          | goto-based dispatch                        |
| COUSR02C    | 2          | 11         | goto-based dispatch                        |
| COUSR03C    | 2          | 11         | goto-based dispatch                        |

These are not bugs. goto_targets traversal is deferred to CobolWalker v0.2.
Consumers needing full goto coverage must additionally consult paragraph["goto_targets"]
from the underlying CobolProgramDict.

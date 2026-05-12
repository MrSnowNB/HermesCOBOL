# HermesCOBOL — Scripts Inventory (Living Document)

**Last updated:** 2026-05-12
**Branch:** audit/3.4-local-second-opinion
**Repo root:** C:\work\HermesCOBOL
**Maintainer:** Update this file whenever a script is added, removed, or changes status.

> NOTE: The CarDemo scripts were copied into scripts\scripts\ (nested folder).
> This is a known structural issue to be resolved. This inventory reflects
> the actual disk layout as of 2026-05-12.

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
- **Notes:** Currently produces same undercount as data_flow.py for COACTUPC (85 vs 87), COACTVWC (34 vs 36), COCRDLIC (39 vs 41). Both extractors must be fixed together in 3.4. Pre-fix snapshot saved to data\facts.snapshot_before_pipeline\ .

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
- **Location:** .\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Parses data_flow.py --all output and generates structured JSON + Markdown audit reports. Produced audit\3_4_warning_baseline.json and .md.
- **Inputs:** stdout of data_flow.py --all (piped or invoked internally)
- **Outputs:** audit\3_4_warning_baseline.json, audit\3_4_warning_baseline.md
- **Gate dependency:** Section 3.4
- **Notes:** audit\3_4_warning_baseline.json is the locked spec anchor for 3.4 — do not overwrite until 3.4 gate closes.

---

## Section 2 — scripts\scripts\ (CarDemo Port — Nested, Needs Restructuring)

> These files were copied directly from aws-mainframe-modernization-carddemo\scripts\.
> The folder is currently nested at scripts\scripts\ which is a structural issue.
> They are REFERENCE copies only — not yet wired into the HermesCOBOL pipeline.
> All paths below reflect the current nested location.

### extract_fallthrough.py
- **Location:** scripts\scripts\
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Derives paragraph-level fallthrough classification — whether each paragraph terminates explicitly (GO TO, STOP RUN, GOBACK, EXEC CICS RETURN/XCTL) or implicitly falls through to the next paragraph in source order. The implicit fallthrough case is the root cause of the -2 delta in COACTUPC, COACTVWC, COCRDLIC.
- **Inputs:** --source (COBOL .cbl file), --cfg (pass1_annotate.py output JSON)
- **Outputs:** validation\pass1\fallthrough\<PROG>.json
- **Gate dependency:** Section 3.4
- **Notes:** Contains C-5 source-order assertion — halts with BLOCKED if paragraph line numbers are non-monotonic. LLM-FREE and deterministic. Requires pass1_annotate.py output as prerequisite. TARGET LOCATION when promoted: scripts\extract_fallthrough.py.

### pass1_annotate.py
- **Location:** scripts\scripts\
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Full deterministic verb-level annotator. Produces per-statement annotation records with verb, operands, operand types, CFG branch context, CICS branch detection, scope depth tracking, and call-graph edge resolution. Prerequisite for extract_fallthrough.py.
- **Inputs:** --src (COBOL .cbl), --cfg (Phase 0 CFG JSON), --program-id, --out
- **Outputs:** validation\pass1\<PROG>_annotations.json
- **Gate dependency:** Section 3.4
- **Notes:** Already tracks current_section internally — this is the section-awareness logic needed for the 3.4 fix. Requires cobc -E (GNU COBOL) in PATH. TARGET LOCATION when promoted: scripts\pass1_annotate.py.

### validate_fallthrough.py
- **Location:** scripts\scripts\
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Validates extract_fallthrough.py output — checks for non-circular fallthrough chains, valid falls_through_to targets, correct implicit-end-of-program placement.
- **Inputs:** validation\pass1\fallthrough\<PROG>.json
- **Outputs:** Console PASS/FAIL per program
- **Gate dependency:** Section 3.4
- **Notes:** Will become the basis for TestSectionAwareFallthrough test class required by 3.4 gate spec. TARGET LOCATION when promoted: scripts\validate_fallthrough.py.

### validate_byte_layout.py
- **Location:** scripts\scripts\
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Validates byte layout JSON for structural integrity — contiguous offsets, correct REDEFINES sizing, OCCURS multiplier totals, no overlapping ranges.
- **Inputs:** data\byte_layouts\<PROG>.json (path needs adaptation)
- **Outputs:** Console PASS/FAIL per program
- **Gate dependency:** None (post-IR validation)
- **Notes:** Paths reference carddemo's validation\ tree — adapt to data\byte_layouts\ for HermesCOBOL use. TARGET LOCATION when promoted: scripts\validate_byte_layout.py.

### validate_mutations.py
- **Location:** scripts\scripts\
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Validates that every field listed as mutated in the IR has a reachable write path from the paragraph that claims the mutation. Deterministic complement to the unresolved_count metric.
- **Inputs:** pass1 annotation JSON + data_flow JSON (paths need adaptation)
- **Outputs:** Console PASS/FAIL per program
- **Gate dependency:** None (post-IR validation)
- **Notes:** TARGET LOCATION when promoted: scripts\validate_mutations.py.

### validate_codepage.py
- **Location:** scripts\scripts\
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Checks COBOL source files for consistent encoding in sequence/indicator/code areas. Catches CRLF + mixed encoding issues that could silently break _normalise_source.
- **Inputs:** data\raw\cbl\*.cbl
- **Outputs:** Console PASS/FAIL per program
- **Gate dependency:** None (pre-pipeline lint)
- **Notes:** Should run before data_flow.py --all as a pre-condition check. Candidate for validation\lint_cobol\rules\L001_codepage.py. TARGET LOCATION when promoted: scripts\validate_codepage.py.

### extract_cfg_local.py
- **Location:** scripts\scripts\
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Lightweight CFG extractor using cobc -E for copybook expansion. Produces paragraph list, PERFORM/GO TO edges, data items, CICS commands, dead-code detection. Prerequisite CFG JSON input for pass1_annotate.py.
- **Inputs:** --source (COBOL .cbl), --output (JSON path)
- **Outputs:** validation\structure\<PROG>_cfg.json
- **Gate dependency:** None (prerequisite tool)
- **Notes:** WARNING — extract_paragraphs() uses loose regex (\s{0,3}), NOT the fixed-column Area-A rule locked in Section 3.1. Do NOT use as a replacement for data_flow.py paragraph detection. analyze_flow() and extract_data_items() functions are safe to port selectively. Requires cobc -E in PATH. TARGET LOCATION when promoted: scripts\extract_cfg_local.py.

### extract_cfg_summary.py
- **Location:** scripts\scripts\
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Rolls up per-program CFG data into a cross-program summary — call graph, dead paragraph inventory, CICS command list, reachability stats.
- **Inputs:** validation\structure\*_cfg.json (path needs adaptation to data\data_flow\)
- **Outputs:** Cross-program summary JSON
- **Gate dependency:** None (reporting)
- **Notes:** Upgrade candidate for generate_report.py. TARGET LOCATION when promoted: scripts\extract_cfg_summary.py.

### extract_file_control.py
- **Location:** scripts\scripts\
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Extracts FD (File Description) entries — SELECT/ASSIGN pairs, ORGANIZATION, ACCESS MODE, RECORD KEY, file status variables — per program.
- **Inputs:** data\raw\cbl\*.cbl (path needs adaptation)
- **Outputs:** Per-program file control JSON
- **Gate dependency:** None (Phase 2 IR enrichment)
- **Notes:** Not needed for Section 3.4. Planned output: data\file_control\<PROG>.json. TARGET LOCATION when promoted: scripts\extract_file_control.py.

### extract_paragraph_io.py
- **Location:** scripts\scripts\
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Per-paragraph READ/WRITE/REWRITE/DELETE/START file I/O summary — which files each paragraph accesses and in what mode.
- **Inputs:** pass1 annotation JSON (path needs adaptation)
- **Outputs:** Per-program paragraph I/O JSON
- **Gate dependency:** None (Phase 2 IR enrichment)
- **Notes:** Overlaps with data_flow.py reads/mutates for file I/O verbs. Use as cross-check validator rather than primary extractor. TARGET LOCATION when promoted: scripts\extract_paragraph_io.py.

### assemble_v1_2.py
- **Location:** scripts\scripts\
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Merges all extractor outputs — pass1 annotations, fallthrough data, byte layouts, file control, CFG summaries — into a single canonical IR record per program. This is the Phase 2 merge step that produces data\canonical\<PROG>.json.
- **Inputs:** All extractor JSON outputs across data\ tree
- **Outputs:** data\canonical\<PROG>.json (path needs adaptation)
- **Gate dependency:** None (Phase 2, after all gates closed)
- **Notes:** Will be renamed assemble_canonical.py when promoted. This is the final assembly script for the 100% faithful IR. TARGET LOCATION when promoted: scripts\assemble_canonical.py.

### validate_pass1.py
- **Location:** scripts\scripts\
- **Origin:** CarDemo
- **Status:** REFERENCE
- **Purpose:** Validates pass1_annotate.py output completeness — every paragraph has at least one verb annotation, no orphaned annotations outside a known paragraph.
- **Inputs:** validation\pass1\<PROG>_annotations.json
- **Outputs:** Console PASS/FAIL
- **Gate dependency:** Section 3.4
- **Notes:** Maps directly to a HermesCOBOL pre-3.4 gate check. TARGET LOCATION when promoted: scripts\validate_pass1.py.

---

## Section 3 — Files Present in scripts\scripts\ but NOT for HermesCOBOL use

| Filename | Reason Not Applicable |
|---|---|
| pass2_llm.py | LLM enrichment — SecuraTron domain, not deterministic pipeline |
| pass2_override.py | LLM output override — SecuraTron domain |
| pass2_template.py | Markdown skeleton generation — carddemo output format only |
| pass3_run.py | Final document assembly — carddemo-specific |
| pass3_synthesize.py | Final document assembly — carddemo-specific |
| pass3_run.bak.20260506_055459 | Historical backup — delete candidate |
| pass3_run.bak.20260506_055615 | Historical backup — delete candidate |
| compile_batch.jcl.template | JCL mainframe job template — AWS infrastructure |
| local_compile.sh | Shell script — mainframe compile, not applicable on Windows |
| remote_compile.sh | Shell script — remote mainframe compile |
| remote_refresh.sh | Shell script — remote environment refresh |
| remote_submit.sh | Shell script — mainframe job submission |
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

## Section 4 — Structural Issue: Nested scripts\scripts\ Folder

> The CarDemo scripts were pasted into scripts\scripts\ creating a nested
> structure. The intended final layout is:
>
>   scripts\                    ← HermesCOBOL native scripts only
>   scripts\scripts\            ← TEMPORARY — CarDemo reference copies
>
> Resolution plan (do not execute — document only):
> 1. Promote the 12 REFERENCE scripts to scripts\ (flat, no subdirectory)
> 2. Delete the inapplicable files from scripts\scripts\
> 3. Rename scripts\scripts\ to scripts\carddemo_archive\
> 4. Add a README.md inside carddemo_archive\ explaining origin
> This restructuring is deferred until after SCRIPTS_INVENTORY.md is
> reviewed and approved on GitHub.

---

## Section 5 — TODO Scripts Not Yet Written

| Script | Location (planned) | Purpose |
|---|---|---|
| assemble_canonical.py | scripts\ | Phase 2 driver — merges all extractor outputs into data\canonical\<PROG>.json for all 31 programs. Renamed from assemble_v1_2.py. |
| generate_canonical.py | scripts\ | Orchestrator — runs all extractors in correct dependency order for all 31 programs. |
| L001_codepage.py | validation\lint_cobol\rules\ | Lint rule ported from validate_codepage.py — pre-pipeline source encoding check. |
| para_diff_v2.py | scripts\ | Upgraded para_diff using (section_name, paragraph_name) tuples instead of flat names. Required after 3.4 lands. |
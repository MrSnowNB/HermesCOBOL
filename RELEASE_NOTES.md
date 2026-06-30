# Release Notes

## v0.8 — CobolWalker + Honcho Corpus (Phase 8)

- **CobolWalker v0.1 implemented** — deterministic DFS traversal over `CobolProgramDict` via `performs` + `falls_through_to` edges. All 10 gates green. Baseline sums: live=205, full=518 across 31 programs. goto_targets not traversed in v0.1 (15 CICS/goto-heavy programs yield live=1 — accepted limitation, deferred to v0.2). Walker regression locked in `validation/walker-baseline.json` and enforced automatically on every `validate_roundtrip.py` run (Gate 10).
- **Gate 10 added to `validate_roundtrip.py`** — `audit_cobol_walker.py` invoked on every run; divergence from baseline causes immediate FAIL.
- **Full corpus loaded into Honcho v3** — 518 paragraph IR units, ~3,900 layout fields, 31 CFGs, 1 oracle (COACTUPC v1), 31 meta records. Load time ~21 minutes. Reload with `python scripts/load_corpus.py --run`.

## v0.7 — CobolProgramDict (Phase 7)

- **`CobolProgramDict` implemented** — unified, validated access layer over the canonical IR. All 10 gates green at dc83fe5. 518 paragraphs, 31/31 programs. Optional enrichment sources (byte_layouts, data_flow, cfg) degrade gracefully — never raises on missing optional files. Importable as `from scripts.cobol_program_dict import CobolProgramDict`. See SPEC.md.

## v0.6 — Para key mapping fix (Phase 6)

- **518 paragraph keys correctly mapped in Honcho** — fixed para key mapping across all 31 programs (d7534f3).

## v0.5 — Full corpus load (Phase 5)

- **31-program full corpus load** — all programs loaded into Honcho v3 in ~21 minutes. Zero failures (cca0804).

## v0.4 — CFG + Oracle load (Phase 3+4)

- **CFG and oracle entries loaded** — 31 CFG summaries + COACTUPC v1 oracle loaded into Honcho (ada4865).

## v0.3 — Batch write perf fix

- **90x write speedup** — batch writes replace single-record writes in Honcho loader (b825709).

## v0.2 — Byte layout load (Phase 2)

- **Byte layout loaded into Honcho** — 1,165 fields for COACTUPC loaded (d07be38). Full corpus layout (~3,900 fields) followed in Phase 5.

## v0.1 — Raw substrate + initial Honcho load (Phase 1)

- **31/31 programs PASS, 0 FAIL** on the AWS CardDemo corpus: 14 non-CICS programs round-trip verified through GnuCOBOL `cobc -E` preprocessing (Mode A) against raw CardDemo copybooks and BMS map copybooks only — no stubs, no translators, no synthetic shims; 17 CICS programs pass Mode B structural validation and are explicitly reported as `preprocess_skipped=cics_no_translator` / `gate_note=cics_structural_only` because raw CardDemo source ships no CICS translator and the raw-data-only policy forbids adding one.
- **Deterministic, reproducible substrate locked:** `data/facts/` contains canonical schema v1.0 JSON for all 31 programs; `validation/reports/summary.json` encodes the 31/0/17 pass/fail/skip split; all generated artifacts are gitignored and reproduced locally by running `extract_facts.py` then `validate_roundtrip.py` — no LLM, no network, no automation in the gate path.
- **`honcho_loader.py` + COACTUPC para IR loaded** into Honcho v3 (fd34250).

# Release Notes

## v0.1-raw-substrate

- **31/31 programs PASS, 0 FAIL** on the AWS CardDemo corpus: 14 non-CICS programs round-trip verified through GnuCOBOL `cobc -E` preprocessing (Mode A) against raw CardDemo copybooks and BMS map copybooks only — no stubs, no translators, no synthetic shims; 17 CICS programs pass Mode B structural validation and are explicitly reported as `preprocess_skipped=cics_no_translator` / `gate_note=cics_structural_only` because raw CardDemo source ships no CICS translator and the raw-data-only policy forbids adding one.
- **Deterministic, reproducible substrate locked:** `data/facts/` contains canonical schema v1.0 JSON for all 31 programs (paragraphs, 01-level data items, external calls, internal performs, SELECT/ASSIGN files, copybooks referenced, CFG stub, CICS/SQL flags); `validation/reports/summary.json` encodes the 31/0/17 pass/fail/skip split; all generated artifacts are gitignored and reproduced locally by running `extract_facts.py` then `validate_roundtrip.py` — no LLM, no network, no automation in the gate path.

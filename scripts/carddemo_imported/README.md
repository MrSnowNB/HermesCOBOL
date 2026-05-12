# carddemo_imported — CarDemo Reference Scripts

**Origin:** aws-mainframe-modernization-carddemo/scripts/
**Status as of:** 2026-05-12

This folder contains the full CarDemo scripts folder, copied as-is.
It is a reference archive — do NOT run these scripts directly against
HermesCOBOL data without first checking path compatibility.

## Batch 1 — Already promoted to scripts\ (independent, no carddemo deps)
These files have been copied to scripts\ and are ready for path adaptation:
- validate_byte_layout.py
- validate_codepage.py
- validate_mutations.py
- extract_cfg_local.py
- extract_cfg_summary.py
- extract_file_control.py
- extract_paragraph_io.py
- extract_byte_layout.py

## Batch 2 — Pending promotion (dependency chain, promote together)
These files depend on each other and must be promoted as a group:
- extract_cfg_local.py      → prerequisite: none (already in Batch 1)
- pass1_annotate.py         → requires: extract_cfg_local.py output
- extract_fallthrough.py    → requires: pass1_annotate.py output
- validate_fallthrough.py   → requires: extract_fallthrough.py output
- validate_pass1.py         → requires: pass1_annotate.py output
- assemble_v1_2.py          → requires: ALL extractor outputs (final step)

## Not for HermesCOBOL use (delete after Batch 2 is complete)
- pass2_llm.py, pass2_override.py, pass2_template.py
- pass3_run.py, pass3_synthesize.py
- score_t04.py
- validate_pass2.py, validate_pass3.py
- validate_t01.py, validate_t02.py, validate_t02r.py, validate_t03.py
- *.sh shell scripts, pad.awk
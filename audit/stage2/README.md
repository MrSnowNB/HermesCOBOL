# Stage 2 Diagnostic Artifacts

**Date:** 2026-05-13
**Branch:** main

## What was run
validate_byte_layout.py — structural integrity check across all 31 programs.
extract_file_control.py — FD/REDEFINES inventory for 5 batch programs.

## What was found
All 31 programs passed T-PASS1-BYTES (byte layout structurally valid).
27 file_control entries found across 5 batch programs.

## Decisions made
- COPYBOOK_GAP x8: BMS/online programs need pass1_annotate.py cobc -E expansion
- FD_GAP x4: batch programs need FD record names added to byte_layout resolver
- CBSTM03A_CLASS x1: inspect REDEFINES chains before prescribing fix
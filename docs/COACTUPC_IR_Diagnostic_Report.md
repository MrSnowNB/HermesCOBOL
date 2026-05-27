# COACTUPC Statement-Level IR Extraction — Diagnostic Report

**Date**: 2026-05-27

## Step 1 Result: source_lines Fixed
- Real line numbers now populated from `data/preprocessed/COACTUPC.cob`
- Example: `1205-COMPARE-OLD-NEW` starts at line **3986**

## Step 2 Result: Missing Mutation Diagnosis
**Field**: `DATA-WAS-CHANGED-BEFORE-UPDATE`
- Occurrences in preprocessed `.cob`: **5**
- Present in `data_flow` mutates: **No**

**Conclusion**: The current data flow extractor is **not capturing `SET … TO TRUE`** mutations. This is a confirmed toolchain gap.

## Next Recommended Action
1. Add `SET` statement handling to the data flow extractor (high priority alongside MOVE)
2. Proceed with PERFORM extraction (Step 3)

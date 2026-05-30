# COACTUPC Translation Status

This directory contains the Python translation of the COACTUPC CICS COBOL program.

## Shared State

All paragraphs share `CarddemoState` (defined in `state.py`). The dataclass contains only fields that appear in the "reads" or "mutates" arrays from the Honcho IR.

## Translated Paragraphs

### 0000-MAIN
- **Statements**: 47 (fully translated)
- **Status**: ✅ Complete

### 1000-PROCESS-INPUTS
- **Statements**: 6 (fully translated)
- **Status**: ✅ Complete

### 1200-EDIT-MAP-INPUTS
- **Statements**: 134 (fully translated)
- **Status**: ✅ Complete

## Stub / Untranslated Paragraphs

- 1100-RECEIVE-MAP, 1210-EDIT-ACCOUNT, 1205-COMPARE-OLD-NEW, 1220-EDIT-YESNO, 1250-EDIT-SIGNED-9V2, 2000-DECIDE-ACTION, 3000-SEND-MAP — called but not implemented

## File Inventory

| File | Purpose | Status |
|------|---------|--------|
| `state.py` | Shared CarddemoState dataclass | Complete |
| `coactupc_0000_main.py` | Entry point (47 stmts) | ✅ Complete |
| `coactupc_1000_process_inputs.py` | Input validation (6 stmts) | ✅ Complete |
| `coactupc_1200_edit_map_inputs.py` | Map editing (134 stmts) | ✅ Complete |
| `README.md` | This file | Current |

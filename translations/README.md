# COACTUPC Translation Status

This directory contains the Python translation of the COACTUPC CICS COBOL program.

## Shared State

All paragraphs share `CarddemoState` (defined in `state.py`). The dataclass contains only fields that appear in the "reads" or "mutates" arrays from the Honcho IR for the translated paragraphs.

## Translated Paragraphs

### 1200-EDIT-MAP-INPUTS
- **Statements**: 134 (fully translated)
- **Reads**: 6 fields (ACUP-NEW-* dates, status, credit limit, etc.)
- **Mutates**: 8 fields (WS-NON-KEY-FLAGS children, WS-GENERIC-EDITS, ACUP-OLD-ACCT-DATA)
- **Performs**: 1210-EDIT-ACCOUNT, 1205-COMPARE-OLD-NEW, 1220-EDIT-YESNO, 1250-EDIT-SIGNED-9V2, EDIT-DATE-CCYYMMDD (stubs)
- **Status**: Fully translated with inline seq + raw COBOL comments

## Stub / Untranslated Paragraphs

- 0000-MAIN — not yet created
- 1000-PROCESS-INPUTS — not yet created
- 1210-EDIT-ACCOUNT, 1205-COMPARE-OLD-NEW, 1220-EDIT-YESNO, 1250-EDIT-SIGNED-9V2 — called but not implemented

## File Inventory

| File | Purpose | Status |
|------|---------|--------|
| `state.py` | Shared CarddemoState dataclass | Complete (all fields from 1200 IR) |
| `coactupc_1200_edit_map_inputs.py` | Main paragraph translation | Complete (134 statements) |
| `coactupc_0000_main.py` | Entry point | Not started |
| `coactupc_1000_process_inputs.py` | Input validation | Not started |
| `README.md` | This file | Current |

## Notes

- All field names are normalized (hyphens → underscores, lowercase).
- Control flags (bool) default to False.
- Complex edits and date validation are delegated to stub functions.

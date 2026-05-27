# COACTUPC Sample Payload Walkthrough (v2)

**Program**: COACTUPC  
**Version**: 2.0  
**Purpose**: Refined explicit/implicit analysis with clearer categorization of missing information  
**Date**: 2026-05-27

---

## Overview

This v2 document improves on the original by:

- Separating three distinct categories of "missing" information
- Adding a new column: **Resolvable from `.cbl` source**
- Making `EIBAID` resolution more explicit
- Acknowledging the confirmed absence of `performs` relationships in this program

---

## Refined Missing Data Categories

| Category | Label | Description |
|----------|-------|-------------|
| Present in source but not extracted | **Toolchain Gap** | Exists in `.cbl` but the current extractor did not capture it |
| Requires runtime execution | **Emulation Gap** | Needs actual CICS state, map buffer, or file results |
| Blocked by missing artifacts | **Artifact Gap** | Depends on copybooks or other files not present in the corpus |

---

## Payload Used (v2)

```json
{
  "scenario": "User Modifies Data",
  "EIBCALEN": 160,
  "EIBAID": "ENTER",
  "COMMAREA": {
    "CDEMO-GENERAL-INFO": {
      "CDEMO-FROM-PROGRAM": "COACTUPC",
      "CDEMO-PGM-REENTER": true
    },
    "CDEMO-ACCOUNT-INFO": {
      "CDEMO-ACCT-ID": "00000000123"
    }
  },
  "MAP-INPUT": {
    "ACCTSIDI": "00000000123",
    "ACSFNAMEI": "JOHN",
    "ACSLNAMEI": "SMITH",
    "ACSADDR1I": "123 MAIN ST"
  },
  "WS-THIS-PROGCOMMAREA": {
    "ACUP-DETAILS-NOT-FETCHED": false,
    "ACUP-OLD-CUST-FIRST-NAME": "JOHN",
    "ACUP-OLD-CUST-LAST-NAME": "DOE"
  }
}
```

**Key Design Choice**: `EIBAID: "ENTER"` is now explicitly stated so that key-checking logic in `1000-PROCESS-INPUTS` can be evaluated against the source.

---

## Refined Analysis Table

| Paragraph                  | Explicit Knowledge                          | Toolchain Gap                          | Emulation Gap                          | Resolvable from .cbl | Notes |
|---------------------------|---------------------------------------------|----------------------------------------|----------------------------------------|----------------------|-------|
| 0000-MAIN                 | Reads COMMAREA + literals                   | EIBCALEN check logic                   | Actual COMMAREA values                 | Yes                  | Entry point |
| 1000-PROCESS-INPUTS       | Decides next map/program                    | PFK-VALID / PFK-INVALID logic          | Which key was actually pressed         | Yes                  | Navigation logic |
| 1100-RECEIVE-MAP          | Receives from COACTUP map                   | Map field mapping                      | Did RECEIVE succeed? Map buffer content| Partial              | Map handling |
| 1205-COMPARE-OLD-NEW      | Compares old vs new name/address            | Comparison condition details           | Actual old vs new values               | Yes                  | High value paragraph |
| 9700-CHECK-CHANGE-IN-REC  | Change detection logic exists               | Update decision condition              | Whether update actually occurs         | Yes                  | Business rule core |
| 1200-EDIT-MAP-INPUTS      | Calls multiple edit paragraphs              | Which edit failed and why              | Validation results                     | Partial              | Orchestration |

---

## Confirmed Characteristics of COACTUPC

- **Performs edges**: 0 (confirmed in canonical IR)
- **CFG paragraphs**: 0 (CFG extraction returned empty for this CICS program)
- **Unresolved data flow entries**: 670
- **Preprocess available**: False

These are structural characteristics of the current extraction for this program, not tool limitations.

---

## Implications for Honcho Memory

This v2 format is better suited for memory chunking because each row now explicitly states:

- What is known
- What is missing due to extractor vs runtime
- Whether the source itself could answer the question

This allows Honcho to store high-precision memory units per paragraph with clear provenance.

---

*Document generated using `scripts/cobol_extract.py` with `strict_data=True`*

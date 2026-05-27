# COACTUPC Sample Payload Walkthrough

**Program**: COACTUPC  
**Purpose**: Demonstrate explicit vs implicit data extraction using a realistic sample payload  
**Date**: 2026-05-27  
**Tool Used**: `scripts/cobol_extract.py` (strict_data mode)

---

## Overview

This document walks through **COACTUPC** using a carefully designed sample payload. The goal is to show:

- What can be **faithfully extracted** from the HermesCOBOL artifacts.
- What must be **inferred or is impossible** to know without emulation.
- How the program operates as a state machine over the `CARDDEMO-COMMAREA`.

---

## Payload Used: "User Modifies Customer Data"

This payload represents a user who has already fetched an account and is now submitting changes.

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
    },
    "CDEMO-MORE-INFO": {
      "CDEMO-LAST-MAP": "CACTUPA"
    }
  },
  "MAP-INPUT": {
    "ACCTSIDI": "00000000123",
    "ACSTTUSI": "A",
    "ACSFNAMEI": "JOHN",
    "ACSLNAMEI": "SMITH",
    "ACSADDR1I": "123 MAIN ST",
    "ACSADDR2I": "APT 4B",
    "ACSCITYI": "NEW YORK",
    "ACSSTATEI": "NY",
    "ACSZIPI": "10001"
  },
  "WS-THIS-PROGCOMMAREA": {
    "ACUP-DETAILS-NOT-FETCHED": false,
    "ACUP-OLD-CUST-FIRST-NAME": "JOHN",
    "ACUP-OLD-CUST-LAST-NAME": "DOE"
  }
}
```

---

## Step-by-Step Walkthrough

### 1. 0000-MAIN

**From artifacts**:
- Reads: `WS-LITERALS.*`, `DFHCOMMAREA`, `CARDDEMO-COMMAREA`, `WS-THIS-PROGCOMMAREA`
- Mutates: `WS-MISC-STORAGE`, `WS-COMMAREA`, `CARDDEMO-COMMAREA`

**Explicit knowledge**:
- This is the entry point.
- The program has already fetched details (`ACUP-DETAILS-NOT-FETCHED = false`).

**Impossible to know**:
- Does it check `EIBCALEN`?
- Does it initialize error message fields?

---

### 2. 1000-PROCESS-INPUTS

**From artifacts**:
- Reads several `WS-LITERALS` fields and `WS-MISC-STORAGE.WS-RETURN-MSG`
- Mutates map navigation fields (`CCARD-NEXT-PROG`, `CCARD-NEXT-MAP`, etc.)

**Explicit knowledge**:
- This paragraph decides the next screen/program.

**Impossible to know**:
- What logic decides the next program?
- Does it check `PFK-INVALID` or `PFK-VALID`?

---

### 3. 1100-RECEIVE-MAP

**From artifacts**:
- Reads map fields: `CACTUPAI.ACCTSIDI`, `CACTUPAI.ACSTTUSI`, etc.

**Explicit knowledge**:
- The program receives user input from the `COACTUP` map.

**Impossible to know**:
- Did the `RECEIVE MAP` succeed?
- What was the actual content of the map buffer?

---

### 4. 1200-EDIT-MAP-INPUTS

This is a major decision point.

**From artifacts**:
- Calls multiple edit paragraphs:
  - `1205-COMPARE-OLD-NEW`
  - `1210-EDIT-ACCOUNT`
  - `1215-EDIT-MANDATORY`
  - `1220-EDIT-YESNO`
  - `1225-EDIT-ALPHA-REQD`
  - `1230-EDIT-ALPHANUM-REQD`

**Explicit knowledge**:
- The program performs layered validation.

**Impossible to know**:
- Which edit failed?
- What error message was set in `CCARD-ERROR-MSG`?

---

### 5. 1205-COMPARE-OLD-NEW (Critical)

**From artifacts**:
- Compares current input against previously fetched values (`ACUP-OLD-*` fields).

**Explicit knowledge**:
- The payload contains both old and new values for first/last name.

**Impossible to know**:
- Did any field actually change?
- Was `DATA-WAS-CHANGED-BEFORE-UPDATE` set to TRUE?

---

### 6. 9700-CHECK-CHANGE-IN-REC

**From artifacts**:
- Appears late in the paragraph list.
- Likely determines whether an update should occur.

**Explicit knowledge**:
- This paragraph exists and is part of the change detection logic.

**Impossible to know**:
- What condition causes an actual update vs. just returning to the map?

---

## What Can vs Cannot Be Determined

| Aspect                        | Can Be Determined from Artifacts      | Cannot Be Determined                     |
|------------------------------|---------------------------------------|------------------------------------------|
| Paragraph execution order    | Partial (no `performs` edges)         | Full execution path                      |
| Which edits run              | Yes (paragraph names)                 | Which ones passed or failed              |
| Field values                 | No                                    | All actual values                        |
| Branch outcomes              | No                                    | Any `IF` condition result                |
| Error message content        | No                                    | What gets moved into `CCARD-ERROR-MSG`   |
| Final action (Update vs Send)| No                                    | Whether a file/CICS update occurs        |
| COMMAREA state on return     | Partial                               | Exact content of COMMAREA on RETURN      |

---

## Summary

- **Explicit Data Available**: Paragraph names, some data flow (with 670 unresolved entries), copybook references.
- **Critical Missing Data**: Control flow edges, actual values, branch decisions, CICS command outcomes.
- **Best Use of Current Artifacts**: Structural understanding and identifying which fields are touched.
- **Emulation Required For**: Real behavior, validation results, and data transformation.

---

*Generated using `scripts/cobol_extract.py` with `strict_data=True`*

# COACTUPC Statement-Level IR Extraction — First Pass (v2)
**Date**: 2026-05-27
**Improvements**: Real source line numbers from preprocessed `.cob`

### 0000-MAIN
```json
{
  "program": "COACTUPC",
  "paragraph": "0000-MAIN",
  "source_lines": [
    3164,
    3194
  ],
  "source_artifact": "data/preprocessed/COACTUPC.cob",
  "next_paragraph": null,
  "statements": [],
  "reads": [
    "WS-LITERALS.LIT-THISTRANID",
    "WS-LITERALS.LIT-MENUPGM",
    "DFHCOMMAREA",
    "CARDDEMO-COMMAREA",
    "WS-THIS-PROGCOMMAREA",
    "CARDDEMO-COMMAREA.CDEMO-GENERAL-INFO.CDEMO-FROM-TRANID",
    "WS-LITERALS.LIT-MENUTRANID",
    "CARDDEMO-COMMAREA.CDEMO-GENERAL-INFO.CDEMO-FROM-PROGRAM"
  ],
  "mutates": [
    "CC-WORK-AREAS.CC-WORK-AREA",
    "WS-MISC-STORAGE",
    "WS-COMMAREA",
    "WS-MISC-STORAGE.WS-CICS-PROCESSNG-VARS.WS-TRANID",
    "CARDDEMO-COMMAREA",
    "WS-THIS-PROGCOMMAREA",
    "CARDDEMO-COMMAREA.CDEMO-GENERAL-INFO.CDEMO-TO-TRANID",
    "CARDDEMO-COMMAREA.CDEMO-GENERAL-INFO.CDEMO-TO-PROGRAM"
  ],
  "performs": [],
  "goto_targets": []
}
```

### 1000-PROCESS-INPUTS
```json
{
  "program": "COACTUPC",
  "paragraph": "1000-PROCESS-INPUTS",
  "source_lines": [
    3330,
    3360
  ],
  "source_artifact": "data/preprocessed/COACTUPC.cob",
  "next_paragraph": null,
  "statements": [],
  "reads": [
    "WS-MISC-STORAGE.WS-RETURN-MSG",
    "WS-LITERALS.LIT-THISPGM",
    "WS-LITERALS.LIT-THISMAPSET",
    "WS-LITERALS.LIT-THISMAP"
  ],
  "mutates": [
    "CC-WORK-AREAS.CC-WORK-AREA.CCARD-ERROR-MSG",
    "CC-WORK-AREAS.CC-WORK-AREA.CCARD-NEXT-PROG",
    "CC-WORK-AREAS.CC-WORK-AREA.CCARD-NEXT-MAPSET",
    "CC-WORK-AREAS.CC-WORK-AREA.CCARD-NEXT-MAP"
  ],
  "performs": [],
  "goto_targets": []
}
```

### 1205-COMPARE-OLD-NEW
```json
{
  "program": "COACTUPC",
  "paragraph": "1205-COMPARE-OLD-NEW",
  "source_lines": [
    3986,
    4016
  ],
  "source_artifact": "data/preprocessed/COACTUPC.cob",
  "next_paragraph": null,
  "statements": [],
  "reads": [
    "WS-THIS-PROGCOMMAREA.ACUP-NEW-DETAILS.ACUP-NEW-ACCT-DATA.ACUP-NEW-ACCT-ID-X",
    "WS-THIS-PROGCOMMAREA.ACUP-OLD-DETAILS.ACUP-OLD-ACCT-DATA.ACUP-OLD-ACCT-ID-X",
    "WS-THIS-PROGCOMMAREA.ACUP-NEW-DETAILS.ACUP-NEW-ACCT-DATA.ACUP-NEW-CURR-BAL",
    "WS-THIS-PROGCOMMAREA.ACUP-OLD-DETAILS.ACUP-OLD-ACCT-DATA.ACUP-OLD-CURR-BAL",
    "WS-THIS-PROGCOMMAREA.ACUP-NEW-DETAILS.ACUP-NEW-ACCT-DATA.ACUP-NEW-CREDIT-LIMIT",
    "WS-THIS-PROGCOMMAREA.ACUP-OLD-DETAILS.ACUP-OLD-ACCT-DATA.ACUP-OLD-CREDIT-LIMIT",
    "WS-THIS-PROGCOMMAREA.ACUP-NEW-DETAILS.ACUP-NEW-ACCT-DATA.ACUP-NEW-CASH-CREDIT-LIMIT",
    "WS-THIS-PROGCOMMAREA.ACUP-OLD-DETAILS.ACUP-OLD-ACCT-DATA.ACUP-OLD-CASH-CREDIT-LIMIT"
  ],
  "mutates": [],
  "performs": [],
  "goto_targets": []
}
```

### 1100-RECEIVE-MAP
```json
{
  "program": "COACTUPC",
  "paragraph": "1100-RECEIVE-MAP",
  "source_lines": [
    3344,
    3374
  ],
  "source_artifact": "data/preprocessed/COACTUPC.cob",
  "next_paragraph": null,
  "statements": [],
  "reads": [
    "CACTUPAI.ACCTSIDI",
    "CACTUPAI",
    "CACTUPAI.ACSTTUSI",
    "CACTUPAI.ACRDLIMI",
    "CACTUPAI.ACSHLIMI",
    "CACTUPAI.ACURBALI",
    "CACTUPAI.ACRCYCRI",
    "CACTUPAI.ACRCYDBI"
  ],
  "mutates": [
    "WS-THIS-PROGCOMMAREA.ACUP-NEW-DETAILS",
    "CC-WORK-AREAS.CC-WORK-AREA.CC-ACCT-ID",
    "WS-THIS-PROGCOMMAREA.ACUP-NEW-DETAILS.ACUP-NEW-ACCT-DATA.ACUP-NEW-ACCT-ID-X",
    "WS-THIS-PROGCOMMAREA.ACUP-NEW-DETAILS.ACUP-NEW-ACCT-DATA.ACUP-NEW-ACTIVE-STATUS",
    "WS-MISC-STORAGE.ALPHA-VARS-FOR-DATA-EDITING.ACUP-NEW-CREDIT-LIMIT-X",
    "WS-THIS-PROGCOMMAREA.ACUP-NEW-DETAILS.ACUP-NEW-ACCT-DATA.ACUP-NEW-CREDIT-LIMIT-N",
    "WS-MISC-STORAGE.ALPHA-VARS-FOR-DATA-EDITING.ACUP-NEW-CASH-CREDIT-LIMIT-X",
    "WS-THIS-PROGCOMMAREA.ACUP-NEW-DETAILS.ACUP-NEW-ACCT-DATA.ACUP-NEW-CASH-CREDIT-LIMIT-N"
  ],
  "performs": [],
  "goto_targets": []
}
```


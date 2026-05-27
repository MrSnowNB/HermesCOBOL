# COACTUPC Statement-Level IR Extraction — Line-by-Line PERFORM Scan
**Date**: 2026-05-27

## Results
- Total paragraphs: **78**
- Paragraphs with PERFORM: **10**
- Total PERFORM statements: **59**

## Sample Paragraphs with Performs
### 0000-MAIN
Performs: 4
```json
{
  "program": "COACTUPC",
  "paragraph": "0000-MAIN",
  "source_lines": [
    3164,
    3325
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
    "CARDDEMO-COMMAREA.CDEMO-GENERAL-INFO.CDEMO-FROM-TRANID"
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
  "performs": [
    {
      "target": "YYYY-STORE-PFKEY",
      "form": "simple"
    },
    {
      "target": "1000-PROCESS-INPUTS",
      "form": "simple"
    },
    {
      "target": "2000-DECIDE-ACTION",
      "form": "simple"
    },
    {
      "target": "3000-SEND-MAP",
      "form": "simple"
    }
  ],
  "goto_targets": []
}
```

### 1000-PROCESS-INPUTS
Performs: 2
```json
{
  "program": "COACTUPC",
  "paragraph": "1000-PROCESS-INPUTS",
  "source_lines": [
    3330,
    3340
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
  "performs": [
    {
      "target": "1100-RECEIVE-MAP",
      "form": "simple"
    },
    {
      "target": "1200-EDIT-MAP-INPUTS",
      "form": "simple"
    }
  ],
  "goto_targets": []
}
```

### 1200-EDIT-MAP-INPUTS
Performs: 30
```json
{
  "program": "COACTUPC",
  "paragraph": "1200-EDIT-MAP-INPUTS",
  "source_lines": [
    3734,
    3982
  ],
  "source_artifact": "data/preprocessed/COACTUPC.cob",
  "next_paragraph": null,
  "statements": [],
  "reads": [
    "WS-THIS-PROGCOMMAREA.ACUP-NEW-DETAILS.ACUP-NEW-ACCT-DATA.ACUP-NEW-ACTIVE-STATUS",
    "WS-MISC-STORAGE.WS-GENERIC-EDITS.WS-EDIT-YES-NO",
    "WS-THIS-PROGCOMMAREA.ACUP-NEW-DETAILS.ACUP-NEW-ACCT-DATA.ACUP-NEW-OPEN-DATE",
    "WS-MISC-STORAGE.ALPHA-VARS-FOR-DATA-EDITING.ACUP-NEW-CREDIT-LIMIT-X",
    "WS-MISC-STORAGE.WS-GENERIC-EDITS.WS-FLG-SIGNED-NUMBER-EDIT",
    "WS-THIS-PROGCOMMAREA.ACUP-NEW-DETAILS.ACUP-NEW-ACCT-DATA.ACUP-NEW-EXPIRAION-DATE"
  ],
  "mutates": [
    "WS-THIS-PROGCOMMAREA.ACUP-OLD-DETAILS.ACUP-OLD-ACCT-DATA",
    "WS-MISC-STORAGE.WS-NON-KEY-FLAGS",
    "WS-MISC-STORAGE.WS-GENERIC-EDITS.WS-EDIT-VARIABLE-NAME",
    "WS-MISC-STORAGE.WS-GENERIC-EDITS.WS-EDIT-YES-NO",
    "WS-MISC-STORAGE.WS-NON-KEY-FLAGS.WS-EDIT-ACCT-STATUS",
    "WS-MISC-STORAGE.WS-NON-KEY-FLAGS.WS-EDIT-OPEN-DATE-FLGS",
    "WS-MISC-STORAGE.WS-GENERIC-EDITS.WS-EDIT-SIGNED-NUMBER-9V2-X",
    "WS-MISC-STORAGE.WS-NON-KEY-FLAGS.WS-EDIT-CREDIT-LIMIT"
  ],
  "performs": [
    {
      "target": "1210-EDIT-ACCOUNT",
      "form": "simple"
    },
    {
      "target": "1205-COMPARE-OLD-NEW",
      "form": "simple"
    },
    {
      "target": "1220-EDIT-YESNO",
      "form": "simple"
    },
    {
      "target": "EDIT-DATE-CCYYMMDD",
      "form": "simple"
    },
    {
      "target": "1250-EDIT-SIGNED-9V2",
      "form": "simple"
    },
    {
      "target": "EDIT-DATE-CCYYMMDD",
      "form": "simple"
    },
    {
      "target": "1250-EDIT-SIGNED-9V2",
      "form": "simple"
    },
    {
      "target": "EDIT-DATE-CCYYMMDD",
      "form": "simple"
    },
    {
      "target": "1250-EDIT-SIGNED-9V2",
      "form": "simple"
    },
    {
      "target": "1250-EDIT-SIGNED-9V2",
      "form": "simple"
    },
    {
      "target": "1250-EDIT-SIGNED-9V2",
      "form": "simple"
    },
    {
      "target": "1265-EDIT-US-SSN",
      "form": "simple"
    },
    {
      "target": "EDIT-DATE-CCYYMMDD",
      "form": "simple"
    },
    {
      "target": "EDIT-DATE-OF-BIRTH",
      "form": "simple"
    },
    {
      "target": "1245-EDIT-NUM-REQD",
      "form": "simple"
    },
    {
      "target": "1275-EDIT-FICO-SCORE",
      "form": "simple"
    },
    {
      "target": "1225-EDIT-ALPHA-REQD",
      "form": "simple"
    },
    {
      "target": "1235-EDIT-ALPHA-OPT",
      "form": "simple"
    },
    {
      "target": "1225-EDIT-ALPHA-REQD",
      "form": "simple"
    },
    {
      "target": "1215-EDIT-MANDATORY",
      "form": "simple"
    },
    {
      "target": "1225-EDIT-ALPHA-REQD",
      "form": "simple"
    },
    {
      "target": "1270-EDIT-US-STATE-CD",
      "form": "simple"
    },
    {
      "target": "1245-EDIT-NUM-REQD",
      "form": "simple"
    },
    {
      "target": "1225-EDIT-ALPHA-REQD",
      "form": "simple"
    },
    {
      "target": "1225-EDIT-ALPHA-REQD",
      "form": "simple"
    },
    {
      "target": "1260-EDIT-US-PHONE-NUM",
      "form": "simple"
    },
    {
      "target": "1260-EDIT-US-PHONE-NUM",
      "form": "simple"
    },
    {
      "target": "1245-EDIT-NUM-REQD",
      "form": "simple"
    },
    {
      "target": "1220-EDIT-YESNO",
      "form": "simple"
    },
    {
      "target": "1280-EDIT-US-STATE-ZIP-CD",
      "form": "simple"
    }
  ],
  "goto_targets": []
}
```

### 1265-EDIT-US-SSN
Performs: 3
```json
{
  "program": "COACTUPC",
  "paragraph": "1265-EDIT-US-SSN",
  "source_lines": [
    4736,
    4793
  ],
  "source_artifact": "data/preprocessed/COACTUPC.cob",
  "next_paragraph": null,
  "statements": [],
  "reads": [
    "WS-THIS-PROGCOMMAREA.ACUP-NEW-DETAILS.ACUP-NEW-CUST-DATA.ACUP-NEW-CUST-SSN-X.ACUP-NEW-CUST-SSN-1",
    "WS-MISC-STORAGE.WS-GENERIC-EDITS.WS-EDIT-ALPHANUM-ONLY-FLAGS",
    "WS-THIS-PROGCOMMAREA.ACUP-NEW-DETAILS.ACUP-NEW-CUST-DATA.ACUP-NEW-CUST-SSN-X.ACUP-NEW-CUST-SSN-2",
    "WS-THIS-PROGCOMMAREA.ACUP-NEW-DETAILS.ACUP-NEW-CUST-DATA.ACUP-NEW-CUST-SSN-X.ACUP-NEW-CUST-SSN-3"
  ],
  "mutates": [
    "WS-MISC-STORAGE.WS-GENERIC-EDITS.WS-EDIT-VARIABLE-NAME",
    "WS-MISC-STORAGE.WS-GENERIC-EDITS.WS-EDIT-ALPHANUM-ONLY",
    "WS-MISC-STORAGE.WS-GENERIC-EDITS.WS-EDIT-ALPHANUM-LENGTH",
    "WS-MISC-STORAGE.WS-GENERIC-EDITS.WS-EDIT-US-SSN-FLGS.WS-EDIT-US-SSN-PART1-FLGS",
    "WS-MISC-STORAGE.WS-GENERIC-EDITS.WS-EDIT-US-SSN.WS-EDIT-US-SSN-PART1",
    "WS-MISC-STORAGE.WS-RETURN-MSG",
    "WS-MISC-STORAGE.WS-GENERIC-EDITS.WS-EDIT-US-SSN-FLGS.WS-EDIT-US-SSN-PART2-FLGS",
    "WS-MISC-STORAGE.WS-GENERIC-EDITS.WS-EDIT-US-SSN-FLGS.WS-EDIT-US-SSN-PART3-FLGS"
  ],
  "performs": [
    {
      "target": "1245-EDIT-NUM-REQD",
      "form": "simple"
    },
    {
      "target": "1245-EDIT-NUM-REQD",
      "form": "simple"
    },
    {
      "target": "1245-EDIT-NUM-REQD",
      "form": "simple"
    }
  ],
  "goto_targets": []
}
```

### 2000-DECIDE-ACTION
Performs: 3
```json
{
  "program": "COACTUPC",
  "paragraph": "2000-DECIDE-ACTION",
  "source_lines": [
    4867,
    4947
  ],
  "source_artifact": "data/preprocessed/COACTUPC.cob",
  "next_paragraph": null,
  "statements": [],
  "reads": [
    "CARDDEMO-COMMAREA.CDEMO-GENERAL-INFO.CDEMO-FROM-TRANID",
    "WS-LITERALS.LIT-THISPGM"
  ],
  "mutates": [
    "CARDDEMO-COMMAREA.CDEMO-ACCOUNT-INFO.CDEMO-ACCT-ID",
    "CARDDEMO-COMMAREA.CDEMO-CARD-INFO.CDEMO-CARD-NUM",
    "CARDDEMO-COMMAREA.CDEMO-ACCOUNT-INFO.CDEMO-ACCT-STATUS",
    "ABEND-DATA.ABEND-CULPRIT",
    "ABEND-DATA.ABEND-CODE",
    "ABEND-DATA.ABEND-REASON",
    "ABEND-DATA.ABEND-MSG"
  ],
  "performs": [
    {
      "target": "9000-READ-ACCT",
      "form": "simple"
    },
    {
      "target": "9600-WRITE-PROCESSING",
      "form": "simple"
    },
    {
      "target": "ABEND-ROUTINE",
      "form": "simple"
    }
  ],
  "goto_targets": []
}
```


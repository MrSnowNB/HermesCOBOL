# COACTUPC Statement-Level IR Extraction — Full 85 Paragraph Run
**Date**: 2026-05-27
**Boundary Rule**: end_line = (next_paragraph_start) - 1
**Total Paragraphs**: 78

## Summary Statistics
- Paragraphs with PERFORM statements: **0**
- Total PERFORM statements extracted: **0**
- Additional SET mutations captured: **130**

## Sample Paragraphs (first 8)
### 0000-MAIN
Lines: 3164–3325 | Performs: 0
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
  "performs": [],
  "goto_targets": []
}
```

### 3000-SEND-MAP-EXIT
Lines: 4969–4972 | Performs: 0
```json
{
  "program": "COACTUPC",
  "paragraph": "3000-SEND-MAP-EXIT",
  "source_lines": [
    4969,
    4972
  ],
  "source_artifact": "data/preprocessed/COACTUPC.cob",
  "next_paragraph": null,
  "statements": [],
  "reads": [],
  "mutates": [],
  "performs": [],
  "goto_targets": []
}
```

### 0000-MAIN-EXIT
Lines: 3326–3329 | Performs: 0
```json
{
  "program": "COACTUPC",
  "paragraph": "0000-MAIN-EXIT",
  "source_lines": [
    3326,
    3329
  ],
  "source_artifact": "data/preprocessed/COACTUPC.cob",
  "next_paragraph": null,
  "statements": [],
  "reads": [],
  "mutates": [],
  "performs": [],
  "goto_targets": []
}
```

### 1000-PROCESS-INPUTS
Lines: 3330–3340 | Performs: 0
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
  "performs": [],
  "goto_targets": []
}
```

### 1000-PROCESS-INPUTS-EXIT
Lines: 3341–3343 | Performs: 0
```json
{
  "program": "COACTUPC",
  "paragraph": "1000-PROCESS-INPUTS-EXIT",
  "source_lines": [
    3341,
    3343
  ],
  "source_artifact": "data/preprocessed/COACTUPC.cob",
  "next_paragraph": null,
  "statements": [],
  "reads": [],
  "mutates": [],
  "performs": [],
  "goto_targets": []
}
```

### 1100-RECEIVE-MAP
Lines: 3344–3730 | Performs: 0
```json
{
  "program": "COACTUPC",
  "paragraph": "1100-RECEIVE-MAP",
  "source_lines": [
    3344,
    3730
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
    "CACTUPAI.ACURBALI"
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

### 1100-RECEIVE-MAP-EXIT
Lines: 3731–3733 | Performs: 0
```json
{
  "program": "COACTUPC",
  "paragraph": "1100-RECEIVE-MAP-EXIT",
  "source_lines": [
    3731,
    3733
  ],
  "source_artifact": "data/preprocessed/COACTUPC.cob",
  "next_paragraph": null,
  "statements": [],
  "reads": [],
  "mutates": [],
  "performs": [],
  "goto_targets": []
}
```

### 1200-EDIT-MAP-INPUTS
Lines: 3734–3982 | Performs: 0
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
  "performs": [],
  "goto_targets": []
}
```

## Full Extraction (condensed)
- **0000-MAIN** (3164–3325): 0 performs, 8 mutates
- **3000-SEND-MAP-EXIT** (4969–4972): 0 performs, 0 mutates
- **0000-MAIN-EXIT** (3326–3329): 0 performs, 0 mutates
- **1000-PROCESS-INPUTS** (3330–3340): 0 performs, 4 mutates
- **1000-PROCESS-INPUTS-EXIT** (3341–3343): 0 performs, 0 mutates
- **1100-RECEIVE-MAP** (3344–3730): 0 performs, 8 mutates
- **1100-RECEIVE-MAP-EXIT** (3731–3733): 0 performs, 0 mutates
- **1200-EDIT-MAP-INPUTS** (3734–3982): 0 performs, 8 mutates
- **1200-EDIT-MAP-INPUTS-EXIT** (3983–3985): 0 performs, 0 mutates
- **1205-COMPARE-OLD-NEW** (3986–4081): 0 performs, 3 mutates
- **1205-COMPARE-OLD-NEW-EXIT** (4082–4087): 0 performs, 0 mutates
- **1210-EDIT-ACCOUNT** (4088–4124): 0 performs, 8 mutates
- **1210-EDIT-ACCOUNT-EXIT** (4125–4128): 0 performs, 0 mutates
- **1215-EDIT-MANDATORY** (4129–4156): 0 performs, 5 mutates
- **1215-EDIT-MANDATORY-EXIT** (4157–4160): 0 performs, 0 mutates
- **1220-EDIT-YESNO** (4161–4198): 0 performs, 4 mutates
- **1220-EDIT-YESNO-EXIT** (4199–4202): 0 performs, 0 mutates
- **1225-EDIT-ALPHA-REQD** (4203–4255): 0 performs, 6 mutates
- **1225-EDIT-ALPHA-REQD-EXIT** (4256–4259): 0 performs, 0 mutates
- **1230-EDIT-ALPHANUM-REQD** (4260–4313): 0 performs, 6 mutates
- **1230-EDIT-ALPHANUM-REQD-EXIT** (4314–4316): 0 performs, 0 mutates
- **1235-EDIT-ALPHA-OPT** (4317–4361): 0 performs, 5 mutates
- **1235-EDIT-ALPHA-OPT-EXIT** (4362–4365): 0 performs, 0 mutates
- **1240-EDIT-ALPHANUM-OPT** (4366–4409): 0 performs, 5 mutates
- **1240-EDIT-ALPHANUM-OPT-EXIT** (4410–4413): 0 performs, 0 mutates
- **1245-EDIT-NUM-REQD** (4414–4480): 0 performs, 5 mutates
- **1245-EDIT-NUM-REQD-EXIT** (4481–4484): 0 performs, 0 mutates
- **1250-EDIT-SIGNED-9V2** (4485–4525): 0 performs, 5 mutates
- **1250-EDIT-SIGNED-9V2-EXIT** (4526–4529): 0 performs, 0 mutates
- **1260-EDIT-US-PHONE-NUM** (4530–4731): 0 performs, 8 mutates
- **1260-EDIT-US-PHONE-NUM-EXIT** (4732–4735): 0 performs, 0 mutates
- **1265-EDIT-US-SSN** (4736–4793): 0 performs, 8 mutates
- **1265-EDIT-US-SSN-EXIT** (4794–4797): 0 performs, 0 mutates
- **1270-EDIT-US-STATE-CD** (4798–4815): 0 performs, 4 mutates
- **1270-EDIT-US-STATE-CD-EXIT** (4816–4818): 0 performs, 0 mutates
- **1275-EDIT-FICO-SCORE** (4819–4835): 0 performs, 3 mutates
- **1275-EDIT-FICO-SCORE-EXIT** (4836–4840): 0 performs, 0 mutates
- **1280-EDIT-US-STATE-ZIP-CD** (4841–4862): 0 performs, 5 mutates
- **1280-EDIT-US-STATE-ZIP-CD-EXIT** (4863–4866): 0 performs, 0 mutates
- **2000-DECIDE-ACTION** (4867–4947): 0 performs, 8 mutates
- **2000-DECIDE-ACTION-EXIT** (4948–4953): 0 performs, 0 mutates
- **3000-SEND-MAP** (4954–4968): 0 performs, 0 mutates
- **3100-SCREEN-INIT** (4973–4998): 0 performs, 8 mutates
- **3100-SCREEN-INIT-EXIT** (4999–5002): 0 performs, 0 mutates
- **3200-SETUP-SCREEN-VARS** (5003–5031): 0 performs, 2 mutates
- **3200-SETUP-SCREEN-VARS-EXIT** (5032–5035): 0 performs, 0 mutates
- **3201-SHOW-INITIAL-VALUES** (5036–5087): 0 performs, 8 mutates
- **3201-SHOW-INITIAL-VALUES-EXIT** (5088–5091): 0 performs, 0 mutates
- **3202-SHOW-ORIGINAL-VALUES** (5092–5171): 0 performs, 8 mutates
- **3202-SHOW-ORIGINAL-VALUES-EXIT** (5172–5174): 0 performs, 0 mutates
- **3203-SHOW-UPDATED-VALUES** (5175–5255): 0 performs, 8 mutates
- **3203-SHOW-UPDATED-VALUES-EXIT** (5256–5259): 0 performs, 0 mutates
- **3250-SETUP-INFOMSG** (5260–5287): 0 performs, 8 mutates
- **3250-SETUP-INFOMSG-EXIT** (5288–5290): 0 performs, 0 mutates
- **3300-SETUP-SCREEN-ATTRS** (5291–6469): 0 performs, 8 mutates
- **3300-SETUP-SCREEN-ATTRS-EXIT** (6470–6473): 0 performs, 0 mutates
- **3310-PROTECT-ALL-ATTRS** (6474–6528): 0 performs, 1 mutates
- **3310-PROTECT-ALL-ATTRS-EXIT** (6529–6532): 0 performs, 0 mutates
- **3320-UNPROTECT-FEW-ATTRS** (6533–6594): 0 performs, 1 mutates
- **3320-UNPROTECT-FEW-ATTRS-EXIT** (6595–6598): 0 performs, 0 mutates
- **3390-SETUP-INFOMSG-ATTRS** (6599–6616): 0 performs, 1 mutates
- **3390-SETUP-INFOMSG-ATTRS-EXIT** (6617–6621): 0 performs, 0 mutates
- **3400-SEND-SCREEN** (6622–6635): 0 performs, 2 mutates
- **3400-SEND-SCREEN-EXIT** (6636–6640): 0 performs, 0 mutates
- **9000-READ-ACCT** (6641–6679): 0 performs, 5 mutates
- **9000-READ-ACCT-EXIT** (6680–6682): 0 performs, 0 mutates
- **9200-GETCARDXREF-BYACCT** (6683–6730): 0 performs, 8 mutates
- **9200-GETCARDXREF-BYACCT-EXIT** (6731–6733): 0 performs, 0 mutates
- **9300-GETACCTDATA-BYACCT** (6734–6780): 0 performs, 8 mutates
- **9300-GETACCTDATA-BYACCT-EXIT** (6781–6784): 0 performs, 0 mutates
- **9400-GETCUSTDATA-BYCUST** (6785–6829): 0 performs, 8 mutates
- **9400-GETCUSTDATA-BYCUST-EXIT** (6830–6833): 0 performs, 0 mutates
- **9500-STORE-FETCHED-DATA** (6834–6917): 0 performs, 8 mutates
- **9500-STORE-FETCHED-DATA-EXIT** (6918–6920): 0 performs, 0 mutates
- **9600-WRITE-PROCESSING** (6921–7137): 0 performs, 8 mutates
- **9600-WRITE-PROCESSING-EXIT** (7138–7141): 0 performs, 0 mutates
- **9700-CHECK-CHANGE-IN-REC** (7142–7225): 0 performs, 1 mutates
- **9700-CHECK-CHANGE-IN-REC-EXIT** (7226–7713): 0 performs, 8 mutates

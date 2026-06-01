---
# HermesCOBOL Session Scratchpad
**Last Updated:** 2026-06-01 ~14:33 EDT
**Last Commit:** 7396cec

## Current Status
- **Program:** COACTUPC.cbl
- **Last Completed Paragraph:** 3390-SETUP-INFOMSG-ATTRS
- **Next Paragraph:** 3400-SEND-SCREEN
- **Pytest Status:** 150 passed / 1 pre-existing failure
- **Lint Status:** Zero violations (lint_check.py guard active)

## Completed Paragraphs (This Session)
- 1275-EDIT-FICO-SCORE
- 1280-EDIT-US-STATE-ZIP-CD  ← 12xx series COMPLETE
- 2000-DECIDE-ACTION (stubs: 9000, 9600)
- 3000-SEND-MAP (orchestrator)
- 3100-SCREEN-INIT
- 3200-SETUP-SCREEN-VARS (+ 3201/3202/3203 helpers)
- 3250-SETUP-INFOMSG
- 3300-SETUP-SCREEN-ATTRS (+ 3310/3320 helpers)
- 3390-SETUP-INFOMSG-ATTRS

## Remaining 3xxx Stubs
- 3400-SEND-SCREEN (next)

## After 3400
- 9000-READ-ACCT series
- 9600-WRITE-PROCESSING series

## Key Design Decisions (carry forward)
- State always passed as parameter — NEVER imported globally
- lint_check.py enforces this — run check before every commit
- state.cactupao = dict (output map), state.cactupai = dict (input map)
- BMS constants in constants.py: DFHBMPRF, DFHBMFSE, DFHBMDAR, DFHBMASB
- Info message constants in constants.py: INFO_PROMPT_SEARCH etc.
- 9000/9600 are TODO stubs in 2000 — translate when reached in sequence
- ABEND path = raise RuntimeError(...)

## Resume Command
"Resume HermesCOBOL session. 
Next paragraph is 3400-SEND-SCREEN. 
Last commit was 7396cec."
---

# AI First Scratchpad

> **Purpose:** Context management for AI First protocol agents working on this repo.

---
# HermesCOBOL — Agent Scratchpad

## AGENT PROTOCOL (INVARIANT)
1. Cloud agent writes scratchpad fresh per stage — never inherit prior stage context
2. Every kickoff includes FIRST-PRINCIPLES LOOP block before any step
3. Context reset between every step — one Cline session per step
4. RESULT: = actual output only, never expected output
5. STOP on 2 consecutive failures — mark BLOCKED, push, await human

## FROZEN GROUND TRUTH
- branch: audit/3.4-local-second-opinion
- last verified commit: 3a8eb10
- test gate: 61/61 PASS
- COACTUPC unresolved: 0
- schema_version in data_flow.py: 1.2 (needs bump to 1.3)
- data_flow JSONs: 29 files regenerated, clean

## EXECUTION PLAN — NODE A: Close Section 3.4 Gate
---

### STEP A1 [IN_PROGRESS]
Goal: Verify current SCHEMA_VERSION and section_name field in data_flow.py

Commands:
  python -c "import scripts.data_flow as df; print('SCHEMA_VERSION:', df.SCHEMA_VERSION)"
  python -c "import json; d=json.load(open('data/data_flow/COACTUPC.json')); p=list(d['paragraph_data_flow'].values())[0]; print('section_name present:', 'section_name' in p); print('value:', p.get('section_name'))"

Pass condition: SCHEMA_VERSION is 1.2, section_name key is present. No exceptions.
On failure: mark BLOCKED, paste error, push, stop.

---

### STEP A2 [PENDING]
Goal: Bump SCHEMA_VERSION from 1.2 to 1.3 in scripts/data_flow.py

Exact change: find SCHEMA_VERSION = "1.2" and change to SCHEMA_VERSION = "1.3"

Verify:
  python -c "import scripts.data_flow as df; print(df.SCHEMA_VERSION)"

Pass condition: prints 1.3
On failure: revert the line, mark BLOCKED, push, stop.

---

### STEP A3 [PENDING]
Goal: Regenerate all data_flow JSONs and confirm schema_version updated

Commands:
  python scripts/data_flow.py --all 2>&1 | Select-Object -Last 5
  python -c "import json; d=json.load(open('data/data_flow/COACTUPC.json')); print('schema_version:', d['schema_version'])"

Pass condition: schema_version is "1.3" in output JSON
On failure: mark BLOCKED, paste error, push, stop.

---

### STEP A4 [PENDING]
Goal: Run full test suite and confirm gate is green

Command:
  python -m pytest tests/ -v 2>&1 | Select-Object -Last 15

Pass condition: all tests pass, zero failures, count >= 61
On failure: paste full failure output, mark BLOCKED, push, stop. Do NOT proceed to commit.

---

### STEP A5 [PENDING]
Goal: Commit gate close

Commands:
  git add scripts/data_flow.py data/data_flow/
  git commit -m "gate(3.4): CLOSED — schema_version 1.3, 61/61 tests pass, unresolved=0 on COACTUPC"
  git push origin audit/3.4-local-second-opinion

Pass condition: push succeeds, working tree clean
On failure: paste error, mark BLOCKED, stop.

════════════════════════════════════════
EXECUTION RULES
════════════════════════════════════════
- Start on STEP A1 only
- Complete each step, append RESULT, mark DONE, then move to next
- One step at a time — do not skip ahead
- After A5 push: STOP. Do not open a PR. Do not edit any other file.
- Files you may touch: scripts/data_flow.py, data/data_flow/*.json, .clinerules/scratchpad.md
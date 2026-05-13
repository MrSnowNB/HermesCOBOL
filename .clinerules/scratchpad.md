# HermesCOBOL — Agent Scratchpad

---

## AGENT PROTOCOL (INVARIANT)

1. Cloud agent writes scratchpad fresh per stage — never inherit prior stage context
2. Every kickoff includes FIRST-PRINCIPLES LOOP block before any step
3. Context reset between every step — one Cline session per step
4. **RESULT:** = actual output only, never expected output
5. STOP on 2 consecutive failures — mark BLOCKED, push, await human

---

## FIRST-PRINCIPLES PROBLEM-SOLVING LOOP

- Verify what is actually true on disk before assuming anything
- State your assumption explicitly before acting on it
- Every step must prove its own result before the next step begins
- Surfaced failure is always preferred over silent pass
- If expected output does not match actual output — STOP and reclassify
- **RESULT:** = actual command output only, never expected output
- Never mark a step DONE without pasting real command output

---

## FROZEN GROUND TRUTH

> APPEND ONLY. Never delete. Never edit existing entries.
> This section survives compaction. It is institutional memory.

### [2026-05-13] Stage 4 gate anchor

- **Branch:** main, commit 10d8ce6
- **Baseline:** 70 passed / 3 failed / 73 total (python -m pytest only)
- **Schema version:** 1.3
- **Byte layouts:** 31/31 programs in `data/byte_layouts/`
- **carddemo_imported:** scripts present, NOT promoted — do not touch
- **pytest rule:** ALWAYS use `python -m pytest tests/ -q`
  NEVER use `python -m unittest discover` — test_extract_facts_alignment.py ERRORs under unittest

### [2026-05-13] Stage 4 punchlist — remaining

| Vector | Test name | Root cause |
|---|---|---|
| V07 | test_v07_exec_cics_masking | ✅ FIXED — commit 53d746b |
| V08 | test_v08_move_corresponding_dual_tree | MOVE CORR resolves group name only; child tree walk missing |
| V09 | test_v09_nearest_enclosing_scope | Qualified name OF/IN resolution not implemented |
| V10 | test_v10_ambiguous_conflict_flagging | Ambiguous field detection missing; reason=ambiguous not set |

### [2026-05-13] Stage 4 invariants

- **Goal this scratchpad:** Fix V08 only — do not touch V09/V10
- **File to modify:** `scripts/data_flow.py` only
- **Do NOT modify:** `tests/test_data_flow.py`
- **Do NOT touch:** any verb handler other than MOVE CORRESPONDING
- **Do NOT promote:** any script from `scripts/carddemo_imported/`
- **One commit only:** after D3 confirms V08 PASS and baseline >= 70

---

## CURRENT CONTEXT

<!-- Local agent updates this after every step. -->

- Branch: main | Tree: clean
- Last: — (session start)
- Next: D1 — read current MOVE CORRESPONDING handler
- Blocker: none

---

## EXECUTION PLAN — Stage 4b: Fix V08 MOVE CORRESPONDING

---

### STEP D1 [PENDING]

**Goal:**
Read the current MOVE CORRESPONDING handler in `scripts/data_flow.py`.
Do not modify anything.

**Exact commands:**

```powershell
git branch --show-current
git status --short

# Search for CORRESPONDING or CORR handling
Select-String -Path scripts\data_flow.py `
  -Pattern "CORRESPONDING|CORR" -CaseSensitive:$false |
  Select-Object LineNumber, Line

# Show ±15 lines around first match (replace LINE with actual line number)
Get-Content scripts\data_flow.py |
  Select-Object -Skip (LINE - 10) -First 30
```

**Pass condition:**
- Branch is main, tree is clean
- Handler code (or confirmed absence) is visible and pasted

**RESULT:**
<!-- Local agent pastes actual command output here before marking DONE -->

---

### STEP D2 [PENDING]

**Goal:**
Fix the MOVE CORRESPONDING handler so it walks the layout tree and extracts
matching non-FILLER child fields — matching children go to reads (from source
group) and mutates (to destination group). Non-matching children and FILLER
are excluded.

**What V08 asserts:**
MOVE CORRESPONDING ROOT-A TO ROOT-B
qmap contains ROOT-A (children: CHILD-X, CHILD-Y, FILLER)
ROOT-B (children: CHILD-X, CHILD-Z, FILLER)

Expected:
CHILD-X in reads (matching, non-FILLER, in ROOT-A)
CHILD-X in mutates (matching, non-FILLER, in ROOT-B)
CHILD-Y NOT in mutates (not in ROOT-B)
CHILD-Z NOT in reads (not in ROOT-A)
FILLER NOT in reads or mutates

text

**Fix specification:**
- Detect: statement matches `MOVE CORRESPONDING <SRC> TO <DEST>`
  or `MOVE CORR <SRC> TO <DEST>`
- Look up SRC and DEST in qmap
- If either is absent from qmap: fall back to current behavior (group name only)
- Get children of SRC: `qmap[SRC].get("children", [])`
- Get children of DEST: `qmap[DEST].get("children", [])`
- Compute intersection by name, excluding any child named `FILLER`
- For each matched child name:
  - Add SRC child entry to reads
  - Add DEST child entry to mutates
- Do NOT add the group names (ROOT-A, ROOT-B) to reads/mutates
- Do NOT touch any handler outside MOVE CORRESPONDING

**After editing, verify diff is minimal:**

```powershell
git diff scripts/data_flow.py
```

If diff touches anything outside MOVE CORRESPONDING — stop immediately:
  `git checkout -- scripts/data_flow.py`
Mark D2 BLOCKED. STOP.

Paste full diff as RESULT. Mark D2 [DONE].

**RESULT:**
<!-- Local agent pastes actual git diff output here before marking DONE -->

---

### STEP D3 [PENDING]

**Goal:**
Run V08 in isolation, then run the full suite with pytest only.
Confirm V08 passes and baseline does not drop below 70.
Commit and push only on confirmed pass.

**Exact commands:**

```powershell
# V08 in isolation
python -m pytest tests/test_data_flow.py -k "v08" -v 2>&1

# Full suite — pytest ONLY, never unittest
python -m pytest tests/ -q 2>&1 | Select-Object -Last 3

# Only if V08 PASSED AND passed count >= 70:
git add scripts/data_flow.py .clinerules/scratchpad.md
git diff --cached --name-only
git commit -m "fix(stage4): V08 MOVE CORR child field tree walk"
git push origin main
git log --oneline -1
```

**Pass condition:**
- V08: PASSED
- Full suite passed count >= 70
- `git diff --cached --name-only` shows ONLY `scripts/data_flow.py`
  and `.clinerules/scratchpad.md`

**On failure:**
- If V08 still fails: STOP. Mark D3 BLOCKED. Paste exact assertion. Do NOT commit.
- If baseline drops below 70:
    `git checkout -- scripts/data_flow.py`
  Confirm 70 restored. Mark BLOCKED.

**RESULT:**
<!-- Local agent pastes actual pytest output and git log here before marking DONE -->

---

## EXECUTION RULES

- You are permitted to modify ONLY: `scripts/data_flow.py`, `.clinerules/scratchpad.md`
- You are NOT permitted to modify: `tests/test_data_flow.py` or any other file
- Commit only after D3 confirms PASS — never speculatively commit
- If `git diff --cached --name-only` shows any unexpected file — abort commit immediately
- ALWAYS run full suite as: `python -m pytest tests/ -q`
- NEVER run: `python -m unittest discover` — this causes ERRORs
- Update CURRENT CONTEXT section after every step completion
- Mark each step [DONE] or [BLOCKED] before moving to the next
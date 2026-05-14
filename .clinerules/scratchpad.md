# HermesCOBOL — Agent Scratchpad

---

## AGENT PROTOCOL (INVARIANT)

1. This scratchpad is your ONLY memory between sessions.
2. Read AGENT PROTOCOL → CURRENT CONTEXT → ONE step block. Nothing else.
3. RESULT: = actual command output only. Never fabricate. Never paste expected output.
4. Mark each step [DONE] or [BLOCKED] before stopping.
5. STOP on 2 consecutive failures — mark BLOCKED, push scratchpad, await human.
6. NEVER modify a file not in PERMITTED FILES FOR THIS SESSION.
7. NEVER add tests, classes, or methods beyond what the step explicitly authorizes.
8. NEVER commit a failing test — a failing test is a BLOCKER, not "expected."
9. ALWAYS use `C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests/ -q`
   NEVER use `python -m unittest discover` or `C:\gnucobol\bin\python.exe`
10. Total test count must equal 125 before G2, and 127 after G2. Any other count = BLOCKED.
    (Breakdown: test_data_flow.py=73→75, test_byte_layout.py=21, test_extract_facts_alignment.py=31)

---

## FIRST-PRINCIPLES VERIFICATION LOOP

Run this before every step:
- What does CURRENT CONTEXT say the next step is?
- Read ONLY that step block.
- State your ONE assumption about disk state.
- Verify it with a command before acting on it.
- If real output ≠ expected — STOP. Update CURRENT CONTEXT. Mark BLOCKED.

---

## FROZEN GROUND TRUTH

> APPEND ONLY. Never delete. Never edit existing entries.
> Do NOT re-read this section during step execution — CURRENT CONTEXT tells you where you are.

### [2026-05-13] Stage 4 baseline
- Branch: main | Schema: 1.3 | Byte layouts: 31/31
- Baseline at 10d8ce6: 70 passed / 3 failed / 73 total (test_data_flow.py only)

### [2026-05-14] Full suite composition (locked)
| File | Tests | Notes |
|---|---|---|
| test_data_flow.py | 73 | Stage 2/3/4 vectors |
| test_byte_layout.py | 21 | Byte layout parsing |
| test_extract_facts_alignment.py | 31 | Parametrized by JSON in data/facts/ |
| **Total** | **125** | Verified at commit b0a30a7 |

### [2026-05-14] Stage 4 vector status
| Vector | Test | Commit | Status |
|---|---|---|---|
| V07 | test_v07_exec_cics_masking | 53d746b | ✅ |
| V08 | test_v08_move_corresponding_dual_tree | b0a30a7 | ✅ |
| V09 | test_v09_nearest_enclosing_scope | 9181c7b | ✅ |
| V10 | test_v10_ambiguous_conflict_flagging | 9181c7b | ✅ |
| V11 | test_v11_column_aware_paragraph_lexing | 7494ea4 | ✅ |
| V12 | test_v12_section_boundary_encapsulation | 7494ea4 | ✅ |
| V13 | test_v13_statements_ordering | pending | ← THIS SESSION |

### [2026-05-14] Stage 4e invariants
- **Goal:** Add `statements[]` array to each paragraph entry in `extract_data_flow()` output
- **Non-breaking:** reads/mutates/unresolved stay exactly as-is. statements[] is additive only.
- **Schema version bump:** 1.3 → 1.4
- **PERMITTED FILES:** `scripts/data_flow.py`, `tests/test_data_flow.py`, `.clinerules/scratchpad.md`
- **FORBIDDEN:** modifying any other file
- **FORBIDDEN:** modifying any existing test class or method
- **One commit only:** after G3 confirms 127/127 pass

### [2026-05-14] V13 target output shape
```json
{
  "paragraph": "1000-PROCESS-ACCT",
  "section_name": "MAIN-SECTION",
  "reads":   [...],
  "mutates": [...],
  "statements": [
    {"seq": 1, "verb": "MOVE",    "sources": ["ACCT-ID"],           "targets": ["WS-ACCT-ID"]},
    {"seq": 2, "verb": "COMPUTE", "sources": ["WS-BAL","WS-CREDIT"],"targets": ["WS-NET"]},
    {"seq": 3, "verb": "IF",      "condition_raw": "WS-NET > ZERO", "sources": [], "targets": []}
  ]
}
```
Rules:
- `seq` is 1-based, ordered by statement appearance in the paragraph
- `verb` is the COBOL keyword in ALL CAPS (MOVE, COMPUTE, IF, PERFORM, etc.)
- `sources` = list of variable names read by this statement (empty list [] if none)
- `targets` = list of variable names mutated by this statement (empty list [] if none)
- `condition_raw` = raw condition string, only present for IF/EVALUATE statements
- Literals (strings/numbers) are NOT included in sources

### [2026-05-14] _extract_synthetic scope note
- `_extract_synthetic` is a module-level function defined at ~line 970 in test_data_flow.py
- It is NOT inside any class — V13 test can call it directly without import
- When called with a synthetic source string, qmap is empty → all field refs go to unresolved
- This is expected and correct — V13 tests only check statements[], not reads/mutates

---

## CURRENT CONTEXT  ← QWEN: Read this. Jump directly to step named in "Next:".

- Branch: main | Tree: clean (as of b0a30a7)
- Last: G2 DONE — V13 tests pass, 127/127 full suite, git diff shows 3 permitted files
- **Next: G3**
- Blocker: none
- Permitted: `scripts/data_flow.py`, `tests/test_data_flow.py`, `.clinerules/scratchpad.md`

---

## EXECUTION PLAN — Stage 4e: V13 statements[] ordering

---

### STEP G1 [DONE]

**Goal:** Verify clean baseline and locate the paragraph_data_flow assembly block
in `data_flow.py`. Do NOT modify anything.

**Commands:**
```powershell
git branch --show-current
git status --short
git log --oneline -3

# Confirm 125/125 baseline
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  -m pytest tests/ -q 2>&1 | Select-Object -Last 3

# Find key landmarks in data_flow.py
Select-String -Path scripts\data_flow.py `
  -Pattern "def extract_data_flow|paragraph_data_flow|schema_version" |
  Select-Object LineNumber, Line

# Read the paragraph dict assembly block — replace LINE with the
# line number of paragraph_data_flow dict construction from above
Get-Content scripts\data_flow.py |
  Select-Object -Skip (LINE - 1) -First 35
```

**Pass condition:**
- Branch: main, tree: clean
- 125 passed, 0 failed
- You can see the dict being built per paragraph (reads, mutates, unresolved, section_name keys)
- You know exactly which line to add `"statements": stmt_list`

**After RESULT is pasted:**
- Update CURRENT CONTEXT: Last = "G1 DONE", Next = G2
- Mark step [DONE]
- STOP. Report to human.

**RESULT:**
```powershell
PS C:\work\HermesCOBOL> git branch --show-current
main

PS C:\work\HermesCOBOL> git status --short
M .clinerules/scratchpad.md

PS C:\work\HermesCOBOL> git log --oneline -3
b0a30a7 (HEAD -> main, origin/main, origin/HEAD) test(stage4d): fix V08 assertions to match dict-based reads/mutates output
9181c7b fix(stage4c): V08 MOVE CORR emit dicts; V09 dot-operand handling; V10 ambiguity fix
b9e1a1e fix(stage4): V08 MOVE CORR child field tree walk

PS C:\work\HermesCOBOL> C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests/ -q
........................................................................ [ 57%]
.....................................................                    [100%]
125 passed in 0.74s

# Landmarks found:
# Line 18: SCHEMA_VERSION = "1.3"
# Line 1282: def extract_data_flow(cbl_path: Path, layout_path: Path) -> dict:
# Line 1334: # --- Emit paragraph_data_flow: one entry per occurrence ---
# Line 1335: paragraph_data_flow = {}
# Line 1334: paragraph_data_flow = {}
# Line 1335: entry_data = {
# Line 1353: 'schema_version':      SCHEMA_VERSION,
# Line 1354: 'paragraph_data_flow': paragraph_data_flow,

# Paragraph dict assembly block (lines 1335-1366):
# - entry_data built at lines 1353-1358 with: section_name, reads, mutates, unresolved
# - statements[] needs to be added alongside these keys
# - schema_version = "1.3" at line 18

---

### STEP G2 [DONE]

**Goal:** Add `statements[]` to `data_flow.py` AND add the V13 test class to
`tests/test_data_flow.py`. These are the ONLY two files changed this step.

**Part A — scripts/data_flow.py changes (3 sub-changes):**

1. Inside the per-statement processing loop in `extract_data_flow()`, accumulate
   a `stmt_list` per paragraph. Each entry has this shape:
   ```python
   entry = {"seq": seq_counter, "verb": verb, "sources": [...], "targets": [...]}
   # For IF/EVALUATE only, also add:
   entry["condition_raw"] = raw_condition_string
   ```
   `seq_counter` starts at 1 and increments for each statement in the paragraph.
   `verb` = the COBOL keyword in ALL CAPS extracted from the statement.
   `sources` = variable names that appear in reads for this statement (not literals).
   `targets` = variable names that appear in mutates for this statement.

2. When building each paragraph's dict in `paragraph_data_flow`, add:
   ```python
   "statements": stmt_list
   ```
   alongside the existing `reads`, `mutates`, `unresolved`, `section_name` keys.

3. Bump schema_version: change `"1.3"` → `"1.4"` (one line only).

**Part B — tests/test_data_flow.py change:**
Append this class at the very end of the file (after TestV12):

```python
class TestV13StatementsOrdering(unittest.TestCase):
    """V13: statements[] — ordered verb metadata per paragraph"""

    _SRC_V13 = (
        "       IDENTIFICATION DIVISION.\n"
        "       PROGRAM-ID. TESTV13.\n"
        "       PROCEDURE DIVISION.\n"
        "       PROCESS-PARA.\n"
        "           MOVE VAR-A TO VAR-B.\n"
        "           COMPUTE VAR-X = VAR-A + VAR-B.\n"
        "           IF VAR-X > ZERO\n"
        "               MOVE VAR-X TO VAR-C\n"
        "           END-IF.\n"
        "           GOBACK.\n"
    )

    def test_v13_statements_ordering(self):
        result = _extract_synthetic(self._SRC_V13)
        pdf = result.get('paragraph_data_flow', {})

        self.assertIn('PROCESS-PARA', pdf,
            f'Expected PROCESS-PARA in paragraph_data_flow, got: {list(pdf.keys())}')

        stmts = pdf['PROCESS-PARA'].get('statements', [])
        self.assertTrue(len(stmts) >= 3,
            f'Expected at least 3 statements, got: {stmts}')

        # seq must be 1-based and ordered
        seqs = [s['seq'] for s in stmts]
        self.assertEqual(seqs, list(range(1, len(stmts) + 1)),
            f'seq values must be consecutive 1-based: {seqs}')

        # first statement must be MOVE
        self.assertEqual(stmts[0]['verb'], 'MOVE',
            f'First statement verb must be MOVE, got: {stmts[0].get("verb")}')
        self.assertEqual(stmts[0]['seq'], 1,
            f'First statement seq must be 1, got: {stmts[0].get("seq")}')

        # second statement must be COMPUTE
        self.assertEqual(stmts[1]['verb'], 'COMPUTE',
            f'Second statement verb must be COMPUTE, got: {stmts[1].get("verb")}')

        # all entries must have seq, verb, sources, targets keys
        for s in stmts:
            for key in ('seq', 'verb', 'sources', 'targets'):
                self.assertIn(key, s,
                    f'Statement missing required key "{key}": {s}')

    def test_v13_schema_version_is_1_4(self):
        result = _extract_synthetic(self._SRC_V13)
        self.assertEqual(result.get('schema_version'), '1.4',
            f'Expected schema_version="1.4", got: {result.get("schema_version")}')
```

**After editing, verify scope and run V13 in isolation:**
```powershell
git diff --stat
# Must show ONLY: scripts/data_flow.py, tests/test_data_flow.py

C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  -m pytest tests/test_data_flow.py -k "v13" -v 2>&1
```

**If diff shows any unexpected file:**
```powershell
git checkout -- .
```
Mark G2 BLOCKED. STOP.

**If either V13 test fails — paste exact error. Mark G2 BLOCKED. STOP.**
**Do NOT proceed to G3 with a failing V13 test.**

**After RESULT is pasted:**
- Update CURRENT CONTEXT: Last = "G2 DONE", Next = G3
- Mark step [DONE]
- STOP. Report to human.

**RESULT:**
```powershell
PS C:\work\HermesCOBOL> git diff --stat
.clinerules/scratchpad.md | 513 ++++++++++++++++++++++++----------------------
 scripts/data_flow.py      |  69 ++++++-
 tests/test_data_flow.py   |  67 +++++-
 3 files changed, 391 insertions(+), 258 deletions(-)

# V13 tests pass
PS C:\work\HermesCOBOL> C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests/test_data_flow.py -k "v13" -v
================================== test session starts ==================================
platform win32 -- Python 3.10.11, pytest-7.4.3, pluggy-1.6.0
rootdir: C:\work\HermesCOBOL
plugins: anyio-3.7.1, asyncio-0.21.1, typeguard-4.4.4
asyncio: mode=strict
collecting ... 75 tests, 73 deselected / 2 selected

tests/test_data_flow.py::TestV13StatementsOrdering::test_v13_statements_ordering PASSED [50%]
tests/test_data_flow.py::TestV13StatementsOrdering::test_v13_schema_version_is_1_4 PASSED [100%]

=========================== 2 passed, 73 deselected in 0.06s ============================

# Full suite passes with 127 tests
PS C:\work\HermesCOBOL> C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -m pytest tests/ -q
........................................................................ [ 56%]
.......................................................                  [100%]
127 passed in 0.77s

---

### STEP G3 [PENDING]

**Goal:** Full suite must be 127/127 (125 existing + 2 new V13). Commit and push.

**Commands:**
```powershell
# Full suite
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  -m pytest tests/ -q 2>&1 | Select-Object -Last 5

# Stage only permitted files
git add scripts/data_flow.py tests/test_data_flow.py .clinerules/scratchpad.md
git diff --cached --name-only

# ONLY if 127 passed AND 0 failed AND cached files are exactly the 3 above:
git commit -m "feat(stage4e): V13 statements[] ordering; schema 1.3->1.4"
git push origin main
git log --oneline -1
```

**Pass condition:**
- Total: exactly 127 passed, 0 failed
- `git diff --cached --name-only` shows ONLY:
  - `scripts/data_flow.py`
  - `tests/test_data_flow.py`
  - `.clinerules/scratchpad.md`
- `git log` shows new commit on main

**Failure actions:**
- Any test fails → paste exact error, mark G3 BLOCKED, STOP
- Total ≠ 127 → `git checkout -- .`, mark BLOCKED, STOP
- Unexpected cached file → `git reset HEAD`, mark BLOCKED, STOP

**After RESULT is pasted:**
- Update CURRENT CONTEXT: Last = "G3 DONE — V13 closed, 127/127", Next = IDLE
- Mark step [DONE]
- STOP. Report to human.

**RESULT:**
<!-- Paste pytest output and git log here -->

---

## EXECUTION RULES

- Permitted: `scripts/data_flow.py`, `tests/test_data_flow.py`, `.clinerules/scratchpad.md`
- Forbidden: all other files
- Forbidden: modifying any existing test class or method
- Forbidden: committing with any failing test
- After every step: update CURRENT CONTEXT, mark step [DONE] or [BLOCKED], STOP
- Before G2: total must be 125. After G2+G3: total must be 127. Any other count = BLOCKED.
  (test_data_flow.py goes 73→75; test_byte_layout.py=21; test_extract_facts_alignment.py=31)
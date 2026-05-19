Set-Location C:\work\HermesCOBOL

# Revert the bad append
git checkout -- scripts\SCRIPTS_INVENTORY.md

Write-Host "=== VERIFY REVERT ===" -ForegroundColor Cyan
git diff scripts\SCRIPTS_INVENTORY.md

# Now re-append using Python to avoid PowerShell encoding/escape issues
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
from pathlib import Path

inv = Path('scripts/SCRIPTS_INVENTORY.md')

append = '''

---

## Section 6 — CobolWalker v0.1 Scripts

### cobol_walker.py
- **Location:** scripts\\\\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Deterministic DFS walker over CobolProgramDict — yields paragraph names via performs + falls_through_to edges only. Supports include_dead_code=False (live paragraphs only) and include_dead_code=True (live + unvisited paragraphs in canonical source order).
- **Inputs:** CobolProgramDict instance (data\\\\canonical\\\\<PROG>.canonical.json)
- **Outputs:** Generator of paragraph name strings
- **Gate dependency:** CobolWalker v0.1 Gates 1-10 (all green)
- **Notes:** Does NOT follow goto_targets — see goto_targets blind spots section below. Deterministic across runs. Deduplication guaranteed (no paragraph yielded twice). Walker entry point: CobolWalker(prog).walk(include_dead_code=bool).

### audit_cobol_walker.py
- **Location:** scripts\\\\
- **Origin:** HermesCOBOL
- **Status:** ACTIVE
- **Purpose:** Walks all 31 programs under both flag settings and emits validation\\\\walker-baseline.json containing per-program live_count, full_count, entry_paragraph, first_five, and last_three. Gate 10 regression hook — called by validate_roundtrip.py on every run.
- **Inputs:** data\\\\canonical\\\\*.canonical.json (all 31 programs)
- **Outputs:** validation\\\\walker-baseline.json
- **Gate dependency:** CobolWalker v0.1 Gate 10 (green)
- **Notes:** On first run: creates baseline. On subsequent runs: verifies current walk output matches saved baseline — FAIL if diverged. Run standalone: python scripts\\\\audit_cobol_walker.py. Baseline sums: live=205, full=518 across 31 programs.

---

## CobolWalker v0.1 — goto_targets Blind Spots (Post-Validation Update)

**Last updated:** 2026-05-19 (rev 7 — updated after v0.1 full gate validation)
**Status:** Accepted limitation. Documented per SPEC-CobolWalker.md.

The walker (performs + falls_through_to edges only) does not traverse goto_targets.
Programs where goto_targets are the primary control-flow mechanism show low live
counts under walk(include_dead_code=False). All confirmed as correct walker behavior.

| Program     | live_count | full_count | Notes                                      |
|-------------|------------|------------|--------------------------------------------|
| CBSTM03A    | 1          | 25         | goto-driven dispatch from 0000-START (7 blind targets) |
| CBSTM03B    | 5          | 14         | goto-driven exit targets (5 blind targets) |
| COACTUPC    | 1          | 85         | CICS program, goto-heavy                   |
| COACTVWC    | 1          | 34         | CICS program, goto-heavy                   |
| COBIL00C    | 2          | 16         | goto-based dispatch                        |
| COCRDLIC    | 1          | 39         | CICS program, goto-heavy                   |
| COMEN01C    | 1          | 7          | goto-based dispatch                        |
| CORPT00C    | 1          | 10         | goto-based dispatch                        |
| COSGN00C    | 1          | 6          | goto-based dispatch                        |
| COTRN00C    | 1          | 16         | goto-based dispatch                        |
| COTRN01C    | 2          | 9          | goto-based dispatch                        |
| COUSR00C    | 1          | 16         | goto-based dispatch                        |
| COUSR01C    | 2          | 9          | goto-based dispatch                        |
| COUSR02C    | 2          | 11         | goto-based dispatch                        |
| COUSR03C    | 2          | 11         | goto-based dispatch                        |

These are not bugs. goto_targets traversal is deferred to CobolWalker v0.2.
Consumers needing full goto coverage must additionally consult paragraph[\"goto_targets\"]
from the underlying CobolProgramDict.
'''

with open(inv, 'a', encoding='utf-8') as f:
    f.write(append)
print('Append complete')
"

Write-Host "=== GIT DIFF (verify clean) ===" -ForegroundColor Cyan
git diff scripts\SCRIPTS_INVENTORY.md | Select-Object -Last 80
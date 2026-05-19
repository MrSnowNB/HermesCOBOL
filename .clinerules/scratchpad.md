# ═══════════════════════════════════════════════════════
# CobolWalker v0.1 — Gated Validation
# Run ALL steps in order. Report PASS/FAIL for each.
# ═══════════════════════════════════════════════════════

Write-Host "=== GATE 1: Import check ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict
print('IMPORT OK')
"

Write-Host "=== GATE 2: Entry paragraph is always first ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import sys, glob, os
sys.path.insert(0, '.')
from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict

failures = []
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog_name = os.path.basename(path).replace('.canonical.json','')
    prog = CobolProgramDict(prog_name)
    w = CobolWalker(prog)
    if not prog.paragraphs:
        continue
    for flag in [False, True]:
        result = list(w.walk(include_dead_code=flag))
        if not result or result[0] != prog.entry_paragraph:
            failures.append((prog_name, flag, result[:1], prog.entry_paragraph))

if failures:
    print(f'FAIL — entry_paragraph not first in {len(failures)} cases:')
    for f in failures: print(f'  {f}')
else:
    print('PASS — entry_paragraph is first for all 31 programs (both flag settings)')
"

Write-Host "=== GATE 3: Live corpus count == 495 ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import sys, glob, os
sys.path.insert(0, '.')
from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict

total = 0
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog_name = os.path.basename(path).replace('.canonical.json','')
    w = CobolWalker(CobolProgramDict(prog_name))
    total += len(list(w.walk(include_dead_code=False)))

print(f'Live paragraph count across corpus: {total}')
print('PASS' if total == 495 else f'FAIL — expected 495 got {total}')
"

Write-Host "=== GATE 4: Full corpus count == 518 ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import sys, glob, os
sys.path.insert(0, '.')
from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict

total = 0
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog_name = os.path.basename(path).replace('.canonical.json','')
    w = CobolWalker(CobolProgramDict(prog_name))
    total += len(list(w.walk(include_dead_code=True)))

print(f'Full paragraph count (include_dead_code=True): {total}')
print('PASS' if total == 518 else f'FAIL — expected 518 got {total}')
"

Write-Host "=== GATE 5: Referential integrity of yielded names ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import sys, glob, os
sys.path.insert(0, '.')
from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict

violations = []
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog_name = os.path.basename(path).replace('.canonical.json','')
    prog = CobolProgramDict(prog_name)
    w = CobolWalker(prog)
    para_names = set(prog.paragraphs.keys())
    for flag in [False, True]:
        for name in w.walk(include_dead_code=flag):
            if name not in para_names:
                violations.append((prog_name, flag, name))

if violations:
    print(f'FAIL — {len(violations)} dangling paragraph names yielded:')
    for v in violations: print(f'  {v}')
else:
    print('PASS — all yielded names exist in CobolProgramDict.paragraphs')
"

Write-Host "=== GATE 6: Determinism (3 successive calls) ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import sys, glob, os
sys.path.insert(0, '.')
from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict

failures = []
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog_name = os.path.basename(path).replace('.canonical.json','')
    prog = CobolProgramDict(prog_name)
    w = CobolWalker(prog)
    for flag in [False, True]:
        r1 = list(w.walk(include_dead_code=flag))
        r2 = list(w.walk(include_dead_code=flag))
        r3 = list(w.walk(include_dead_code=flag))
        if not (r1 == r2 == r3):
            failures.append((prog_name, flag))

if failures:
    print(f'FAIL — non-deterministic output for: {failures}')
else:
    print('PASS — all 31 programs produce identical output across 3 successive calls')
"

Write-Host "=== GATE 7: No duplicates in any walk sequence ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import sys, glob, os
sys.path.insert(0, '.')
from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict

failures = []
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog_name = os.path.basename(path).replace('.canonical.json','')
    w = CobolWalker(CobolProgramDict(prog_name))
    for flag in [False, True]:
        result = list(w.walk(include_dead_code=flag))
        if len(result) != len(set(result)):
            dupes = [x for x in result if result.count(x) > 1]
            failures.append((prog_name, flag, dupes))

if failures:
    print(f'FAIL — duplicates found:')
    for f in failures: print(f'  {f}')
else:
    print('PASS — no duplicate paragraph names in any walk sequence')
"

Write-Host "=== GATE 8: CICS and dead-code handling ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import sys, glob, os
sys.path.insert(0, '.')
from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict

cics_failures = []
dead_code_failures = []

for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog_name = os.path.basename(path).replace('.canonical.json','')
    prog = CobolProgramDict(prog_name)
    w = CobolWalker(prog)
    live = list(w.walk(include_dead_code=False))
    full = list(w.walk(include_dead_code=True))

    # CICS: full walk must equal total paragraph count
    if prog.is_cics:
        if len(full) != len(prog.paragraphs):
            cics_failures.append((prog_name, len(full), len(prog.paragraphs)))

    # Dead code: programs with dead paragraphs must suppress/include correctly
    dead = prog.dead_code_paragraphs
    if dead:
        for dp in dead:
            if dp in live:
                dead_code_failures.append((prog_name, 'dead in live walk', dp))
            if dp not in full:
                dead_code_failures.append((prog_name, 'dead missing from full walk', dp))
        # Dead paragraphs must appear AFTER all live paragraphs in full walk
        live_set = set(live)
        full_dead_section = [x for x in full if x not in live_set]
        if full_dead_section != dead:
            dead_code_failures.append((prog_name, 'dead code not in source order after live', full_dead_section))

print(f'Programs with dead code: {[os.path.basename(p).replace(\".canonical.json\",\"\") for p in glob.glob(\"data/canonical/*.canonical.json\") if CobolProgramDict(os.path.basename(p).replace(\".canonical.json\",\"\")).dead_code_paragraphs]}')
if cics_failures:
    print(f'FAIL CICS — {cics_failures}')
elif dead_code_failures:
    print(f'FAIL dead-code — {dead_code_failures}')
else:
    print('PASS — CICS paragraph counts correct, dead code suppressed/surfaced correctly')
"

Write-Host "=== GATE 9: No regression on existing gates ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  scripts\validate_canonical_ir.py 2>&1 | Select-Object -Last 2
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  scripts\validate_roundtrip.py 2>&1 | Select-Object -Last 2
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  -m pytest tests/ -q --tb=short 2>&1 | Select-Object -Last 3
# Expected: 31/31 PASS, 31 passed 0 fail, 136 passed

Write-Host "=== GATE 10: Audit script exists and produces baseline ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  scripts\audit_cobol_walker.py 2>&1 | Select-Object -Last 5
# Expected: JSON summary written to validation/walker-baseline.json
# Verify the file exists:
Test-Path validation\walker-baseline.json
# ═══════════════════════════════════════════════════════
# CobolWalker — Gate 8 & Gate 10 Targeted Verification
# ═══════════════════════════════════════════════════════

Set-Location C:\work\HermesCOBOL
git pull origin main

Write-Host "=== GATE 3: Live count still 205 ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import sys, glob, os
sys.path.insert(0, '.')
from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict
total = sum(
    len(list(CobolWalker(CobolProgramDict(
        os.path.basename(p).replace('.canonical.json','')
    )).walk(include_dead_code=False)))
    for p in sorted(glob.glob('data/canonical/*.canonical.json'))
)
print(f'Live total: {total}')
print('PASS' if total == 205 else f'FAIL — expected 205 got {total}')
"

Write-Host "=== GATE 4: Full count still 518 ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import sys, glob, os
sys.path.insert(0, '.')
from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict
total = sum(
    len(list(CobolWalker(CobolProgramDict(
        os.path.basename(p).replace('.canonical.json','')
    )).walk(include_dead_code=True)))
    for p in sorted(glob.glob('data/canonical/*.canonical.json'))
)
print(f'Full total: {total}')
print('PASS' if total == 518 else f'FAIL — expected 518 got {total}')
"

Write-Host "=== GATE 7: Still no duplicates ===" -ForegroundColor Cyan
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
        r = list(w.walk(include_dead_code=flag))
        if len(r) != len(set(r)):
            failures.append((prog_name, flag, [x for x in set(r) if r.count(x)>1]))
print('PASS — no duplicates' if not failures else f'FAIL: {failures}')
"

Write-Host "=== GATE 8: Dead-code handling (full diagnostic) ===" -ForegroundColor Cyan
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
    live = list(w.walk(include_dead_code=False))
    full = list(w.walk(include_dead_code=True))
    live_set = set(live)
    all_para_names = list(prog.paragraphs.keys())

    expected_tail = [n for n in all_para_names if n not in live_set]
    actual_tail   = [n for n in full if n not in live_set]

    if expected_tail != actual_tail:
        failures.append((prog_name, f'tail mismatch expected={expected_tail} got={actual_tail}'))

    # CICS: full walk must equal total paragraph count
    if prog.is_cics and len(full) != len(prog.paragraphs):
        failures.append((prog_name, f'CICS count full={len(full)} para={len(prog.paragraphs)}'))

    if expected_tail:
        print(f'  {prog_name}: live={len(live)} unvisited={len(expected_tail)} tail_match={expected_tail==actual_tail}')

if failures:
    print(f'FAIL: {failures}')
else:
    print('PASS — dead-code handling correct for all programs')
"

Write-Host "=== GATE 9: 136-test regression ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
    -m pytest tests/ -q --tb=short 2>&1 | Select-Object -Last 3

Write-Host "=== GATE 10: audit_cobol_walker.py exists? ===" -ForegroundColor Cyan
Test-Path C:\work\HermesCOBOL\scripts\audit_cobol_walker.py
Test-Path C:\work\HermesCOBOL\validation\walker-baseline.json
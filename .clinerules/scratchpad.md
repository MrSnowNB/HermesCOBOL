# ═══════════════════════════════════════════════════════
# CobolWalker v0.1 — FINAL Full Gate Run
# All 10 gates. Report exact output for each.
# ═══════════════════════════════════════════════════════

Set-Location C:\work\HermesCOBOL
git pull origin main

Write-Host "=== GATE 1: Import check ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict
print('IMPORT OK')
"

Write-Host "=== GATE 2: Entry paragraph always first ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import sys, glob, os
sys.path.insert(0, '.')
from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict
failures = []
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog_name = os.path.basename(path).replace('.canonical.json','')
    prog = CobolProgramDict(prog_name)
    if not prog.paragraphs: continue
    w = CobolWalker(prog)
    for flag in [False, True]:
        result = list(w.walk(include_dead_code=flag))
        if not result or result[0] != prog.entry_paragraph:
            failures.append((prog_name, flag, result[:1], prog.entry_paragraph))
print('PASS' if not failures else f'FAIL: {failures}')
"

Write-Host "=== GATE 3: Live corpus count == 205 ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import sys, glob, os
sys.path.insert(0, '.')
from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict
total = 0
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog_name = os.path.basename(path).replace('.canonical.json','')
    count = len(list(CobolWalker(CobolProgramDict(prog_name)).walk(include_dead_code=False)))
    total += count
    print(f'  {prog_name}: {count}')
print(f'TOTAL live: {total}')
print('PASS' if total == 205 else f'FAIL — expected 205 got {total}')
"

Write-Host "=== GATE 4: Full corpus count == 518 ===" -ForegroundColor Cyan
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
print(f'TOTAL full: {total}')
print('PASS' if total == 518 else f'FAIL — expected 518 got {total}')
"

Write-Host "=== GATE 5: Referential integrity ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import sys, glob, os
sys.path.insert(0, '.')
from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict
violations = []
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog_name = os.path.basename(path).replace('.canonical.json','')
    prog = CobolProgramDict(prog_name)
    para_names = set(prog.paragraphs.keys())
    w = CobolWalker(prog)
    for flag in [False, True]:
        for name in w.walk(include_dead_code=flag):
            if name not in para_names:
                violations.append((prog_name, flag, name))
print('PASS' if not violations else f'FAIL: {violations}')
"

Write-Host "=== GATE 6: Determinism ===" -ForegroundColor Cyan
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
        r1,r2,r3 = [list(w.walk(include_dead_code=flag)) for _ in range(3)]
        if not (r1==r2==r3): failures.append((prog_name, flag))
print('PASS' if not failures else f'FAIL: {failures}')
"

Write-Host "=== GATE 7: No duplicates ===" -ForegroundColor Cyan
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
print('PASS' if not failures else f'FAIL: {failures}')
"

Write-Host "=== GATE 8: Dead-code handling (visited-set logic) ===" -ForegroundColor Cyan
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
    all_names = list(prog.paragraphs.keys())
    expected_tail = [n for n in all_names if n not in live_set]
    actual_tail   = [n for n in full if n not in live_set]
    if expected_tail != actual_tail:
        failures.append((prog_name, f'expected={expected_tail[:3]}... got={actual_tail[:3]}...'))
    if prog.is_cics and len(full) != len(prog.paragraphs):
        failures.append((prog_name, f'CICS full={len(full)} para={len(prog.paragraphs)}'))
    if expected_tail:
        print(f'  {prog_name}: live={len(live)} unvisited={len(expected_tail)} match={expected_tail==actual_tail}')
print('PASS' if not failures else f'FAIL: {failures}')
"

Write-Host "=== GATE 9: Full regression suite ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
    scripts\validate_canonical_ir.py 2>&1 | Select-Object -Last 2
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
    scripts\validate_roundtrip.py 2>&1 | Select-Object -Last 4
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
    -m pytest tests/ -q --tb=short 2>&1 | Select-Object -Last 3

Write-Host "=== GATE 10: Audit script + baseline exist and match ===" -ForegroundColor Cyan
Test-Path C:\work\HermesCOBOL\scripts\audit_cobol_walker.py
Test-Path C:\work\HermesCOBOL\validation\walker-baseline.json
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import json
from pathlib import Path
baseline = json.loads(Path('validation/walker-baseline.json').read_text())
print(f'Programs in baseline: {len(baseline)}')
print(f'First entry: {baseline[0][\"program\"]} live={baseline[0][\"live_count\"]} full={baseline[0][\"full_count\"]}')
print(f'Last entry:  {baseline[-1][\"program\"]} live={baseline[-1][\"live_count\"]} full={baseline[-1][\"full_count\"]}')
total_live = sum(e['live_count'] for e in baseline)
total_full = sum(e['full_count'] for e in baseline)
print(f'Sum live: {total_live} (expect 205)')
print(f'Sum full: {total_full} (expect 518)')
print('PASS' if len(baseline)==31 and total_live==205 and total_full==518 else 'FAIL')
"
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
    scripts\audit_cobol_walker.py 2>&1
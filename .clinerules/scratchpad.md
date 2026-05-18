# ═══════════════════════════════════════════════════════
# CobolProgramDict v0.1 — Gated Validation
# Run ALL steps. Report PASS/FAIL for each.
# ═══════════════════════════════════════════════════════

Write-Host "=== GATE 1: Import check ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
from scripts.cobol_program_dict import CobolProgramDict
print('IMPORT OK')
"

Write-Host "=== GATE 2: All 31 programs instantiate ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import os, sys
sys.path.insert(0, '.')
from scripts.cobol_program_dict import CobolProgramDict
import glob

failed = []
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog = os.path.basename(path).replace('.canonical.json','')
    try:
        d = CobolProgramDict(prog)
        _ = d.paragraphs
        _ = d.is_cics
        _ = d.reachable_paragraphs
    except Exception as e:
        failed.append((prog, str(e)))

if failed:
    print(f'FAIL — {len(failed)} programs failed to instantiate:')
    for prog, err in failed: print(f'  {prog}: {err}')
else:
    print('PASS — all 31 programs instantiated successfully')
"

Write-Host "=== GATE 3: Paragraph count == 518 total ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import os, sys, glob
sys.path.insert(0, '.')
from scripts.cobol_program_dict import CobolProgramDict

total = 0
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog = os.path.basename(path).replace('.canonical.json','')
    d = CobolProgramDict(prog)
    total += len(d.paragraphs)

print(f'Total paragraphs across corpus: {total}')
print('PASS' if total == 518 else f'FAIL — expected 518 got {total}')
"

Write-Host "=== GATE 4: No noise tokens in any paragraph name ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import os, sys, glob
sys.path.insert(0, '.')
from scripts.cobol_program_dict import CobolProgramDict
from scripts.cobol_parse_utils import PARAGRAPH_NOISE, RESERVED_WORDS

noise_found = []
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog = os.path.basename(path).replace('.canonical.json','')
    d = CobolProgramDict(prog)
    for name in d.paragraphs:
        if name in PARAGRAPH_NOISE or name in RESERVED_WORDS:
            noise_found.append((prog, name))

if noise_found:
    print(f'FAIL — noise tokens found in paragraph names:')
    for prog, name in noise_found: print(f'  {prog}: {name}')
else:
    print('PASS — no noise tokens in any paragraph name')
"

Write-Host "=== GATE 5: Referential integrity via CobolProgramDict ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import os, sys, glob
sys.path.insert(0, '.')
from scripts.cobol_program_dict import CobolProgramDict

violations = []
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog = os.path.basename(path).replace('.canonical.json','')
    d = CobolProgramDict(prog)
    para_names = set(d.paragraphs.keys())
    for name, para in d.paragraphs.items():
        for target in para.get('performs', []) or []:
            if target not in para_names:
                violations.append((prog, name, 'performs', target))
        ft = para.get('falls_through_to')
        if ft and ft not in para_names:
            violations.append((prog, name, 'falls_through_to', ft))

if violations:
    print(f'FAIL — {len(violations)} referential integrity violations:')
    for v in violations: print(f'  {v}')
else:
    print('PASS — all performs and falls_through_to targets are valid')
"

Write-Host "=== GATE 6: CICS flag correctness ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import os, sys, glob, json
sys.path.insert(0, '.')
from scripts.cobol_program_dict import CobolProgramDict

mismatches = []
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog = os.path.basename(path).replace('.canonical.json','')
    raw = json.load(open(path))
    d = CobolProgramDict(prog)
    expected = raw.get('cics_present', False)
    if d.is_cics != expected:
        mismatches.append((prog, expected, d.is_cics))

if mismatches:
    print(f'FAIL — is_cics mismatch:')
    for prog, exp, got in mismatches: print(f'  {prog}: expected={exp} got={got}')
else:
    print('PASS — is_cics matches canonical IR for all 31 programs')
"

Write-Host "=== GATE 7: Reachability correctness ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import os, sys, glob
sys.path.insert(0, '.')
from scripts.cobol_program_dict import CobolProgramDict

total_reachable = 0
total_dead = 0
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog = os.path.basename(path).replace('.canonical.json','')
    d = CobolProgramDict(prog)
    total_reachable += len(d.reachable_paragraphs)
    total_dead += len(d.dead_code_paragraphs)

total = total_reachable + total_dead
print(f'Total paragraphs        : {total}')
print(f'  reachable             : {total_reachable}')
print(f'  dead code             : {total_dead}')
print('PASS' if total == 518 else f'FAIL — reachable+dead should equal 518, got {total}')
# Expected: ~495 reachable, ~23 dead (matching earlier snapshot)
"

Write-Host "=== GATE 8: Data source resilience ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import os, sys
sys.path.insert(0, '.')
from scripts.cobol_program_dict import CobolProgramDict
import pathlib

# Temporarily hide optional file
test_prog = 'CBACT01C'
optional_path = pathlib.Path(f'data/byte_layouts/{test_prog}.json')
hidden_path = pathlib.Path(f'data/byte_layouts/{test_prog}.json.hidden')

hidden = False
if optional_path.exists():
    optional_path.rename(hidden_path)
    hidden = True

try:
    d = CobolProgramDict(test_prog)
    paras = d.paragraphs
    items = d.data_items
    print(f'Instantiated OK: {len(paras)} paragraphs, data_items={items!r:.40}...')
    print('PASS — class works without optional byte_layouts file')
except Exception as e:
    print(f'FAIL — raised exception: {e}')
finally:
    if hidden and hidden_path.exists():
        hidden_path.rename(optional_path)
        print('(optional file restored)')
"

Write-Host "=== GATE 9: No regression — existing pipeline gates ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  scripts\validate_canonical_ir.py 2>&1 | Select-Object -Last 2
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  scripts\validate_roundtrip.py 2>&1 | Select-Object -Last 2
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  -m pytest tests/ -q --tb=short 2>&1 | Select-Object -Last 3
# Expected: 31/31 PASS, Pass 31 Fail 0, 136 passed

Write-Host "=== GATE 10: Corpus summary snapshot ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import os, sys, glob
sys.path.insert(0, '.')
from scripts.cobol_program_dict import CobolProgramDict

cics = 0
non_cics = 0
total_ext_calls = 0
total_copybooks = 0
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog = os.path.basename(path).replace('.canonical.json','')
    d = CobolProgramDict(prog)
    if d.is_cics: cics += 1
    else: non_cics += 1
    total_ext_calls += len(d.external_calls)
    total_copybooks += len(d.copybooks_referenced)

print(f'CICS programs     : {cics}')
print(f'Non-CICS programs : {non_cics}')
print(f'Total ext calls   : {total_ext_calls}')
print(f'Total copybooks   : {total_copybooks}')
"
# ═══════════════════════════════════════════════════════
# FULL PIPELINE STATE VERIFICATION — Pre-CobolProgramDict
# Run ALL steps. Report PASS/FAIL for each.
# ═══════════════════════════════════════════════════════

Write-Host "=== STEP 1: Full pipeline rerun from scratch ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  scripts\extract_cfg_local.py --all 2>&1 | Select-Object -Last 2
echo "CFG Exit: $LASTEXITCODE"

C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  scripts\extract_fallthrough.py --all 2>&1 | Select-Object -Last 2
echo "Fallthrough Exit: $LASTEXITCODE"

C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  scripts\assemble_canonical.py 2>&1 | Select-Object -Last 2
echo "Assemble Exit: $LASTEXITCODE"

Write-Host "=== STEP 2: Stage 5-H gate ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  scripts\validate_canonical_ir.py 2>&1
echo "Gate Exit: $LASTEXITCODE"
# Expected: 31/31 PASS

Write-Host "=== STEP 3: Roundtrip validator ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  scripts\validate_roundtrip.py 2>&1 | Select-Object -Last 4
echo "Roundtrip Exit: $LASTEXITCODE"
# Expected: Pass 31, Fail 0

Write-Host "=== STEP 4: Full test suite ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  -m pytest tests/ -q --tb=short 2>&1 | Select-Object -Last 5
echo "Pytest Exit: $LASTEXITCODE"
# Expected: 136 passed

Write-Host "=== STEP 5: Canonical IR health snapshot ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import json, glob, os
total_progs = 0
total_paras = 0
cics_progs = 0
non_cics = 0
reachable_false = 0
has_performs = 0
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    d = json.load(open(path))
    total_progs += 1
    paras = d.get('paragraphs', [])
    total_paras += len(paras)
    if d.get('cics_present'):
        cics_progs += 1
    else:
        non_cics += 1
    for p in paras:
        if not p.get('reachable', True):
            reachable_false += 1
        if p.get('performs'):
            has_performs += 1
print(f'Programs        : {total_progs}')
print(f'  Non-CICS      : {non_cics}')
print(f'  CICS          : {cics_progs}')
print(f'Total paragraphs: {total_paras}')
print(f'  reachable=False (dead code): {reachable_false}')
print(f'  with performs[] populated  : {has_performs}')
"

Write-Host "=== STEP 6: Noise cleanliness — CFG ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import json, glob
noise = {'STOP','EXIT','GOBACK','END-IF','END-EXEC','FILLER','EVALUATE',
         'PERFORM','MOVE','IF','ELSE','END-EVALUATE','WHEN',
         'END-PERFORM','END-READ','END-WRITE','END-CALL','CONTINUE',
         'END-STRING','END-REWRITE','SECTION','DIVISION'}
found = []
for path in glob.glob('data/cfg/*.json'):
    d = json.load(open(path))
    for p in d.get('paragraphs', []):
        if p['name'] in noise:
            found.append((path, p['name']))
print('CFG noise check:', 'CLEAN' if not found else f'{len(found)} violations')
"

Write-Host "=== STEP 7: Noise cleanliness — fallthrough ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import json, glob, os
bad = []
for path in sorted(glob.glob('data/fallthrough/*.json')):
    prog = os.path.basename(path).replace('.json','')
    d = json.load(open(path))
    for p in d.get('paragraphs', []):
        ft = p.get('falls_through_to')
        if ft and 'END-' in ft:
            bad.append((prog, p['paragraph'], ft))
print('Fallthrough END-* check:', 'CLEAN' if not bad else f'{len(bad)} violations')
for prog,para,ft in bad:
    print(f'  {prog}.{para} -> {ft}')
"

Write-Host "=== STEP 8: Schema version check ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import json, glob
versions = set()
for path in glob.glob('data/canonical/*.canonical.json'):
    d = json.load(open(path))
    versions.add(d.get('schema_version'))
print('Schema versions in corpus:', versions)
# Expected: {'1.4'} only
"

Write-Host "=== STEP 9: Required paragraph fields — full corpus ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import json, glob, os
REQUIRED = {'name','terminator','falls_through_to','performs','goto_targets','reachable'}
missing_any = []
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog = os.path.basename(path).replace('.canonical.json','')
    d = json.load(open(path))
    for p in d.get('paragraphs', []):
        missing = REQUIRED - set(p.keys())
        if missing:
            missing_any.append((prog, p.get('name','?'), missing))
if missing_any:
    print(f'MISSING FIELDS in {len(missing_any)} paragraphs:')
    for prog,name,m in missing_any: print(f'  {prog}.{name}: {m}')
else:
    print('ALL paragraphs have all 6 required fields')
"

Write-Host "=== FINAL: Git status ===" -ForegroundColor Cyan
git status --porcelain
# Expected: empty (clean working tree) or only untracked files
# No modified source files should appear
# ═══════════════════════════════════════════════════════
# GATED VALIDATION: extract_cfg_local.py migration
# Run ALL steps in order. Report PASS/FAIL for each.
# Do NOT skip any step. Stop and report on first failure.
# ═══════════════════════════════════════════════════════

Write-Host "=== PRE-FLIGHT: Confirm only one file changed ===" -ForegroundColor Cyan
git diff --name-only HEAD
# Expected: scripts/extract_cfg_local.py only
# If any other file appears: FAIL — do not continue

Write-Host "=== PRE-FLIGHT: Confirm old function is gone ===" -ForegroundColor Cyan
Select-String -Path scripts\extract_cfg_local.py -Pattern "def extract_paragraphs"
# Expected: 0 matches (the old 3-token weak function must not exist)
# New function is _extract_paragraphs_ordered — confirm:
Select-String -Path scripts\extract_cfg_local.py -Pattern "def _extract_paragraphs_ordered"
# Expected: 1 match

Write-Host "=== PRE-FLIGHT: Confirm authoritative import present ===" -ForegroundColor Cyan
Select-String -Path scripts\extract_cfg_local.py -Pattern "from cobol_parse_utils import"
# Expected: 1 match

Write-Host "=== PRE-FLIGHT: Confirm analyze_flow guard present ===" -ForegroundColor Cyan
Select-String -Path scripts\extract_cfg_local.py -Pattern "PARAGRAPH_NOISE"
# Expected: at least 2 matches (import line + analyze_flow guard)

Write-Host "=== GATE 1: Regenerate all CFG files ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  scripts\extract_cfg_local.py --all 2>&1 | Select-Object -Last 3
echo "Exit: $LASTEXITCODE"
# Expected: 31/31 complete, exit 0

Write-Host "=== GATE 2: Reassemble canonical IR ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  scripts\assemble_canonical.py 2>&1 | Select-Object -Last 3
echo "Exit: $LASTEXITCODE"
# Expected: 31/31 complete, exit 0

Write-Host "=== GATE 3: Stage 5-H validation gate ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  scripts\validate_canonical_ir.py 2>&1
echo "Exit: $LASTEXITCODE"
# Expected: 31/31 PASS, exit 0

Write-Host "=== GATE 4: Roundtrip validator ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  scripts\validate_roundtrip.py 2>&1 | Select-Object -Last 5
echo "Exit: $LASTEXITCODE"
# Expected: Pass 31, Fail 0, exit 0

Write-Host "=== GATE 5: Full test suite ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  -m pytest tests/ -q --tb=short 2>&1 | Select-Object -Last 5
echo "Exit: $LASTEXITCODE"
# Expected: 136 passed, exit 0

Write-Host "=== GATE 6: Noise cleanliness verification ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import json, glob
noise = {'STOP','EXIT','GOBACK','END-IF','END-EXEC','FILLER','EVALUATE',
         'PERFORM','MOVE','IF','ELSE','END-EVALUATE','WHEN','END-WHEN',
         'END-PERFORM','END-READ','END-WRITE','END-CALL','CONTINUE',
         'SECTION','DIVISION'}
found = []
for path in glob.glob('data/cfg/*.json'):
    d = json.load(open(path))
    for p in d.get('paragraphs', []):
        if p['name'] in noise:
            found.append((path, p['name']))
if found:
    print('FAIL — noise tokens found:')
    for f,n in found: print(f'  {n} in {f}')
else:
    print('CLEAN — no noise tokens in any CFG paragraph list')
"
# Expected: CLEAN — no noise tokens in any CFG paragraph list

Write-Host "=== GATE 7: Paragraph count audit ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import json, glob
total_cfg = 0
total_facts = 0
mismatches = []
import os
for cfg_path in sorted(glob.glob('data/cfg/*.json')):
    prog = os.path.basename(cfg_path).replace('.json','')
    facts_path = f'data/facts/{prog}.json'
    cfg = json.load(open(cfg_path))
    cfg_count = len(cfg.get('paragraphs', []))
    total_cfg += cfg_count
    if os.path.exists(facts_path):
        facts = json.load(open(facts_path))
        facts_count = len(facts.get('paragraphs', []))
        total_facts += facts_count
        if cfg_count != facts_count:
            mismatches.append((prog, facts_count, cfg_count))
print(f'Total CFG paragraphs : {total_cfg}')
print(f'Total facts paragraphs: {total_facts}')
if mismatches:
    print('Programs where CFG count != facts count:')
    for prog, fc, cc in mismatches:
        print(f'  {prog}: facts={fc} cfg={cc}')
else:
    print('All program paragraph counts match between CFG and facts')
"
# CFG and facts counts may legitimately differ (CFG uses preprocessed/expanded
# source, facts uses raw source). Document the diff — do not fail on mismatch.
# FAIL only if total_cfg is 0 or any individual count dropped to 0 unexpectedly.

Write-Host "=== FINAL STATUS ===" -ForegroundColor Green
git status --porcelain | Where-Object { $_ -match "extract_cfg" }
# Expected: M  scripts/extract_cfg_local.py (modified, unstaged — not committed)
# ═══════════════════════════════════════════════════════
# GATED VALIDATION: Stage 5-H Phase 2 referential integrity rules
# Run ALL steps in order. Report PASS/FAIL for each.
# ═══════════════════════════════════════════════════════

Write-Host "=== PRE-FLIGHT: Only validate_canonical_ir.py changed ===" -ForegroundColor Cyan
git diff --name-only HEAD
# Expected: scripts/validate_canonical_ir.py only

Write-Host "=== PRE-FLIGHT: Rule names present in PARAGRAPHS_RULES ===" -ForegroundColor Cyan
Select-String -Path scripts\validate_canonical_ir.py `
  -Pattern "performs_referential_integrity|terminator_enum|falls_through_to_referential_integrity"
# Expected: at least 6 matches total (2 per rule — set entry + failure record)

Write-Host "=== GATE 1-3: Select-String rule name counts ===" -ForegroundColor Cyan
(Select-String -Path scripts\validate_canonical_ir.py `
  -Pattern "performs_referential_integrity").Count
(Select-String -Path scripts\validate_canonical_ir.py `
  -Pattern "terminator_enum").Count
(Select-String -Path scripts\validate_canonical_ir.py `
  -Pattern "falls_through_to_referential_integrity").Count
# Expected: each returns 2 or more

Write-Host "=== GATE 4: Stage 5-H validator full output ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  scripts\validate_canonical_ir.py 2>&1
# Expected: 28/31 PASS, exactly 3 FAIL on programs:
#   CBACT04C  — falls_through_to END-STRING
#   CBSTM03A  — falls_through_to END-STRING
#   CBTRN02C  — falls_through_to END-REWRITE
# Any OTHER program failing = FAIL THIS GATE — report immediately

Write-Host "=== GATE 4b: Confirm ONLY falls_through_to violations ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import json, glob, os
violations = {'performs_referential_integrity': [],
              'terminator_enum': [],
              'falls_through_to_referential_integrity': []}
for path in sorted(glob.glob('validation/canonical-ir/*-validation.json')):
    d = json.load(open(path))
    for f in d.get('failures', []):
        rule = f.get('rule')
        if rule in violations:
            violations[rule].append((d['program'], f.get('details',{})))
for rule, items in violations.items():
    print(f'{rule}: {len(items)} violation(s)')
    for prog, details in items:
        print(f'  {prog}: {details}')
"
# Expected:
#   performs_referential_integrity: 0 violation(s)
#   terminator_enum: 0 violation(s)
#   falls_through_to_referential_integrity: 3 violation(s)
#     CBACT04C: END-STRING
#     CBSTM03A: END-STRING
#     CBTRN02C: END-REWRITE

Write-Host "=== GATE 5: Roundtrip validator ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  scripts\validate_roundtrip.py 2>&1 | Select-Object -Last 4
# Expected: Pass 31, Fail 0

Write-Host "=== GATE 6: Full test suite ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe `
  -m pytest tests/ -q --tb=short 2>&1 | Select-Object -Last 5
# Expected: 136 passed

Write-Host "=== GATE 7: Terminator value audit ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import json, glob, os
VALID = {'implicit','implicit-end-of-program','goto',
         'stop-run','goback','explicit-exit',
         'cics-return','cics-xctl'}
bad = []
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog = os.path.basename(path).replace('.canonical.json','')
    d = json.load(open(path))
    for p in d.get('paragraphs', []):
        t = p.get('terminator')
        if t not in VALID:
            bad.append((prog, p['name'], t))
if bad:
    print('INVALID terminators found:')
    for prog,name,t in bad: print(f'  {prog}.{name}: {repr(t)}')
else:
    print('ALL terminators valid')
"
# Expected: ALL terminators valid

Write-Host "=== GATE 8: Upstream source audit of 3 failing programs ===" -ForegroundColor Cyan
# Inspect extract_fallthrough output for the 3 failing programs
# to confirm END-STRING / END-REWRITE originated in fallthrough data
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import json
for prog in ['CBACT04C', 'CBSTM03A', 'CBTRN02C']:
    d = json.load(open(f'data/fallthrough/{prog}.json'))
    paras = d.get('paragraphs', [])
    bad = [p for p in paras if p.get('falls_through_to','') and
           'END-' in str(p.get('falls_through_to',''))]
    print(f'{prog}: {len(bad)} bad falls_through_to in fallthrough data')
    for p in bad:
        print(f'  {p[\"paragraph\"]} -> {p[\"falls_through_to\"]}')
"
# Expected: confirms END-STRING / END-REWRITE came from fallthrough extractor
# This tells us the fix belongs in extract_fallthrough.py, not the validator
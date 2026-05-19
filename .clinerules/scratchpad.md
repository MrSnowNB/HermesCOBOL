# ═══════════════════════════════════════════════════════
# CobolWalker v0.1 — SCRIPTS_INVENTORY.md Update
# Read the file, show current content, then write the update.
# ═══════════════════════════════════════════════════════

Set-Location C:\work\HermesCOBOL
git pull origin main

Write-Host "=== STEP 1: Show current SCRIPTS_INVENTORY.md ===" -ForegroundColor Cyan
Get-Content C:\work\HermesCOBOL\scripts\SCRIPTS_INVENTORY.md

Write-Host "=== STEP 2: Show current walker-baseline.json summary ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import json
from pathlib import Path
b = json.loads(Path('validation/walker-baseline.json').read_text())
low_live = [(e['program'], e['live_count'], e['full_count']) for e in b if e['live_count'] <= 2]
print('Programs with live_count <= 2:')
for p,l,f in sorted(low_live, key=lambda x: x[1]):
    print(f'  {p}: live={l} total={f}')
"
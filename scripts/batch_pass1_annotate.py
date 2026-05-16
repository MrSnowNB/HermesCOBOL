#!/usr/bin/env python3
"""Batch runner for pass1_annotate.py across all 31 programs."""

import json
import subprocess
from pathlib import Path

RAW_CBL_DIR = Path('data/raw/cbl')
CFG_DIR = Path('data/cfg')
OUT_DIR = Path('validation/pass1')

results = []
errors = []

for src_path in sorted(RAW_CBL_DIR.glob('*.cbl')):
    program_id = src_path.stem.upper()
    cfg_path = CFG_DIR / f'{program_id}.json'
    out_path = OUT_DIR / f'{program_id}_annotations.json'
    
    if not cfg_path.exists():
        errors.append(f'SKIP: {program_id} - CFG not found')
        continue
    
    result = subprocess.run([
        'C:\\Users\\AMD\\AppData\\Local\\Programs\\Python\\Python310\\python.exe',
        'scripts/pass1_annotate.py',
        '--src', str(src_path),
        '--cfg', str(cfg_path),
        '--program-id', program_id,
        '--out', str(out_path)
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        output = json.loads(result.stdout.strip())
        results.append({
            'program_id': program_id,
            'annotations': output['annotations'],
            'cics_branches': output['cics_branches']
        })
        print(f'{program_id}: annotations={output["annotations"]} cics_branches={output["cics_branches"]}')
    else:
        errors.append(f'{program_id}: ERROR - {result.stderr}')
        print(f'{program_id}: ERROR')

print(f'\n--- SUMMARY ---')
print(f'Total processed: {len(results)}')
print(f'Total errors: {len(errors)}')
if errors:
    print(f'Errors:')
    for e in errors:
        print(f'  {e}')
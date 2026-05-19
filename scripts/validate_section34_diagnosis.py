# SCRATCHPAD: validate_section34_diagnosis.py
# Run: python scripts/validate_section34_diagnosis.py
# Purpose: independently confirm the missing paragraph names and their column positions

import json, re
from pathlib import Path

PROGS = ['COACTUPC', 'COACTVWC', 'COCRDLIC']
PARA_HEADER_RE = re.compile(r'^([A-Z0-9][A-Z0-9\-]*)\.[ \t]*$', re.IGNORECASE)

results = {}
for prog in PROGS:
    facts_path     = Path(f'data/facts/{prog}.json')
    canonical_path = Path(f'data/canonical/{prog}.canonical.json')
    cbl_path       = Path(f'data/raw/cbl/{prog}.cbl')

    facts_data = json.loads(facts_path.read_text())
    canonical_data = json.loads(canonical_path.read_text())

    # Extract names from paragraphs_defined (list of dicts with 'name', 'source_line', 'area_a')
    expected = [p['name'] for p in facts_data.get('paragraphs_defined', [])]
    # Extract names from paragraphs (list of dicts with 'name' field)
    actual = [p['name'] for p in canonical_data.get('paragraphs', [])]
    missing = [p for p in expected if p not in actual]

    # Find raw source lines for missing paragraphs
    hits = {}
    raw_lines = cbl_path.read_text(encoding='utf-8', errors='replace').splitlines()
    for i, line in enumerate(raw_lines, start=1):
        if len(line) < 7:
            continue
        code_area = line[7:72] if len(line) >= 8 else ''
        stripped  = code_area.strip()
        m = PARA_HEADER_RE.match(stripped)
        if m and m.group(1).upper() in missing:
            col = len(code_area) - len(code_area.lstrip()) + 8  # 1-based col
            hits[m.group(1).upper()] = {
                'line': i, 'col': col,
                'raw_prefix': repr(line[:20])
            }

    results[prog] = {
        'expected': len(expected),
        'actual'  : len(actual),
        'missing' : missing,
        'source_hits': hits
    }

for prog, r in results.items():
    print(f'\n{prog}: expected={r["expected"]} actual={r["actual"]} delta={r["actual"]-r["expected"]}')
    print(f'  MISSING: {r["missing"]}')
    for name, loc in r["source_hits"].items():
        print(f'  {name}: line {loc["line"]} col {loc["col"]}  raw={loc["raw_prefix"]}')

# Write to scratchpad JSON for audit
Path('/tmp/section34_diagnosis.json').write_text(json.dumps(results, indent=2))
print('\nAudit artifact: /tmp/section34_diagnosis.json')
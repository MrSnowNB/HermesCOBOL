"""
audit_fallthrough.py — Audit the 34 flagged falls_through_to values

Categorizes them into:
- Real noise violations (those in PARAGRAPH_NOISE/RESERVED_WORDS)
- Legitimate paragraph names containing END-
"""
import json
import glob
import os
from cobol_parse_utils import PARAGRAPH_NOISE, RESERVED_WORDS

real_noise = []
legitimate = []

for path in sorted(glob.glob('data/fallthrough/*.json')):
    prog = os.path.basename(path).replace('.json','')
    d = json.load(open(path))
    for p in d.get('paragraphs', []):
        ft = p.get('falls_through_to')
        if ft and 'END-' in ft:
            if ft in PARAGRAPH_NOISE or ft in RESERVED_WORDS:
                real_noise.append((prog, p['paragraph'], ft))
            else:
                legitimate.append((prog, p['paragraph'], ft))

print(f'Real noise violations (in PARAGRAPH_NOISE/RESERVED_WORDS): {len(real_noise)}')
for x in real_noise: print(f'  {x}')

print(f'Legitimate paragraph names containing END-: {len(legitimate)}')
for x in legitimate: print(f'  {x}')
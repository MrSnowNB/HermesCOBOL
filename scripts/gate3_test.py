import sys, glob, os
sys.path.insert(0, '.')

from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict

total = 0
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog_name = os.path.basename(path).replace('.canonical.json','')
    w = CobolWalker(CobolProgramDict(prog_name))
    count = len(list(w.walk(include_dead_code=False)))
    total += count
    print(f'  {prog_name}: {count}')

print(f'TOTAL live: {total}')
print('PASS' if total == 205 else f'FAIL — expected 205 got {total}')
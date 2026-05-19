import sys, glob, os
sys.path.insert(0, '.')

from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict

failures = []
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog_name = os.path.basename(path).replace('.canonical.json','')
    w = CobolWalker(CobolProgramDict(prog_name))
    for flag in [False, True]:
        result = list(w.walk(include_dead_code=flag))
        if len(result) != len(set(result)):
            dupes = [x for x in set(result) if result.count(x) > 1]
            failures.append((prog_name, flag, dupes))

if failures:
    print(f'FAIL — duplicates found: {failures}')
else:
    print('PASS — no duplicates in any walk sequence')
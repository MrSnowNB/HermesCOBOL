import sys, glob, os
sys.path.insert(0, '.')

from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict

failures = []
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog_name = os.path.basename(path).replace('.canonical.json','')
    prog = CobolProgramDict(prog_name)
    w = CobolWalker(prog)
    for flag in [False, True]:
        r1 = list(w.walk(include_dead_code=flag))
        r2 = list(w.walk(include_dead_code=flag))
        r3 = list(w.walk(include_dead_code=flag))
        if not (r1 == r2 == r3):
            failures.append((prog_name, flag))

if failures:
    print(f'FAIL — non-deterministic: {failures}')
else:
    print('PASS — all 31 programs deterministic across 3 successive calls')
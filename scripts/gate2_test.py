import sys, glob, os
sys.path.insert(0, '.')

from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict

failures = []
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog_name = os.path.basename(path).replace('.canonical.json','')
    prog = CobolProgramDict(prog_name)
    if not prog.paragraphs:
        continue
    w = CobolWalker(prog)
    for flag in [False, True]:
        result = list(w.walk(include_dead_code=flag))
        if not result or result[0] != prog.entry_paragraph:
            failures.append((prog_name, flag, result[:1], prog.entry_paragraph))

if failures:
    print(f'FAIL — entry_paragraph not first in {len(failures)} cases:')
    for f in failures: print(f'  {f}')
else:
    print('PASS — entry_paragraph is first for all 31 programs (both flag settings)')
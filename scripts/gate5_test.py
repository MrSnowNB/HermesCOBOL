import sys, glob, os
sys.path.insert(0, '.')

from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict

violations = []
for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog_name = os.path.basename(path).replace('.canonical.json','')
    prog = CobolProgramDict(prog_name)
    w = CobolWalker(prog)
    para_names = set(prog.paragraphs.keys())
    for flag in [False, True]:
        for name in w.walk(include_dead_code=flag):
            if name not in para_names:
                violations.append((prog_name, flag, name))

if violations:
    print(f'FAIL — {len(violations)} dangling names yielded:')
    for v in violations: print(f'  {v}')
else:
    print('PASS — all yielded names exist in CobolProgramDict.paragraphs')
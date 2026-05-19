import sys, glob, os
sys.path.insert(0, '.')

from scripts.cobol_walker import CobolWalker
from scripts.cobol_program_dict import CobolProgramDict

cics_failures = []
dead_failures = []

for path in sorted(glob.glob('data/canonical/*.canonical.json')):
    prog_name = os.path.basename(path).replace('.canonical.json','')
    prog = CobolProgramDict(prog_name)
    w = CobolWalker(prog)
    live = list(w.walk(include_dead_code=False))
    full = list(w.walk(include_dead_code=True))
    live_set = set(live)

    if prog.is_cics:
        if len(full) != len(prog.paragraphs):
            cics_failures.append((prog_name, len(full), len(prog.paragraphs)))

    dead = prog.dead_code_paragraphs
    if dead:
        print(f'  Dead-code program: {prog_name} dead={dead}')
        for dp in dead:
            if dp in live:
                dead_failures.append((prog_name, 'dead in live walk', dp))
            if dp not in full:
                dead_failures.append((prog_name, 'dead missing from full walk', dp))
        dead_tail = [x for x in full if x not in live_set]
        if dead_tail != dead:
            dead_failures.append((prog_name, f'source order wrong tail={dead_tail} expected={dead}'))

if cics_failures:
    print(f'FAIL CICS: {cics_failures}')
elif dead_failures:
    print(f'FAIL dead-code: {dead_failures}')
else:
    print('PASS — CICS counts correct, dead code handled correctly')
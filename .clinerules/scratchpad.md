# ═══════════════════════════════════════════════════════
# FULL COVERAGE AUDIT — Pre-CobolProgramDict
# Verifies extraction completeness across all 4 extractors
# ═══════════════════════════════════════════════════════

Write-Host "=== AUDIT 1: Facts vs Raw Source — paragraph count match ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import json, glob, os, re

RAW_DIR = 'app/src/main/cobol'
FACTS_DIR = 'data/facts'

# Count paragraphs directly from raw source using same logic as cobol_parse_utils
RE_PARA = re.compile(r'^\s{0,3}([A-Z0-9][A-Z0-9\-]*)\.[ \t]*$', re.IGNORECASE)
NOISE = {'EXIT','STOP','GOBACK','END-IF','END-EXEC','END-PERFORM','END-EVALUATE',
         'END-READ','END-WRITE','END-REWRITE','END-CALL','END-STRING','FILLER',
         'EVALUATE','PERFORM','MOVE','IF','ELSE','CONTINUE','SECTION','DIVISION',
         'WHEN','END-WHEN','END-SEARCH','END-COMPUTE','END-MULTIPLY','END-DIVIDE',
         'END-ADD','END-SUBTRACT','END-UNSTRING','END-XML','END-JSON','END-ACCEPT',
         'END-DISPLAY','END-DELETE','END-START','END-RETURN','END-RECEIVE'}

mismatches = []
for facts_path in sorted(glob.glob(f'{FACTS_DIR}/*.json')):
    prog = os.path.basename(facts_path).replace('.json','')
    facts = json.load(open(facts_path))
    facts_count = len(facts.get('paragraphs', []))

    # Find raw source
    raw_path = f'{RAW_DIR}/{prog}.cbl'
    if not os.path.exists(raw_path):
        raw_path = f'{RAW_DIR}/{prog}.CBL'
    if not os.path.exists(raw_path):
        continue

    text = open(raw_path, errors='replace').read()
    in_proc = False
    raw_paras = []
    for line in text.splitlines():
        if 'PROCEDURE DIVISION' in line.upper():
            in_proc = True
            continue
        if not in_proc:
            continue
        m = RE_PARA.match(line)
        if m:
            name = m.group(1).upper()
            if name not in NOISE and name not in raw_paras:
                raw_paras.append(name)

    if facts_count != len(raw_paras):
        mismatches.append((prog, facts_count, len(raw_paras)))

if mismatches:
    print(f'MISMATCHES ({len(mismatches)} programs):')
    for prog, fc, rc in mismatches:
        print(f'  {prog}: facts={fc} raw_scan={rc}')
else:
    print('PASS — facts paragraph counts match raw source scan for all programs')
"

Write-Host "=== AUDIT 2: CFG coverage — performs/goto extraction completeness ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import json, glob, os
total = 0
with_performs = 0
with_gotos = 0
empty_both = 0
for path in sorted(glob.glob('data/cfg/*.json')):
    prog = os.path.basename(path).replace('.json','')
    d = json.load(open(path))
    for p in d.get('paragraphs', []):
        total += 1
        has_p = bool(p.get('performs'))
        has_g = bool(p.get('goto_targets'))
        if has_p: with_performs += 1
        if has_g: with_gotos += 1
        if not has_p and not has_g: empty_both += 1
print(f'Total CFG paragraphs : {total}')
print(f'Has performs[]       : {with_performs} ({100*with_performs//total}%)')
print(f'Has goto_targets[]   : {with_gotos} ({100*with_gotos//total}%)')
print(f'Empty both (leaf para): {empty_both} ({100*empty_both//total}%)')
"

Write-Host "=== AUDIT 3: Fallthrough coverage — terminator classification ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import json, glob, os
from collections import Counter
terminator_counts = Counter()
null_terminator = []
for path in sorted(glob.glob('data/fallthrough/*.json')):
    prog = os.path.basename(path).replace('.json','')
    d = json.load(open(path))
    for p in d.get('paragraphs', []):
        t = p.get('terminator')
        terminator_counts[t] += 1
        if t is None:
            null_terminator.append((prog, p.get('paragraph')))
print('Terminator distribution across corpus:')
for t, count in sorted(terminator_counts.items(), key=lambda x: -x[1]):
    print(f'  {str(t):<30} {count}')
if null_terminator:
    print(f'NULL terminators ({len(null_terminator)}):')
    for prog, para in null_terminator:
        print(f'  {prog}.{para}')
else:
    print('No null terminators — CLEAN')
"

Write-Host "=== AUDIT 4: Pass1 annotations coverage ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import json, glob, os
total_stmts = 0
unresolved = 0
unreachable = 0
no_verb = 0
programs_with_annotations = 0
programs_without = []
for path in sorted(glob.glob('data/facts/*.json')):
    prog = os.path.basename(path).replace('.json','')
    ann_path = f'validation/pass1/{prog}_annotations.json'
    if not os.path.exists(ann_path):
        programs_without.append(prog)
        continue
    anns = json.load(open(ann_path))
    if not anns:
        programs_without.append(prog)
        continue
    programs_with_annotations += 1
    for a in anns:
        total_stmts += 1
        if a.get('operand_unresolved'): unresolved += 1
        if not a.get('cfg_reachable', True): unreachable += 1
        if not a.get('verb'): no_verb += 1
print(f'Programs with pass1 annotations : {programs_with_annotations}')
print(f'Programs WITHOUT annotations    : {len(programs_without)}')
if programs_without:
    for p in programs_without: print(f'  {p}')
print(f'Total annotated statements      : {total_stmts}')
print(f'  operand_unresolved            : {unresolved}')
print(f'  cfg_reachable=False           : {unreachable}')
print(f'  missing verb                  : {no_verb}')
"

Write-Host "=== AUDIT 5: External calls — cross-reference check ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import json, glob, os
all_programs = set()
for path in glob.glob('data/facts/*.json'):
    all_programs.add(os.path.basename(path).replace('.json',''))

internal_calls = 0
external_calls = 0
unknown_calls = []
for path in sorted(glob.glob('data/facts/*.json')):
    prog = os.path.basename(path).replace('.json','')
    d = json.load(open(path))
    for call in d.get('external_calls', []):
        if call in all_programs:
            internal_calls += 1
        else:
            external_calls += 1
            unknown_calls.append((prog, call))
print(f'Calls to known programs (internal): {internal_calls}')
print(f'Calls to unknown targets (external): {external_calls}')
print('External call targets:')
for prog, call in sorted(set(unknown_calls)):
    print(f'  {prog} -> {call}')
"

Write-Host "=== AUDIT 6: Copybook cross-reference ===" -ForegroundColor Cyan
C:\Users\AMD\AppData\Local\Programs\Python\Python310\python.exe -c "
import json, glob, os
CPY_DIR = 'app/src/main/cobol/copy'
available_cpys = set()
if os.path.exists(CPY_DIR):
    available_cpys = {f.stem.upper() for f in __import__('pathlib').Path(CPY_DIR).glob('*.cpy')}
    available_cpys |= {f.stem.upper() for f in __import__('pathlib').Path(CPY_DIR).glob('*.CPY')}

referenced = {}
for path in sorted(glob.glob('data/facts/*.json')):
    prog = os.path.basename(path).replace('.json','')
    d = json.load(open(path))
    for cpy in d.get('copybooks_referenced', []):
        referenced.setdefault(cpy, []).append(prog)

resolved = [c for c in referenced if c in available_cpys]
unresolved = [c for c in referenced if c not in available_cpys]
print(f'Copybooks referenced total : {len(referenced)}')
print(f'  Resolved (file exists)   : {len(resolved)}')
print(f'  Unresolved (missing file): {len(unresolved)}')
if unresolved:
    for cpy in 
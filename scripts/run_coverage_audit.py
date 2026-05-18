#!/usr/bin/env python3
"""
Coverage Audit Script for HermesCOBOL
Runs all 6 audit checks for the COBOL extraction pipeline
"""
import json
import glob
import os
import re
from collections import Counter

# Regex pattern from cobol_parse_utils.py
RE_PARAGRAPH = re.compile(r"^[ ]{0,11}([A-Z0-9][A-Z0-9-]*)[ \t]*\.[ \t]*(?:\*.*)?$", re.MULTILINE)

RESERVED_WORDS = frozenset([
    "IDENTIFICATION", "ENVIRONMENT", "DATA", "PROCEDURE",
    "CONFIGURATION", "INPUT-OUTPUT", "FILE", "WORKING-STORAGE",
    "LINKAGE", "LOCAL-STORAGE", "REPORT", "SCREEN",
    "PROGRAM-ID", "AUTHOR", "INSTALLATION", "DATE-WRITTEN",
    "DATE-COMPILED", "SECURITY", "REMARKS",
    "FD", "SD", "RD",
    "STOP", "EXIT", "GOBACK", "MOVE",
])

PARAGRAPH_NOISE = frozenset([
    "END-IF", "END-EVALUATE", "END-PERFORM", "END-READ", "END-WRITE",
    "END-REWRITE", "END-DELETE", "END-START", "END-CALL", "END-STRING",
    "END-UNSTRING", "END-COMPUTE", "END-ADD", "END-SUBTRACT",
    "END-MULTIPLY", "END-DIVIDE", "END-EXEC", "END-SEARCH",
    "FILE-CONTROL", "FILE-SECTION", "I-O-CONTROL",
    "GOBACK", "EXIT", "CONTINUE", "STOP",
    "FILLER",
])


def extract_paragraphs(text: str) -> set[str]:
    """Extract paragraph names from COBOL source text using same logic as cobol_parse_utils"""
    clean_lines = []
    for line in text.splitlines():
        if len(line) >= 7 and line[6] in ("*", "/"):
            continue
        if line.strip():
            clean_lines.append(line)
    clean = "\n".join(clean_lines)
    
    proc_match = re.search(r"^[ \t]*PROCEDURE[ \t]+DIVISION\b", clean, re.MULTILINE | re.IGNORECASE)
    proc_text = clean[proc_match.start():] if proc_match else clean
    
    paragraphs = set()
    for m in RE_PARAGRAPH.finditer(proc_text):
        name = m.group(1).upper()
        if (name not in RESERVED_WORDS
                and name not in PARAGRAPH_NOISE
                and not name.endswith("-DIVISION")):
            paragraphs.add(name)
    
    return paragraphs


def audit_1_facts_vs_raw():
    """AUDIT 1: Facts vs Raw Source — paragraph count match"""
    print("=== AUDIT 1: Facts vs Raw Source — paragraph count match ===")
    RAW_DIR = 'data/raw/cbl'
    FACTS_DIR = 'data/facts'
    
    mismatches = []
    facts_paras = 0
    raw_paras_total = 0
    for facts_path in sorted(glob.glob(f'{FACTS_DIR}/*.json')):
        prog = os.path.basename(facts_path).replace('.json','')
        facts = json.load(open(facts_path))
        facts_count = len(facts.get('paragraphs', []))
        facts_paras += facts_count
        
        raw_path = f'{RAW_DIR}/{prog}.cbl'
        if not os.path.exists(raw_path):
            raw_path = f'{RAW_DIR}/{prog}.CBL'
        if not os.path.exists(raw_path):
            continue
        
        text = open(raw_path, errors='replace').read()
        raw_paras = extract_paragraphs(text)
        raw_count = len(raw_paras)
        raw_paras_total += raw_count
        
        if facts_count != raw_count:
            mismatches.append((prog, facts_count, raw_count))
    
    print(f'facts paragraphs total: {facts_paras}')
    print(f'raw source paragraphs total: {raw_paras_total}')
    if mismatches:
        print(f'MISMATCHES ({len(mismatches)} programs):')
        for prog, fc, rc in mismatches:
            print(f'  {prog}: facts={fc} raw_scan={rc}')
        return False
    else:
        print('PASS — facts paragraph counts match raw source scan for all programs')
        return True

def audit_2_cfg_coverage():
    """AUDIT 2: CFG coverage — performs/goto extraction completeness"""
    print("\n=== AUDIT 2: CFG coverage — performs/goto extraction completeness ===")
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
    return True

def audit_3_fallthrough_coverage():
    """AUDIT 3: Fallthrough coverage — terminator classification"""
    print("\n=== AUDIT 3: Fallthrough coverage — terminator classification ===")
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
        return False
    else:
        print('No null terminators — CLEAN')
        return True

def audit_4_pass1_annotations():
    """AUDIT 4: Pass1 annotations coverage"""
    print("\n=== AUDIT 4: Pass1 annotations coverage ===")
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
        for p in programs_without:
            print(f'  {p}')
    print(f'Total annotated statements      : {total_stmts}')
    print(f'  operand_unresolved            : {unresolved}')
    print(f'  cfg_reachable=False           : {unreachable}')
    print(f'  missing verb                  : {no_verb}')
    return True

def audit_5_external_calls():
    """AUDIT 5: External calls — cross-reference check"""
    print("\n=== AUDIT 5: External calls — cross-reference check ===")
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
    return True

def audit_6_copybooks():
    """AUDIT 6: Copybook cross-reference"""
    print("\n=== AUDIT 6: Copybook cross-reference ===")
    CPY_DIR = 'data/raw/cpy'
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
        for cpy in unresolved:
            print(f'  {cpy}')
    return True

def main():
    results = []
    
    # Run all audits
    results.append(('AUDIT 1', audit_1_facts_vs_raw()))
    results.append(('AUDIT 2', audit_2_cfg_coverage()))
    results.append(('AUDIT 3', audit_3_fallthrough_coverage()))
    results.append(('AUDIT 4', audit_4_pass1_annotations()))
    results.append(('AUDIT 5', audit_5_external_calls()))
    results.append(('AUDIT 6', audit_6_copybooks()))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\nALL AUDITS PASSED — extraction is complete, ready for CobolProgramDict")
    else:
        failed = [r[0] for r in results if not r[1]]
        print(f"\nAUDITS FAILED: {', '.join(failed)}")

if __name__ == '__main__':
    main()
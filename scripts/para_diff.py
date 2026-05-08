#!/usr/bin/env python3
"""
para_diff.py  --  diagnostic: show paragraph name delta between local extractor
and facts file for one program.

Usage:
    python scripts/para_diff.py CBACT01C
    python scripts/para_diff.py CBACT01C --all
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from data_flow import _normalise_source, extract_paragraphs

CBL_DIR   = Path('data/raw/cbl')
FACTS_DIR = Path('data/facts')


def diff_program(program_name: str):
    program_name = program_name.upper()
    cbl_path   = CBL_DIR   / f"{program_name}.cbl"
    facts_path = FACTS_DIR / f"{program_name}.json"

    if not cbl_path.exists():
        # try upper extension
        cbl_path = CBL_DIR / f"{program_name}.CBL"
    if not cbl_path.exists():
        print(f"[{program_name}] ERROR: .cbl not found in {CBL_DIR}")
        return

    raw   = cbl_path.read_text(encoding='utf-8', errors='replace')
    lines = _normalise_source(raw)
    paras = extract_paragraphs(lines)
    local_set = sorted(k for k in paras if k != '__MAIN__')

    facts_set = []
    if facts_path.exists():
        with open(facts_path, encoding='utf-8') as fh:
            facts = json.load(fh)
        raw_val = facts.get('paragraphs_defined', [])
        if isinstance(raw_val, list):
            facts_set = sorted(v.upper() for v in raw_val)
        elif isinstance(raw_val, int):
            facts_set = [f'<count only: {raw_val}>']
    else:
        facts_set = ['<no facts file>']

    local_only = sorted(set(local_set) - set(facts_set))
    facts_only = sorted(set(facts_set) - set(local_set))

    print(f"\n{'='*60}")
    print(f"  {program_name}")
    print(f"  local={len(local_set)}  facts={len(facts_set)}")
    print(f"{'='*60}")
    print(f"  local_only (+{len(local_only)}):")
    for n in local_only:
        print(f"    + {n}")
    print(f"  facts_only (-{len(facts_only)}):")
    for n in facts_only:
        print(f"    - {n}")
    if not local_only and not facts_only:
        print("  (no delta)")


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = [a for a in sys.argv[1:] if a.startswith('--')]
    if not args:
        print("Usage: python scripts/para_diff.py <PROGRAM> [--all]")
        sys.exit(1)
    if '--all' in flags:
        for cbl in sorted(CBL_DIR.glob('*.cbl')) + sorted(CBL_DIR.glob('*.CBL')):
            diff_program(cbl.stem)
    else:
        diff_program(args[0])

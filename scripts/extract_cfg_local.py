#!/usr/bin/env python3
"""
extract_cfg_local.py

A pure-Python local replacement for Phase 0 (smojol/Cobol-REKT).
Uses 'cobc -E' to expand copybooks and performs regex-based static analysis
to produce data/cfg/<PROG>.json files.

This unblocks Windows dev environments without Java/Smojol dependencies.

Stage 5-B (CFG wiring) — promoted with minimal path adaptation for HermesCOBOL.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from config import RAW_CBL_DIR, RAW_CPY_DIR, RAW_CPY_BMS_DIR, CFG_DIR
from cobol_parse_utils import (
    extract_paragraphs as _extract_paragraphs_authoritative,
    PARAGRAPH_NOISE,
    RESERVED_WORDS,
)


def git_blob_sha(path: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "hash-object", str(path)], cwd=path.parent, stderr=subprocess.DEVNULL
        )
        return out.decode().strip()
    except Exception:
        return hashlib.sha1(path.read_bytes()).hexdigest()


def extract_program_id(text: str, fallback: str) -> str:
    m = re.search(r"PROGRAM-ID\.\s*([A-Za-z0-9\-_]+)", text, re.IGNORECASE)
    if not m:
        return fallback.upper()
    return m.group(1).upper()


def preprocess(src_path: Path) -> str:
    """Uses cobc -E to get expanded source (with HermesCOBOL copybook includes)."""
    try:
        proc = subprocess.run(
            ["cobc", "-E", "-I", str(RAW_CPY_DIR), "-I", str(RAW_CPY_BMS_DIR), str(src_path)],
            capture_output=True,
            text=True,
            check=True
        )
        return proc.stdout
    except Exception as e:
        print(f"Warning: cobc -E failed, using raw source: {e}", file=sys.stderr)
        return src_path.read_text(errors="replace")


def clean_preprocessed(text: str) -> str:
    """Removes #line markers and handles whitespace."""
    lines = []
    for line in text.splitlines():
        if line.startswith("#"):
            continue
        lines.append(line)
    return "\n".join(lines)


def _extract_paragraphs_ordered(text: str) -> list[str]:
    """
    Return paragraph names in source encounter order.

    Uses the authoritative filter (full PARAGRAPH_NOISE + RESERVED_WORDS +
    section handling + RE_PARAGRAPH) from cobol_parse_utils for correctness,
    while preserving the linear source order required by the CFG + reachability
    logic in this module.
    """
    good_names: set[str] = _extract_paragraphs_authoritative(text)
    paragraphs: list[str] = []
    in_proc = False
    for line in text.splitlines():
        u = line.upper()
        if "PROCEDURE DIVISION" in u:
            in_proc = True
            continue
        if not in_proc:
            continue
        m = re.match(r"^\s{0,3}([A-Z0-9][A-Z0-9\-]*)\.\s*$", line, re.IGNORECASE)
        if m:
            name = m.group(1).upper()
            if name in good_names and name not in paragraphs:
                paragraphs.append(name)
    return paragraphs


def analyze_flow(text: str, paragraphs: list[str]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    performs = {p: [] for p in paragraphs}
    gotos = {p: [] for p in paragraphs}
    
    current_para = None
    in_proc = False
    
    perf_re = re.compile(r"\bPERFORM\s+([A-Z0-9][A-Z0-9\-]+)", re.IGNORECASE)
    goto_re = re.compile(r"\bGO\s+TO\s+([A-Z0-9][A-Z0-9\-]+)", re.IGNORECASE)
    
    for line in text.splitlines():
        u = line.upper()
        if "PROCEDURE DIVISION" in u:
            in_proc = True
            if not current_para and paragraphs:
                current_para = paragraphs[0]
            continue
        if not in_proc:
            continue
            
        m = re.match(r"^\s{0,3}([A-Z0-9][A-Z0-9\-]*)\.\s*$", line, re.IGNORECASE)
        if m:
            name = m.group(1).upper()
            if name not in PARAGRAPH_NOISE and name not in RESERVED_WORDS:
                current_para = name
            continue
            
        if not current_para:
            continue
            
        for target in perf_re.findall(line):
            t = target.upper()
            if t in paragraphs and t not in performs[current_para]:
                performs[current_para].append(t)
        
        for target in goto_re.findall(line):
            t = target.upper()
            if t in paragraphs and t not in gotos[current_para]:
                gotos[current_para].append(t)
                
    return performs, gotos


def extract_data_items(text: str) -> list[dict]:
    items = []
    in_data = False
    item_re = re.compile(r"^\s+(0[1-9]|[1-4][0-9]|77|88)\s+([A-Z0-9][A-Z0-9\-]+)", re.IGNORECASE)
    redef_re = re.compile(r"\bREDEFINES\s+([A-Z0-9][A-Z0-9\-]+)", re.IGNORECASE)
    pic_re = re.compile(r"\bPIC(?:TURE)?\s+(?:IS\s+)?(\S+)", re.IGNORECASE)
    
    for line in text.splitlines():
        u = line.upper()
        if "DATA DIVISION" in u:
            in_data = True
            continue
        if "PROCEDURE DIVISION" in u:
            in_data = False
            continue
        if not in_data:
            continue
            
        m = item_re.match(line)
        if m:
            level = int(m.group(1))
            name = m.group(2).upper()
            if name == "FILLER": continue
            
            redef = redef_re.search(line)
            pic = pic_re.search(line)
            
            items.append({
                "name": name,
                "level": level,
                "picture": pic.group(1).rstrip(".") if pic else None,
                "redefines": redef.group(1).upper() if redef else None,
                "reachable": True
            })
    return items


def run_single(source_path: Path, output_path: Path = None):
    """Run CFG extraction for a single program."""
    if output_path is None:
        output_path = CFG_DIR / f"{source_path.stem.upper()}.json"

    raw_source = source_path.read_text(errors="replace")
    expanded_source = clean_preprocessed(preprocess(source_path))
    
    program_id = extract_program_id(raw_source, source_path.stem)
    source_sha = git_blob_sha(source_path)
    
    paras = _extract_paragraphs_ordered(expanded_source)
    performs, gotos = analyze_flow(expanded_source, paras)
    data_items = extract_data_items(expanded_source)
    
    reachable = set()
    if paras:
        worklist = [paras[0]]
        while worklist:
            curr = worklist.pop()
            if curr not in reachable:
                reachable.add(curr)
                worklist.extend(performs.get(curr, []))
                worklist.extend(gotos.get(curr, []))
    
    paragraph_records = []
    for p in paras:
        paragraph_records.append({
            "name": p,
            "reachable": p in reachable,
            "performs": performs.get(p, []),
            "goto_targets": gotos.get(p, []),
            "goto_flag": len(gotos.get(p, [])) > 0
        })
        
    cfg_out = {
        "program_id": program_id,
        "source_file": str(source_path).replace("\\", "/"),
        "source_sha": source_sha,
        "cfg_tool": "HermesCOBOL extract_cfg_local.py (Stage 5-B)",
        "paragraphs": paragraph_records,
        "data_items": data_items,
        "redefines_clauses": [d for d in data_items if d["redefines"]],
        "copybooks_used": sorted(list(set(re.findall(r"\bCOPY\s+([A-Z0-9][A-Z0-9\-]+)", raw_source, re.IGNORECASE)))),
        "calls_to": sorted(list(set(re.findall(r"\bCALL\s+['\"]([^'\"]+)['\"]", expanded_source, re.IGNORECASE)))),
        "cics_commands": sorted(list(set(re.findall(r"EXEC\s+CICS\s+([A-Z][A-Z0-9\-]*)", expanded_source, re.IGNORECASE)))),
        "dead_code_paragraphs": [p for p in paras if p not in reachable],
        "dead_code_items": [],
        "irreducible_gotos": [],
        "smojol_cfg_path": None,
        "smojol_node_count": 0
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(cfg_out, indent=2))
    print(f"[ok] {source_path.stem.upper()}  paragraphs={len(paras)}  data_items={len(data_items)}")


def run_all():
    """Process all programs in RAW_CBL_DIR (Stage 5-B corpus mode)."""
    CFG_DIR.mkdir(parents=True, exist_ok=True)
    seen = set()
    unique = []
    for f in sorted(RAW_CBL_DIR.glob('*.cbl')) + sorted(RAW_CBL_DIR.glob('*.CBL')):
        stem_upper = f.stem.upper()
        if stem_upper not in seen:
            seen.add(stem_upper)
            unique.append(f)

    print(f"[corpus] processing {len(unique)} programs for CFG...", file=sys.stderr)
    for cbl_path in unique:
        try:
            out_path = CFG_DIR / f"{cbl_path.stem.upper()}.json"
            run_single(cbl_path, out_path)
        except Exception as exc:
            print(f"[{cbl_path.stem.upper()}] ERROR: {exc}", file=sys.stderr)

    print(f"[ok] {len(unique)}/31 complete — wrote to {CFG_DIR}/", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="Local CFG extractor (Stage 5-B)")
    ap.add_argument("--source", type=Path, help="Path to single .cbl file")
    ap.add_argument("--output", type=Path, help="Output JSON path (single mode)")
    ap.add_argument("--all", action="store_true", help="Process entire corpus (requires no --source)")
    args = ap.parse_args()

    if args.all:
        if args.source or args.output:
            ap.error("--all is mutually exclusive with --source/--output")
        run_all()
        return

    if not args.source:
        ap.error("--source is required (or use --all)")

    source_path = args.source
    if args.output:
        output_path = args.output
    else:
        output_path = CFG_DIR / f"{source_path.stem.upper()}.json"

    run_single(source_path, output_path)


if __name__ == "__main__":
    main()

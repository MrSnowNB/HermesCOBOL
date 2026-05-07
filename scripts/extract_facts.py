#!/usr/bin/env python3
"""
extract_facts.py  — COBOL -> structured_facts.json  (Stage 3)

Prerequisites (run manually before this script):
  Stage 1: cobc -E  (see docs/manual-runbook.md)
  Stage 2: COBOL-REKT smojol-cli  (see docs/manual-runbook.md)

Reads:
  data/raw/cbl/<PROG>.cbl          raw source
  data/raw/cpy/                    copybooks (for cobc -E inline expansion)
  data/rekt/<PROG>.cbl.report/**   REKT CFG JSON (from Stage 2)

Writes:
  data/facts/<PROG>.json           structured_facts.json per program

Usage:
  python scripts/extract_facts.py             # all programs in data/raw/cbl/
  python scripts/extract_facts.py CBACT01C    # single program
"""

import re, json, subprocess, sys
from pathlib import Path
from scripts.config import (
    SRC_DIR, CPY_DIR, REKT_DIR, FACTS_DIR,
    MAX_REKT_SENTENCES, MAX_01_ITEMS
)
from scripts.schema import validate

FACTS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Stage 1 inline: cobc -E copybook expansion
# ---------------------------------------------------------------------------
def cobc_expand(prog: str) -> list:
    """Run cobc -E to inline copybooks. Falls back to raw source if cobc not found."""
    src = SRC_DIR / f"{prog}.cbl"
    if not src.exists():
        src = SRC_DIR / f"{prog}.CBL"
    if not src.exists():
        raise FileNotFoundError(f"No source file for {prog} in {SRC_DIR}")
    try:
        r = subprocess.run(
            ["cobc", "-E", "-I", str(CPY_DIR), str(src)],
            capture_output=True, text=True, timeout=60
        )
        lines = r.stdout.splitlines()
    except FileNotFoundError:
        # cobc not on PATH — fall back to raw source (REKT still works)
        print(f"  [{prog}] WARNING: cobc not found, using raw source (copybooks not expanded)")
        lines = src.read_text(encoding="utf-8", errors="replace").splitlines()
    return [l for l in lines if not l.startswith("#")]

# ---------------------------------------------------------------------------
# Stage 2 consumer: REKT CFG JSON loading
# ---------------------------------------------------------------------------
def rekt_load(prog: str) -> dict:
    """Load REKT CFG JSON. Handles flat, double-nested, and uppercase path variants."""
    # 1. Standard flat path
    p = REKT_DIR / f"{prog}.cbl.report/cfg/cfg-{prog}.cbl.json"
    # 2. Double-nested path (most common on Windows/REKT default)
    if not p.exists():
        p = REKT_DIR / f"{prog}.cbl.report/{prog}.cbl.report/cfg/cfg-{prog}.cbl.json"
    # 3. Uppercase .CBL variants
    if not p.exists():
        p = REKT_DIR / f"{prog}.cbl.report/{prog}.CBL.report/cfg/cfg-{prog}.Cbl.json"
    if not p.exists():
        p = REKT_DIR / f"{prog}.cbl.report/{prog}.CBL.report/cfg/cfg-{prog}.cbl.json"
    # 4. Recursive glob fallback
    if not p.exists():
        matches = list(REKT_DIR.glob(f"**/{prog}.*.report/**/cfg-{prog}.*.json"))
        if matches:
            p = matches[0]
    if not p.exists() or not p.is_file():
        return {"nodes": [], "edges": [], "rekt_available": False}
    raw = json.loads(p.read_text(encoding="utf-8"))
    raw["rekt_available"] = True
    return raw

def rekt_sentences(rekt: dict) -> list:
    return [
        {"id": n["id"], "type": n.get("type", ""), "text": n.get("originalText", "").strip()}
        for n in rekt.get("nodes", [])
        if n.get("nodeType") == "CODE_VERTEX" and n.get("originalText", "").strip()
    ]

def rekt_calls(sentences: list) -> list:
    calls = []
    for s in sentences:
        m = re.search(r"\bCALL\s+['\"]([A-Z0-9]+)['\"]", s["text"], re.IGNORECASE)
        if m:
            calls.append(m.group(1))
    return list(dict.fromkeys(calls))

def rekt_cics(sentences: list) -> list:
    hits = []
    for s in sentences:
        m = re.match(r"EXEC\s+CICS\s+(\w+)", s["text"].upper())
        if m:
            hits.append({"verb": m.group(1), "text": s["text"][:120]})
    return hits

# ---------------------------------------------------------------------------
# Stage 3: Paragraph extraction (from cobc -E expanded source)
# ---------------------------------------------------------------------------
PARA_RE = re.compile(r'^[ ]{0,7}([A-Z0-9][A-Z0-9\-]{2,})\.\s*$')
PERF_RE = re.compile(r'\bPERFORM\s+([A-Z0-9][A-Z0-9\-]+)(?:\s+THRU\s+([A-Z0-9][A-Z0-9\-]+))?')
GOTO_RE = re.compile(r'\bGO\s+TO\s+((?:[A-Z0-9][A-Z0-9\-]+\s*)+?)(?:\s+DEPENDING|\.)', re.IGNORECASE)
TERM_RE = re.compile(r'\b(STOP\s+RUN|GOBACK|EXIT\s+PROGRAM)\b', re.IGNORECASE)
CICS_RETURN_RE = re.compile(r'EXEC\s+CICS\s+RETURN', re.IGNORECASE)

PARA_EXCLUDE = frozenset([
    "SECTION", "DIVISION", "PROGRAM", "AUTHOR", "DATE", "REMARKS",
    "ENVIRONMENT", "CONFIGURATION", "INPUT", "OUTPUT", "FILE",
    "WORKING", "LINKAGE", "LOCAL", "SCREEN", "REPORT",
])

def para_extract(lines: list) -> list:
    paragraphs = []
    in_procedure = False
    current = None
    for i, raw in enumerate(lines):
        upper = raw.strip().upper()
        if "PROCEDURE DIVISION" in upper:
            in_procedure = True
            continue
        if not in_procedure:
            continue
        m = PARA_RE.match(raw)
        if m:
            name = m.group(1).upper()
            if name not in PARA_EXCLUDE:
                if current:
                    paragraphs.append(current)
                current = {"name": name, "line_start": i + 1,
                           "performs": [], "gotos": [], "terminator": "implicit"}
                continue
        if current is None:
            continue
        for pm in PERF_RE.finditer(upper):
            tgt = pm.group(1)
            if tgt not in ("UNTIL", "VARYING", "TIMES", "WITH", "TEST", "THRU"):
                entry = {"target": tgt}
                if pm.group(2):
                    entry["thru"] = pm.group(2)
                if entry not in current["performs"]:
                    current["performs"].append(entry)
        for gm in GOTO_RE.finditer(upper):
            for tgt in gm.group(1).split():
                tgt = tgt.strip()
                if tgt and tgt not in current["gotos"]:
                    current["gotos"].append(tgt)
        if TERM_RE.search(upper):
            current["terminator"] = TERM_RE.search(upper).group(0).upper().replace("  ", " ")
        if CICS_RETURN_RE.search(upper):
            current["terminator"] = "EXEC CICS RETURN"
    if current:
        paragraphs.append(current)
    for i, p in enumerate(paragraphs):
        p["line_end"] = (paragraphs[i + 1]["line_start"] - 1
                         if i + 1 < len(paragraphs) else len(lines))
    return paragraphs

# ---------------------------------------------------------------------------
# Stage 3: Data division extraction
# ---------------------------------------------------------------------------
DATA_RE   = re.compile(r'^\s+(\d{2})\s+([A-Z0-9][A-Z0-9\-]*)\s*(?:PIC\S*\s+(\S+))?', re.IGNORECASE)
FD_RE     = re.compile(r'^\s+FD\s+([A-Z0-9][A-Z0-9\-]+)', re.IGNORECASE)
SELECT_RE = re.compile(r'SELECT\s+([A-Z0-9][A-Z0-9\-]+)\s+ASSIGN\s+TO\s+(\S+)', re.IGNORECASE)

def data_extract(lines: list) -> dict:
    in_data = False
    items_01, files, selects = [], [], []
    for raw in lines:
        upper = raw.strip().upper()
        if "DATA DIVISION" in upper:
            in_data = True
        if "PROCEDURE DIVISION" in upper:
            in_data = False
        m = SELECT_RE.search(raw)
        if m:
            selects.append({"logical": m.group(1).upper(),
                            "ddname": m.group(2).upper().strip('.')})
        m2 = FD_RE.match(raw)
        if m2:
            files.append(m2.group(1).upper())
        if in_data:
            m3 = DATA_RE.match(raw)
            if m3 and m3.group(1) == "01" and m3.group(2).upper() not in ("FILLER",):
                items_01.append({"name": m3.group(2).upper(), "pic": m3.group(3)})
    return {"select_files": selects, "fd_names": files,
            "working_storage_01s": items_01[:MAX_01_ITEMS]}

# ---------------------------------------------------------------------------
# Assemble and write facts JSON
# ---------------------------------------------------------------------------
def assemble(prog: str) -> dict:
    print(f"  [{prog}] expanding source...", end="", flush=True)
    lines     = cobc_expand(prog)
    print(f" {len(lines)} lines | loading REKT...", end="", flush=True)
    rekt      = rekt_load(prog)
    sentences = rekt_sentences(rekt)
    print(f" {len(sentences)} sentences | extracting...", end="", flush=True)
    paras     = para_extract(lines)
    data      = data_extract(lines)

    facts = {
        "program":              prog,
        "source_lines":         len(lines),
        "rekt_available":       rekt["rekt_available"],
        "rekt_node_count":      len(rekt.get("nodes", [])),
        "rekt_edge_count":      len(rekt.get("edges", [])),
        "paragraphs":           paras,
        "para_count":           len(paras),
        "data":                 data,
        "external_calls":       rekt_calls(sentences),
        "cics_verbs":           rekt_cics(sentences),
        "rekt_sentences":       sentences[:MAX_REKT_SENTENCES],
        "rekt_sentence_total":  len(sentences),
    }

    # Validate against schema before writing
    errs = validate(facts)
    if errs:
        print(f" SCHEMA ERRORS: {errs}")
    else:
        print(f" {len(paras)} paras | valid")

    out = FACTS_DIR / f"{prog}.json"
    out.write_text(json.dumps(facts, indent=2))
    print(f"  -> {out}")
    return facts

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    progs = sys.argv[1:] if len(sys.argv) > 1 else [
        p.stem.upper() for p in SRC_DIR.glob("*.[cC][bB][lL]")
    ]
    if not progs:
        print(f"No .cbl files found in {SRC_DIR}")
        print("Place raw COBOL source in data/raw/cbl/ first.")
        sys.exit(1)
    print(f"Extracting facts for {len(progs)} program(s)...")
    ok, fail = 0, 0
    for prog in sorted(progs):
        try:
            assemble(prog.upper())
            ok += 1
        except Exception as e:
            print(f"  [{prog}] ERROR: {e}")
            fail += 1
    print(f"\nDone: {ok} OK, {fail} failed. Output: {FACTS_DIR}")

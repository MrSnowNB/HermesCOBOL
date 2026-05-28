#!/usr/bin/env python3
"""
load_corpus.py — Load all CardDemo programs into Honcho.

For each program found in data/byte_layouts/:
  1. Load byte layout (from data/byte_layouts/{PROG}.json)
  2. Load CFG (generate if needed, load under {PROG}/cfg/summary)
  3. Load para IR (from data/canonical/ or docs/ if available)
  4. Load oracle (from docs/ if available)
  5. Write {PROG}/meta entry

Usage:
    python scripts/load_corpus.py --discover        # show what's available
    python scripts/load_corpus.py --run             # load everything
    python scripts/load_corpus.py --program COBIL00C  # load one program
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))
from honcho_loader import HonchoClient, load_layout, load_cfg, meta_key
from honcho_loader import para_key, layout_key, oracle_key, cfg_key

DATA_DIR = Path("data")
DOCS_DIR = Path("docs")
LAYOUTS_DIR = DATA_DIR / "byte_layouts"
SCRIPTS_DIR = Path("scripts")

def discover_programs() -> list[dict]:
    """
    Find all programs and what artifacts exist for each.
    Returns list of program status dicts.
    """
    programs = {}

    # Find all .cob source files
    for src in sorted(DATA_DIR.rglob("*.cob")):
        name = src.stem.upper()
        if name not in programs:
            programs[name] = {"program": name, "source": str(src),
                              "has_layout": False, "has_cfg": False,
                              "has_ir": False, "has_oracle": False}
                              
    for src in sorted(DATA_DIR.rglob("*.cbl")):
        name = src.stem.upper()
        if name not in programs:
             programs[name] = {"program": name, "source": str(src),
                              "has_layout": False, "has_cfg": False,
                              "has_ir": False, "has_oracle": False}

    # Check byte layouts
    if LAYOUTS_DIR.exists():
        for f in LAYOUTS_DIR.glob("*.json"):
            name = f.stem.upper()
            if name in programs:
                programs[name]["has_layout"] = True
                programs[name]["layout_path"] = str(f)

    # Check CFG outputs
    for f in DATA_DIR.rglob("*cfg*.json"):
        name = f.stem.upper().replace("_CFG", "").replace("-CFG", "")
        if name in programs:
            programs[name]["has_cfg"] = True
            programs[name]["cfg_path"] = str(f)

    # Check oracle docs
    for f in DOCS_DIR.glob("*Oracle*.json"):
        # e.g. COACTUPC_Simulation_Oracle_v1.json
        name = f.stem.split("_")[0].upper()
        if name in programs:
            programs[name]["has_oracle"] = True
            programs[name]["oracle_path"] = str(f)
            
    # Check canonical IR
    canonical_dir = DATA_DIR / "canonical"
    if canonical_dir.exists():
        for f in canonical_dir.glob("*.canonical.json"):
            name = f.name.replace(".canonical.json", "").upper()
            if name in programs:
                programs[name]["has_ir"] = True
                programs[name]["ir_path"] = str(f)

    return sorted(programs.values(), key=lambda x: x["program"])


def load_program_full(honcho: HonchoClient, prog: dict,
                      run_cfg_extractor: bool = True) -> dict:
    """Load all available artifacts for one program into Honcho."""
    name = prog["program"]
    result = {"program": name, "steps": {}}

    # 1. Load byte layout if available
    if prog.get("has_layout"):
        with open(prog["layout_path"]) as f:
            layout_data = json.load(f)
        if isinstance(layout_data, dict) and "records" in layout_data:
            fields = []
            for rec in layout_data["records"]:
                fields.extend(rec.get("fields", []))
            layout_data = fields
        elif isinstance(layout_data, dict):
            layout_data = list(layout_data.values())
        r = load_layout(honcho, name, layout_data)
        result["steps"]["layout"] = r
        print(f"  [LAYOUT] {name}: {r.get('loaded', 0)} fields")
    else:
        print(f"  [LAYOUT] {name}: no layout file — skipping")

    # 2. Load or generate CFG
    cfg_path = Path(f"docs/{name}_cfg_summary.json")
    if not cfg_path.exists() and prog.get("has_cfg"):
        cfg_path = Path(prog["cfg_path"])

    if cfg_path.exists():
        with open(cfg_path) as f:
            cfg_data = json.load(f)
        r = load_cfg(honcho, name, cfg_data)
        result["steps"]["cfg"] = r
        print(f"  [CFG]    {name}: loaded")
    elif run_cfg_extractor and prog.get("source"):
        # Generate CFG on the fly
        out_path = f"docs/{name}_cfg_summary.json"
        cmd = [sys.executable, "scripts/extract_cfg_summary.py",
               "--source", prog["source"], 
               "--report-dir", "validation/reports",
               "--output", out_path]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0 and Path(out_path).exists():
            with open(out_path) as f:
                cfg_data = json.load(f)
            r = load_cfg(honcho, name, cfg_data)
            result["steps"]["cfg"] = r
            print(f"  [CFG]    {name}: generated + loaded")
        else:
            print(f"  [CFG]    {name}: extractor failed — {proc.stderr[:100]}")
    else:
        print(f"  [CFG]    {name}: no CFG available — skipping")

    # 3. Load oracle if available
    if prog.get("has_oracle"):
        with open(prog["oracle_path"]) as f:
            oracle_data = json.load(f)
        from honcho_loader import load_oracle
        r = load_oracle(honcho, name, oracle_data)
        result["steps"]["oracle"] = r
        print(f"  [ORACLE] {name}: loaded")

    # 4. Load IR if available
    if prog.get("has_ir"):
        with open(prog["ir_path"]) as f:
            ir_data = json.load(f)
        
        # Determine format (manifest vs pure canonical)
        units = []
        if isinstance(ir_data, dict) and "units" in ir_data:
            for unit in ir_data["units"]:
                units.append(unit.get("value", unit))
        elif isinstance(ir_data, dict) and "paragraphs" in ir_data:
            units = ir_data["paragraphs"]
        elif isinstance(ir_data, list):
            units = ir_data
            
        from honcho_loader import load_program
        r = load_program(honcho, name, units)
        result["steps"]["ir"] = r
        print(f"  [IR]     {name}: {r.get('loaded', 0)} paragraphs loaded")

    # 5. Write meta entry
    meta = {
        "program": name,
        "source": prog.get("source", ""),
        "has_layout": prog.get("has_layout", False),
        "has_cfg": "cfg" in result["steps"],
        "has_ir": prog.get("has_ir", False),
        "has_oracle": prog.get("has_oracle", False),
        "loaded_at": datetime.now(timezone.utc).isoformat()
    }
    honcho.set(meta_key(name), meta)
    result["steps"]["meta"] = {"loaded": 1}
    print(f"  [META]   {name}: written")

    return result


def main():
    parser = argparse.ArgumentParser(description="Load full CardDemo corpus into Honcho")
    parser.add_argument("--discover", action="store_true",
                        help="Show available programs and artifacts without loading")
    parser.add_argument("--run", action="store_true",
                        help="Load all programs into Honcho")
    parser.add_argument("--program", help="Load a single specific program")
    parser.add_argument("--skip-cfg-gen", action="store_true",
                        help="Skip CFG generation for programs missing CFG files")
    args = parser.parse_args()

    programs = discover_programs()

    if args.discover or (not args.run and not args.program):
        print(f"\n{'Program':<20} {'Source':>6} {'Layout':>8} {'CFG':>6} {'IR':>6} {'Oracle':>8}")
        print("-" * 62)
        for p in programs:
            print(f"{p['program']:<20} "
                  f"{'✅' if p.get('source') else '❌':>6} "
                  f"{'✅' if p['has_layout'] else '❌':>8} "
                  f"{'✅' if p['has_cfg'] else '❌':>6} "
                  f"{'✅' if p['has_ir'] else '❌':>6} "
                  f"{'✅' if p['has_oracle'] else '❌':>8}")
        print(f"\nTotal: {len(programs)} programs")
        return

    honcho = HonchoClient()
    to_load = programs

    if args.program:
        to_load = [p for p in programs if p["program"] == args.program.upper()]
        if not to_load:
            print(f"ERROR: program {args.program} not found")
            sys.exit(1)

    print(f"\nLoading {len(to_load)} programs into Honcho...\n")
    total_start = datetime.now(timezone.utc)

    all_results = []
    for prog in to_load:
        print(f"\n{'='*40}")
        print(f"Program: {prog['program']}")
        r = load_program_full(honcho, prog,
                              run_cfg_extractor=not args.skip_cfg_gen)
        all_results.append(r)

    elapsed = (datetime.now(timezone.utc) - total_start).total_seconds()
    print(f"\n{'='*40}")
    print(f"Corpus load complete.")
    print(f"Programs processed: {len(all_results)}")
    print(f"Total time: {elapsed:.1f}s")

    # Save corpus manifest
    manifest_path = Path("docs/corpus_load_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump({
            "loaded_at": total_start.isoformat(),
            "program_count": len(all_results),
            "elapsed_seconds": elapsed,
            "results": all_results
        }, f, indent=2)
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()

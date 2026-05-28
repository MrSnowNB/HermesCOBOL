# HermesCOBOL — Honcho-as-RAM Expansion Plan

## Overview

Yesterday's session proved the core loop: extract paragraph IR from COBOL source → load to Honcho under a deterministic key → simulate execution traces → derive a regression oracle from the mutates diff. COACTUPC is fully loaded (39 units), the simulation engine works, and the oracle has 6 write-only fields locked with fully-qualified paths.

The goal of this expansion is to scale that loop to the **entire CardDemo COBOL corpus** — every program, every paragraph, every working-storage field — so that all business logic is queryable from Honcho without ever re-parsing COBOL source again. Honcho is the RAM. The harness is the CPU. The extraction pipeline is the compiler.

***

## Architecture

```
COBOL Source (.cob)
      │
      ▼
hermes_v11_combined_extractor.py   ← already built, parses paragraphs/reads/mutates/performs
      │
      ▼
Statement IR JSON  (per program)   ← already proven on COACTUPC
      │
      ▼
honcho_loader.py   ← NEW (Step 1 below)
      │
      ▼
Honcho Memory Store
  ├── {PROGRAM}/para/{paragraph}   ← paragraph IR (39 units for COACTUPC today)
  ├── {PROGRAM}/layout/{field}     ← byte layout per WS field (Step 2)
  ├── {PROGRAM}/cfg/summary        ← call graph adjacency list (Step 3)
  ├── {PROGRAM}/oracle/v1          ← simulation oracle (Step 4)
  └── {PROGRAM}/meta               ← program metadata (Step 5)
      │
      ▼
Simulation Engine (recursive PERFORM traversal)
      │
      ▼
Business Logic Queries  (no re-parsing, pure Honcho reads)
```

***

## Key Schema (canonical — never deviate from this)

| Key Pattern | Value | Example |
|---|---|---|
| `{PROG}/para/{name}` | Full paragraph IR JSON | `COACTUPC/para/0000-MAIN` |
| `{PROG}/layout/{dotted.path}` | Byte layout entry | `COACTUPC/layout/WS-MISC-STORAGE.ACCT-UPDATE-RECORD` |
| `{PROG}/cfg/summary` | Adjacency list JSON | `COACTUPC/cfg/summary` |
| `{PROG}/oracle/v1` | Oracle JSON | `COACTUPC/oracle/v1` |
| `{PROG}/meta` | Program metadata | `COACTUPC/meta` |

**PROGRAM name is always uppercase, no extension.** `COACTUPC` not `coactupc` not `COACTUPC.cob`.

***

## Phased Plan

### Phase 1 — `honcho_loader.py` (TODAY)
Build the canonical loader script. Parameterized, idempotent, verifiable. Loads paragraph IR for any program. This is the foundation every subsequent phase depends on.

### Phase 2 — Byte Layout Load
Run `extract_byte_layout.py` (already exists) on each program. Load every WORKING-STORAGE field under `{PROG}/layout/{dotted.field.path}`. Enables value-level simulation — the simulator knows field sizes, types, and REDEFINES chains.

### Phase 3 — CFG Load
Run `extract_cfg_summary.py` (already exists) on each program. Load the call graph adjacency list under `{PROG}/cfg/summary`. Enables cross-program trace planning without running the full simulator.

### Phase 4 — Oracle Generation + Load
For each program with a loaded para IR, run the display-vs-write simulation diff automatically. Store the resulting oracle under `{PROG}/oracle/v1`. COACTUPC already has this manually — Phase 4 automates it for all programs.

### Phase 5 — Corpus Meta Index
After all programs are loaded, write a corpus-level index under `CORPUS/index` listing every loaded program, its paragraph count, whether layout/cfg/oracle are loaded, and the 4 external targets (if any). This is the master table of contents for the entire Honcho store.

***

***

# STEP 1 — Build `honcho_loader.py`

## What This Script Does

`honcho_loader.py` is the canonical loader that takes any program's Statement IR (the JSON produced by the extraction pipeline) and loads it into Honcho under the correct key schema. It is **idempotent** (safe to re-run), **verifiable** (spot-checks after loading), and **parameterized** (works for any program, not just COACTUPC).

***

## Exact Instructions for Hermes

***

### CONTEXT — What Hermes Needs to Know

You are working in the HermesCOBOL project at `C:\work\HermesCOBOL\`. The Honcho server is your persistent memory store. Yesterday you completed the following for COACTUPC:

- Extracted 78 paragraphs from `data/preprocessed/COACTUPC.cob`
- Produced `docs/COACTUPC_Statement_IR_v1_Final.md` (the canonical IR)
- Loaded 39 non-EXIT paragraph units to Honcho under `COACTUPC/para/{name}` keys
- Produced `docs/COACTUPC_Honcho_Load_Manifest.json`
- Produced `docs/COACTUPC_Simulation_Oracle_v1.json`

Today you are building `honcho_loader.py` — the repeatable, scriptable version of the manual load process you did yesterday. This script will be the standard tool for loading any program's IR into Honcho.

***

### TASK — Write `scripts/honcho_loader.py`

Create the file `scripts/honcho_loader.py` with the following exact specification.

***

#### Imports and Config

```python
#!/usr/bin/env python3
"""
honcho_loader.py — Canonical Honcho memory loader for HermesCOBOL IR data.

Usage:
    python scripts/honcho_loader.py --program COACTUPC --manifest docs/COACTUPC_Honcho_Load_Manifest.json
    python scripts/honcho_loader.py --program COACTUPC --ir docs/COACTUPC_Statement_IR_v1_Final.md
    python scripts/honcho_loader.py --verify COACTUPC
    python scripts/honcho_loader.py --list
"""

import argparse
import json
import os
import sys
import re
from datetime import datetime, timezone
from pathlib import Path
```

***

#### Honcho Client Wrapper

Write a class `HonchoClient` that wraps the existing Honcho server interface used in the project. Check how the existing scripts (e.g., `hermes_v11_combined_extractor.py`) connect to Honcho and use the same connection method. The class must expose these methods:

```python
class HonchoClient:
    def __init__(self):
        # Connect using same method as existing scripts
        # Check scripts/config.py for connection parameters
        pass

    def set(self, key: str, value: dict) -> bool:
        """Store a JSON-serializable value under key. Return True on success."""
        pass

    def get(self, key: str) -> dict | None:
        """Retrieve value by key. Return None if not found."""
        pass

    def keys(self, prefix: str = "") -> list[str]:
        """List all keys matching prefix."""
        pass

    def delete(self, key: str) -> bool:
        """Delete a key. Return True on success."""
        pass
```

***

#### Key Schema Functions

```python
def para_key(program: str, paragraph: str) -> str:
    """COACTUPC/para/0000-MAIN"""
    return f"{program.upper()}/para/{paragraph}"

def layout_key(program: str, field_path: str) -> str:
    """COACTUPC/layout/WS-MISC-STORAGE.ACCT-UPDATE-RECORD"""
    return f"{program.upper()}/layout/{field_path}"

def oracle_key(program: str, version: int = 1) -> str:
    """COACTUPC/oracle/v1"""
    return f"{program.upper()}/oracle/v{version}"

def cfg_key(program: str) -> str:
    """COACTUPC/cfg/summary"""
    return f"{program.upper()}/cfg/summary"

def meta_key(program: str) -> str:
    """COACTUPC/meta"""
    return f"{program.upper()}/meta"
```

***

#### IR Parser

The script must handle two IR input formats:

**Format A — JSON manifest** (from `COACTUPC_Honcho_Load_Manifest.json`):
```json
{
  "program": "COACTUPC",
  "total_units": 39,
  "units": [
    { "key": "COACTUPC/0000-MAIN", "value": { ... } }
  ]
}
```

**Format B — Markdown IR** (from `COACTUPC_Statement_IR_v1_Final.md`):
The markdown contains fenced JSON blocks per paragraph. Parse each ```json ... ``` block and extract the paragraph IR object.

```python
def parse_manifest(path: Path) -> tuple[str, list[dict]]:
    """
    Parse a Honcho load manifest JSON file.
    Returns (program_name, list_of_ir_units).
    Each unit is a dict with 'paragraph' and all IR fields.
    """
    with open(path) as f:
        data = json.load(f)
    program = data["program"]
    units = [unit["value"] for unit in data["units"]]
    return program, units


def parse_ir_markdown(path: Path) -> tuple[str, list[dict]]:
    """
    Parse a Statement IR markdown file containing fenced JSON blocks.
    Returns (program_name, list_of_ir_units).
    Extracts program name from first JSON block's 'program' field.
    """
    text = path.read_text(encoding="utf-8")
    # Extract all ```json ... ``` blocks
    blocks = re.findall(r"```json\s*([\s\S]*?)```", text)
    units = []
    program = None
    for block in blocks:
        try:
            obj = json.loads(block.strip())
            if "paragraph" in obj and "program" in obj:
                if program is None:
                    program = obj["program"]
                units.append(obj)
        except json.JSONDecodeError:
            continue
    return program, units
```

***

#### Exit Paragraph Filter

```python
def is_exit_paragraph(paragraph_name: str) -> bool:
    """
    Return True if paragraph is a stub EXIT paragraph.
    EXIT paragraphs end with -EXIT and have no performs/reads/mutates.
    These are excluded from Honcho loading.
    """
    return paragraph_name.upper().endswith("-EXIT")


def should_load(unit: dict) -> bool:
    """
    Return True if this unit should be loaded to Honcho.
    Excludes EXIT paragraphs (stub terminators with zero content).
    """
    name = unit.get("paragraph", "")
    if is_exit_paragraph(name):
        return False
    return True
```

***

#### Core Load Function

```python
def load_program(
    honcho: HonchoClient,
    program: str,
    units: list[dict],
    overwrite: bool = True,
    dry_run: bool = False
) -> dict:
    """
    Load all paragraph IR units for a program into Honcho.
    
    Returns a result dict:
    {
        "program": str,
        "loaded": int,
        "skipped_exit": int,
        "skipped_existing": int,
        "failed": int,
        "keys_loaded": list[str],
        "timestamp": str
    }
    """
    result = {
        "program": program,
        "loaded": 0,
        "skipped_exit": 0,
        "skipped_existing": 0,
        "failed": 0,
        "keys_loaded": [],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    for unit in units:
        para_name = unit.get("paragraph", "UNKNOWN")
        key = para_key(program, para_name)

        # Skip EXIT paragraphs
        if not should_load(unit):
            result["skipped_exit"] += 1
            continue

        # Skip if exists and not overwriting
        if not overwrite:
            existing = honcho.get(key)
            if existing is not None:
                result["skipped_existing"] += 1
                continue

        if dry_run:
            print(f"  [DRY RUN] Would load: {key}")
            result["loaded"] += 1
            result["keys_loaded"].append(key)
            continue

        # Load to Honcho
        success = honcho.set(key, unit)
        if success:
            result["loaded"] += 1
            result["keys_loaded"].append(key)
            print(f"  [OK] {key}")
        else:
            result["failed"] += 1
            print(f"  [FAIL] {key}", file=sys.stderr)

    return result
```

***

#### Verification Function

```python
def verify_program(honcho: HonchoClient, program: str) -> dict:
    """
    Verify that a program's IR is correctly loaded in Honcho.
    
    Runs spot checks:
    1. At least 1 unit loaded
    2. 0000-MAIN exists (if program has it)
    3. All loaded units have non-empty 'paragraph' field
    4. No EXIT paragraphs were loaded
    5. Program-specific spot checks if known
    
    Returns verification report dict.
    """
    prefix = f"{program.upper()}/para/"
    keys = honcho.keys(prefix)
    
    report = {
        "program": program,
        "keys_found": len(keys),
        "checks": [],
        "passed": True
    }

    # Check 1: at least 1 unit
    check1 = len(keys) > 0
    report["checks"].append({
        "name": "at_least_one_unit",
        "passed": check1,
        "detail": f"{len(keys)} units found"
    })
    if not check1:
        report["passed"] = False

    # Check 2: no EXIT paragraphs loaded
    exit_keys = [k for k in keys if k.upper().endswith("-EXIT")]
    check2 = len(exit_keys) == 0
    report["checks"].append({
        "name": "no_exit_paragraphs",
        "passed": check2,
        "detail": f"{len(exit_keys)} EXIT keys found: {exit_keys[:3]}"
    })
    if not check2:
        report["passed"] = False

    # Check 3: all units retrievable and have paragraph field
    bad_units = []
    for key in keys[:10]:  # spot check first 10
        unit = honcho.get(key)
        if unit is None or "paragraph" not in unit:
            bad_units.append(key)
    check3 = len(bad_units) == 0
    report["checks"].append({
        "name": "units_retrievable",
        "passed": check3,
        "detail": f"Spot checked {min(10, len(keys))} units. Bad: {bad_units}"
    })
    if not check3:
        report["passed"] = False

    # Program-specific checks
    KNOWN_CHECKS = {
        "COACTUPC": [
            ("COACTUPC/para/0000-MAIN", "performs", 4),
            ("COACTUPC/para/1200-EDIT-MAP-INPUTS", "performs", 30),
            ("COACTUPC/para/9600-WRITE-PROCESSING", "mutates", 8),
        ]
    }
    if program.upper() in KNOWN_CHECKS:
        for key, field, expected_min in KNOWN_CHECKS[program.upper()]:
            unit = honcho.get(key)
            if unit:
                actual = len(unit.get(field, []))
                passed = actual >= expected_min
                report["checks"].append({
                    "name": f"spot_check_{key.split('/')[-1]}_{field}",
                    "passed": passed,
                    "detail": f"{field} count: {actual} (expected >= {expected_min})"
                })
                if not passed:
                    report["passed"] = False

    return report
```

***

#### List Function

```python
def list_loaded_programs(honcho: HonchoClient) -> list[dict]:
    """
    List all programs currently loaded in Honcho.
    Returns list of { program, para_count, has_oracle, has_layout, has_cfg }.
    """
    all_keys = honcho.keys("")
    programs = {}
    
    for key in all_keys:
        parts = key.split("/")
        if len(parts) < 2:
            continue
        prog = parts[0]
        namespace = parts[1] if len(parts) > 1 else ""
        
        if prog not in programs:
            programs[prog] = {
                "program": prog,
                "para_count": 0,
                "has_oracle": False,
                "has_layout": False,
                "has_cfg": False,
                "has_meta": False
            }
        
        if namespace == "para":
            programs[prog]["para_count"] += 1
        elif namespace == "oracle":
            programs[prog]["has_oracle"] = True
        elif namespace == "layout":
            programs[prog]["has_layout"] = True
        elif namespace == "cfg":
            programs[prog]["has_cfg"] = True
        elif namespace == "meta":
            programs[prog]["has_meta"] = True
    
    return sorted(programs.values(), key=lambda x: x["program"])
```

***

#### CLI Entry Point

```python
def main():
    parser = argparse.ArgumentParser(
        description="HermesCOBOL Honcho loader — loads IR data into Honcho memory store"
    )
    parser.add_argument("--program", help="Program name (e.g. COACTUPC)")
    parser.add_argument("--manifest", help="Path to Honcho load manifest JSON")
    parser.add_argument("--ir", help="Path to Statement IR markdown file")
    parser.add_argument("--verify", metavar="PROGRAM", help="Verify a program's Honcho load")
    parser.add_argument("--list", action="store_true", help="List all loaded programs")
    parser.add_argument("--overwrite", action="store_true", default=True,
                        help="Overwrite existing keys (default: True)")
    parser.add_argument("--no-overwrite", dest="overwrite", action="store_false",
                        help="Skip keys that already exist")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be loaded without writing to Honcho")
    parser.add_argument("--output-manifest", metavar="PATH",
                        help="Save load result manifest to this JSON path")
    args = parser.parse_args()

    honcho = HonchoClient()

    # --list mode
    if args.list:
        programs = list_loaded_programs(honcho)
        print(f"\n{'Program':<20} {'Paragraphs':>10} {'Oracle':>8} {'Layout':>8} {'CFG':>6}")
        print("-" * 58)
        for p in programs:
            print(f"{p['program']:<20} {p['para_count']:>10} "
                  f"{'✅' if p['has_oracle'] else '❌':>8} "
                  f"{'✅' if p['has_layout'] else '❌':>8} "
                  f"{'✅' if p['has_cfg'] else '❌':>6}")
        print(f"\nTotal programs: {len(programs)}")
        return

    # --verify mode
    if args.verify:
        report = verify_program(honcho, args.verify)
        print(f"\nVerification: {args.verify}")
        for check in report["checks"]:
            status = "✅" if check["passed"] else "❌"
            print(f"  {status} {check['name']}: {check['detail']}")
        overall = "PASSED" if report["passed"] else "FAILED"
        print(f"\nOverall: {overall} ({report['keys_found']} keys found)")
        sys.exit(0 if report["passed"] else 1)

    # Load mode — requires --program and one of --manifest or --ir
    if not args.program:
        parser.error("--program is required for load operations")
    if not args.manifest and not args.ir:
        parser.error("one of --manifest or --ir is required")

    # Parse input
    if args.manifest:
        path = Path(args.manifest)
        if not path.exists():
            print(f"ERROR: manifest not found: {path}", file=sys.stderr)
            sys.exit(1)
        program, units = parse_manifest(path)
        print(f"Parsed manifest: {len(units)} units for {program}")
    else:
        path = Path(args.ir)
        if not path.exists():
            print(f"ERROR: IR file not found: {path}", file=sys.stderr)
            sys.exit(1)
        program, units = parse_ir_markdown(path)
        print(f"Parsed IR markdown: {len(units)} units for {program}")

    # Override program name if explicitly provided
    if args.program:
        program = args.program.upper()

    print(f"\nLoading {program} to Honcho...")
    if args.dry_run:
        print("(DRY RUN — no writes will occur)")

    result = load_program(
        honcho=honcho,
        program=program,
        units=units,
        overwrite=args.overwrite,
        dry_run=args.dry_run
    )

    # Summary
    print(f"\n{'='*50}")
    print(f"Program:          {result['program']}")
    print(f"Loaded:           {result['loaded']}")
    print(f"Skipped (EXIT):   {result['skipped_exit']}")
    print(f"Skipped (exists): {result['skipped_existing']}")
    print(f"Failed:           {result['failed']}")
    print(f"Timestamp:        {result['timestamp']}")

    # Save output manifest if requested
    if args.output_manifest and not args.dry_run:
        out_path = Path(args.output_manifest)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nManifest saved: {out_path}")

    # Run verification automatically after load
    if not args.dry_run and result["failed"] == 0:
        print(f"\nRunning post-load verification...")
        report = verify_program(honcho, program)
        for check in report["checks"]:
            status = "✅" if check["passed"] else "❌"
            print(f"  {status} {check['name']}: {check['detail']}")
        if not report["passed"]:
            print("\nWARNING: Verification failed — check Honcho connection and data")
            sys.exit(1)
        else:
            print(f"\n✅ Verification passed. {program} is live in Honcho.")

    sys.exit(0 if result["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
```

***

### VALIDATION — Run These After Writing the Script

After writing `scripts/honcho_loader.py`, run in this order:

```bash
# 1. Dry run against existing COACTUPC manifest — should show 39 keys, write nothing
python scripts/honcho_loader.py --program COACTUPC \
  --manifest docs/COACTUPC_Honcho_Load_Manifest.json \
  --dry-run

# 2. List what is currently in Honcho
python scripts/honcho_loader.py --list

# 3. Verify COACTUPC is correctly loaded (should pass all spot checks)
python scripts/honcho_loader.py --verify COACTUPC

# 4. Full reload of COACTUPC from manifest (idempotent — should show 39 loaded, 0 failed)
python scripts/honcho_loader.py --program COACTUPC \
  --manifest docs/COACTUPC_Honcho_Load_Manifest.json \
  --output-manifest docs/COACTUPC_Honcho_Reload_Manifest.json
```

**Expected output for step 3:**
```
Verification: COACTUPC
  ✅ at_least_one_unit: 39 units found
  ✅ no_exit_paragraphs: 0 EXIT keys found
  ✅ units_retrievable: Spot checked 10 units. Bad: []
  ✅ spot_check_0000-MAIN_performs: performs count: 4 (expected >= 4)
  ✅ spot_check_1200-EDIT-MAP-INPUTS_performs: performs count: 30 (expected >= 30)
  ✅ spot_check_9600-WRITE-PROCESSING_mutates: mutates count: 8 (expected >= 8)

Overall: PASSED (39 keys found)
```

If any check fails, report the exact error output before proceeding.

***

### COMMIT after validation passes

```bash
git add scripts/honcho_loader.py
git commit -m "feat: add honcho_loader.py — canonical parameterized IR loader with verification"
```

***

### REPORT BACK with

1. The exact output of `--dry-run` (first 5 and last 5 lines)
2. The exact output of `--verify COACTUPC`
3. The output of `--list`
4. Confirmation of git commit hash

Do not proceed to Phase 2 (byte layout load) until all four validation commands pass cleanly.
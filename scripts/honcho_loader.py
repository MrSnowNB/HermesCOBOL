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
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# Try to import Honcho config from scripts.config
try:
    from scripts.config import HONCHO_BASE_URL, HONCHO_WORKSPACE_ID
except ImportError:
    # Fallback if running from outside the package structure
    HONCHO_BASE_URL = "http://localhost:18000"
    HONCHO_WORKSPACE_ID = "hermes"


class HonchoClient:
    def __init__(self, base_url: str = HONCHO_BASE_URL, workspace_id: str = HONCHO_WORKSPACE_ID):
        self.base_url = base_url.rstrip("/")
        self.workspace_id = workspace_id
        self.session_id = "hermes-agent" # Use existing session

    def _request(self, method: str, path: str, data: dict = None) -> dict | list | None:
        url = f"{self.base_url}{path}"
        req_data = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=req_data, method=method)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as resp:
                if 200 <= resp.status < 300:
                    content = resp.read().decode("utf-8")
                    return json.loads(content) if content else {}
                else:
                    print(f"Unexpected status {resp.status}: {resp.read().decode('utf-8')}", file=sys.stderr)
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='ignore')
            print(f"HTTP Error {e.code} at {path}: {body}", file=sys.stderr)
        except urllib.error.URLError as e:
            print(f"Connection Error: {e}", file=sys.stderr)
        return None

    def set(self, key: str, value: dict) -> bool:
        """Store a JSON-serializable value under key using Messages. Idempotent (adds new entry)."""
        # Mapping Key Schema {PROG}/para/{name} to v3 Messages
        path = f"/v3/workspaces/{self.workspace_id}/sessions/{self.session_id}/messages"
        payload = {
            "messages": [
                {
                    "content": json.dumps(value),
                    "peer_id": "hermes",
                    "metadata": {"key": key}
                }
            ]
        }
        res = self._request("POST", path, payload)
        return res is not None

    def set_batch(self, units: list[tuple[str, dict]]) -> bool:
        """Store multiple units in a single batch call using Messages."""
        if not units:
            return True
        
        path = f"/v3/workspaces/{self.workspace_id}/sessions/{self.session_id}/messages"
        messages = []
        for key, value in units:
            messages.append({
                "content": json.dumps(value),
                "peer_id": "hermes",
                "metadata": {"key": key}
            })
        
        payload = {"messages": messages}
        res = self._request("POST", path, payload)
        return res is not None

    def get(self, key: str) -> dict | None:
        """Retrieve value by key from Messages. Returns the most recent one."""
        # Using size=1 and reverse=true to get the latest message for this key
        path = f"/v3/workspaces/{self.workspace_id}/sessions/{self.session_id}/messages/list?size=1&reverse=true"
        # Filtering by metadata in messages/list
        payload = {"filters": {"metadata": {"key": key}}}
        res = self._request("POST", path, payload)
        if res and isinstance(res, dict) and res.get("items"):
            msg = res["items"][0]
            try:
                return json.loads(msg["content"])
            except (json.JSONDecodeError, TypeError):
                return msg["content"]
        return None

    def keys(self, prefix: str = "") -> list[str]:
        """List all keys matching prefix from Messages using pagination."""
        all_keys = set()
        page = 1
        size = 100
        
        while True:
            path = f"/v3/workspaces/{self.workspace_id}/sessions/{self.session_id}/messages/list?size={size}&page={page}"
            payload = {"filters": {}}
            res = self._request("POST", path, payload)
            
            if not res or not isinstance(res, dict) or not res.get("items"):
                break
                
            items = res["items"]
            for item in items:
                meta = item.get("metadata")
                if meta and isinstance(meta, dict):
                    k = meta.get("key")
                    if k and (not prefix or k.startswith(prefix)):
                        all_keys.add(k)
            
            if len(items) < size:
                break
            page += 1
            
        return list(all_keys)

    def delete(self, key: str) -> bool:
        """Delete all messages matching this key."""
        path = f"/v3/workspaces/{self.workspace_id}/sessions/{self.session_id}/messages/list"
        payload = {"filters": {"metadata": {"key": key}}}
        res = self._request("POST", path, payload)
        success = True
        if res and isinstance(res, dict) and res.get("items"):
            for item in res["items"]:
                mid = item["id"]
                del_path = f"/v3/workspaces/{self.workspace_id}/sessions/{self.session_id}/messages/{mid}"
                if self._request("DELETE", del_path) is None:
                    success = False
        return success


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


def parse_manifest(path: Path) -> tuple[str, list[dict]]:
    """
    Parse a Honcho load manifest JSON file.
    Returns (program_name, list_of_ir_units).
    Each unit is a dict with 'paragraph' and all IR fields.
    """
    with open(path) as f:
        data = json.load(f)
    program = data["program"]
    # Handle both "value" wrapper (from COACTUPC_Honcho_Load_Manifest.json)
    # and flat units if they appear.
    units = []
    for unit in data["units"]:
        if "value" in unit:
            units.append(unit["value"])
        else:
            units.append(unit)
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
        # Double check if it really has no content
        has_logic = (len(unit.get("performs", [])) > 0 or 
                     len(unit.get("reads", [])) > 0 or 
                     len(unit.get("mutates", [])) > 0)
        if not has_logic:
            return False
    return True


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


def verify_program(honcho: HonchoClient, program: str) -> dict:
    """
    Verify that a program's IR is correctly loaded in Honcho.
    
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
    # Note: should_load might have let some through if they had logic, 
    # but normally they shouldn't be there.
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
    if not args.program and not (args.manifest or args.ir):
        parser.print_help()
        sys.exit(0)

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

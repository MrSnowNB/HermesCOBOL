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
import time
from datetime import datetime, timezone
from pathlib import Path
import requests

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
        self.headers = {"Content-Type": "application/json"}
        self.messages_url = f"{self.base_url}/v3/workspaces/{self.workspace_id}/sessions/{self.session_id}/messages"

    def _request(self, method: str, path: str, data: dict = None) -> dict | list | None:
        # Fallback for non-batch methods, using urllib or simple requests
        url = f"{self.base_url}{path}"
        try:
            if method == "POST":
                resp = requests.post(url, json=data, headers=self.headers)
            elif method == "DELETE":
                resp = requests.delete(url, headers=self.headers)
            else:
                resp = requests.request(method, url, json=data, headers=self.headers)
            
            if 200 <= resp.status_code < 300:
                if resp.text:
                    return resp.json()
                return {}
            elif resp.status_code == 404:
                return None
            else:
                print(f"HTTP Error {resp.status_code} at {path}: {resp.text}", file=sys.stderr)
        except requests.exceptions.RequestException as e:
            print(f"Connection Error: {e}", file=sys.stderr)
        return None

    def set(self, key: str, value: dict, force_overwrite: bool = True) -> bool:
        """Write key→value. When force_overwrite=True, skip delete — just POST."""
        content_str = json.dumps(value)
        if len(content_str) > 24000:
            msg_payload = {
                "content": f"Large object stored in metadata: {key}",
                "peer_id": "hermes",
                "metadata": {"key": key, "data": value}
            }
        else:
            msg_payload = {
                "content": content_str,
                "peer_id": "hermes",
                "metadata": {"key": key}
            }
            
        payload = {"messages": [msg_payload]}
        resp = requests.post(self.messages_url, json=payload, headers=self.headers)
        return resp.status_code in (200, 201)

    def set_batch(self, items: list[tuple[str, dict]]) -> dict:
        """
        Write multiple key→value pairs efficiently.
        items: list of (key, value) tuples
        Returns: {"loaded": int, "failed": int, "failed_keys": list, "keys_loaded": list}
        """
        result = {"loaded": 0, "failed": 0, "failed_keys": [], "keys_loaded": []}
        session = requests.Session()
        
        chunk_size = 100
        for i in range(0, len(items), chunk_size):
            chunk = items[i:i+chunk_size]
            messages = []
            for key, value in chunk:
                content_str = json.dumps(value)
                if len(content_str) > 24000:
                    messages.append({
                        "content": f"Large object stored in metadata: {key}",
                        "peer_id": "hermes",
                        "metadata": {"key": key, "data": value}
                    })
                else:
                    messages.append({
                        "content": content_str,
                        "peer_id": "hermes",
                        "metadata": {"key": key}
                    })
            
            payload = {"messages": messages}
            try:
                resp = session.post(self.messages_url, json=payload, headers=self.headers)
                if resp.status_code in (200, 201):
                    result["loaded"] += len(chunk)
                    result["keys_loaded"].extend([k for k, v in chunk])
                else:
                    # If batch fails, count all as failed
                    print(f"Batch POST failed: {resp.status_code} - {resp.text}", file=sys.stderr)
                    result["failed"] += len(chunk)
                    result["failed_keys"].extend([k for k, v in chunk])
            except Exception as e:
                print(f"Batch POST error: {e}", file=sys.stderr)
                result["failed"] += len(chunk)
                result["failed_keys"].extend([k for k, v in chunk])
                
        session.close()
        return result

    def get(self, key: str) -> dict | None:
        """Retrieve value by key from Messages. Returns the most recent one."""
        # Using size=1 and reverse=true to get the latest message for this key
        path = f"/v3/workspaces/{self.workspace_id}/sessions/{self.session_id}/messages/list?size=1&reverse=true"
        # Filtering by metadata in messages/list
        payload = {"filters": {"metadata": {"key": key}}}
        res = self._request("POST", path, payload)
        if res and isinstance(res, dict) and res.get("items"):
            msg = res["items"][0]
            meta = msg.get("metadata", {})
            if "data" in meta:
                return meta["data"]
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
    """
    batch = []
    skipped_exit = 0

    for unit in units:
        para_name = unit.get("paragraph", "UNKNOWN")
        key = para_key(program, para_name)

        if not should_load(unit):
            skipped_exit += 1
            continue

        batch.append((key, unit))

    if dry_run:
        for key, _ in batch:
            print(f"  [DRY RUN] Would load: {key}")
        return {
            "program": program,
            "loaded": len(batch),
            "skipped_exit": skipped_exit,
            "skipped_existing": 0,
            "failed": 0,
            "keys_loaded": [k for k, _ in batch],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # Single batched write
    batch_res = honcho.set_batch(batch)
    
    return {
        "program": program,
        "loaded": batch_res["loaded"],
        "skipped_exit": skipped_exit,
        "skipped_existing": 0,
        "failed": batch_res["failed"],
        "keys_loaded": batch_res["keys_loaded"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def load_layout(
    honcho: HonchoClient,
    program: str,
    layout_data: list[dict],
    overwrite: bool = True,
    dry_run: bool = False
) -> dict:
    """
    Load WORKING-STORAGE byte layout entries into Honcho.
    Key schema: {PROGRAM}/layout/{field_path}
    """
    batch = []
    
    for entry in layout_data:
        field_path = (entry.get("field_path") or 
                      entry.get("qualified_name") or 
                      entry.get("name") or 
                      entry.get("path"))
        
        if not field_path:
            continue
        key = layout_key(program, field_path)
        batch.append((key, entry))

    if dry_run:
        for key, _ in batch:
            print(f"  [DRY RUN] Would load layout: {key}")
        return {
            "program": program,
            "loaded": len(batch),
            "failed": 0,
            "keys_loaded": [k for k, _ in batch],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # Single batched write
    batch_res = honcho.set_batch(batch)
    
    return {
        "program": program,
        "loaded": batch_res["loaded"],
        "failed": batch_res["failed"],
        "keys_loaded": batch_res["keys_loaded"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }



def load_cfg(
    honcho: HonchoClient,
    program: str,
    cfg_data: dict,
    dry_run: bool = False
) -> dict:
    """Load CFG summary under {PROGRAM}/cfg/summary key."""
    key = cfg_key(program)
    if dry_run:
        print(f"  [DRY RUN] Would load CFG: {key}")
        return {"program": program, "loaded": 1, "failed": 0}
    success = honcho.set(key, cfg_data)
    status = "OK" if success else "FAIL"
    print(f"  [{status}] {key}")
    return {
        "program": program,
        "loaded": 1 if success else 0,
        "failed": 0 if success else 1,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def load_oracle(
    honcho: HonchoClient,
    program: str,
    oracle_data: dict,
    version: int = 1,
    dry_run: bool = False
) -> dict:
    """Load simulation oracle under {PROGRAM}/oracle/v{n} key."""
    key = oracle_key(program, version)
    if dry_run:
        print(f"  [DRY RUN] Would load oracle: {key}")
        return {"program": program, "loaded": 1, "failed": 0}
    success = honcho.set(key, oracle_data)
    status = "OK" if success else "FAIL"
    print(f"  [{status}] {key}")
    return {
        "program": program,
        "key": key,
        "loaded": 1 if success else 0,
        "failed": 0 if success else 1,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


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
    parser.add_argument("--layout", help="Path to Byte Layout JSON file")
    parser.add_argument("--cfg", help="Path to CFG JSON file")
    parser.add_argument("--oracle", help="Path to Oracle JSON file")
    parser.add_argument("--oracle-version", type=int, default=1, help="Oracle version (default: 1)")
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

    # Load mode — requires --program and one of --manifest, --ir, --layout, --cfg, or --oracle
    if not args.program and not (args.manifest or args.ir or args.layout or args.cfg or args.oracle):
        parser.print_help()
        sys.exit(0)

    if not args.program:
        parser.error("--program is required for load operations")

    program = args.program.upper()

    # --oracle mode
    if args.oracle:
        oracle_path = Path(args.oracle)
        if not oracle_path.exists():
            print(f"ERROR: oracle file not found: {oracle_path}", file=sys.stderr)
            sys.exit(1)
        with open(oracle_path) as f:
            oracle_data = json.load(f)
        
        print(f"Loaded oracle data for {program}")
        result = load_oracle(honcho, program, oracle_data, 
                             version=args.oracle_version, dry_run=args.dry_run)
        
        sys.exit(0 if result["failed"] == 0 else 1)

    # --cfg mode
    if args.cfg:
        cfg_path = Path(args.cfg)
        if not cfg_path.exists():
            print(f"ERROR: CFG file not found: {cfg_path}", file=sys.stderr)
            sys.exit(1)
        with open(cfg_path) as f:
            cfg_data = json.load(f)
        
        print(f"Loaded CFG data for {program}")
        result = load_cfg(honcho, program, cfg_data, dry_run=args.dry_run)
        
        sys.exit(0 if result["failed"] == 0 else 1)

    # --layout mode
    if args.layout:
        layout_path = Path(args.layout)
        if not layout_path.exists():
            print(f"ERROR: layout file not found: {layout_path}", file=sys.stderr)
            sys.exit(1)
        with open(layout_path) as f:
            raw_data = json.load(f)
        
        # Flatten the byte_layout.py / extract_byte_layout.py format
        layout_data = []
        if isinstance(raw_data, dict):
            # Format A: {"records": [{"name": "R1", "fields": [...]}, ...]}
            if "records" in raw_data:
                for rec in raw_data["records"]:
                    # Add the record itself
                    rec_entry = rec.copy()
                    if "fields" in rec_entry:
                        del rec_entry["fields"]
                    layout_data.append(rec_entry)
                    # Add all fields
                    layout_data.extend(rec.get("fields", []))
            # Format B: {"sections": {"working_storage": [...], ...}}
            elif "sections" in raw_data:
                def _flatten(items):
                    for item in items:
                        item_copy = item.copy()
                        children = item_copy.pop("children", [])
                        layout_data.append(item_copy)
                        _flatten(children)
                for sect in raw_data["sections"].values():
                    _flatten(sect)
            else:
                layout_data = list(raw_data.values())
        else:
            layout_data = raw_data

        print(f"Loaded layout: {len(layout_data)} field entries for {program}")
        result = load_layout(honcho, program, layout_data,
                             overwrite=args.overwrite, dry_run=args.dry_run)
        print(f"\nLayout loaded: {result['loaded']} fields, {result['failed']} failed")
        
        if args.output_manifest and not args.dry_run:
            out_path = Path(args.output_manifest)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w") as f:
                json.dump(result, f, indent=2)
            print(f"Manifest saved: {out_path}")
        
        sys.exit(0 if result["failed"] == 0 else 1)

    # Load IR mode
    if not args.manifest and not args.ir:
        parser.error("one of --manifest, --ir or --layout is required")

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

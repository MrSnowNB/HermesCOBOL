#!/usr/bin/env python3
"""
schema.py — Canonical schema definition and validator for structured_facts.json

Schema version: 1.0

All downstream consumers (validate_roundtrip.py, Hermes agent layer, etc.)
must use the canonical key names defined here.

Usage:
  python scripts/schema.py            # validate all data/facts/*.json files
  python scripts/schema.py CBACT01C   # validate single program
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FACTS_DIR = REPO_ROOT / "data" / "facts"

SCHEMA_VERSION = "1.0"

# ---------------------------------------------------------------------------
# Canonical top-level keys (all required in v1.0)
# ---------------------------------------------------------------------------
REQUIRED_KEYS = [
    "schema_version",
    "program",
    "source_file",
    "extracted_at",
    "gnucobol_version",
    "gate_rc",
    "gate_status",
    "gate_reasons",
    "cics_present",       # bool — EXEC CICS present in raw source
    "sql_present",        # bool — EXEC SQL present in raw source
    "paragraphs",         # list[str] — paragraph label names
    "data_items",         # list[str] — 01-level WS names
    "external_calls",     # list[str] — CALL literal targets
    "internal_performs",  # list[str] — PERFORM targets
    "data_files",         # list[{name, ddname, organization, access}]
    "copybooks_referenced", # list[str] — COPY targets
    "cfg",                # {source, edges, unresolved}
]

REQUIRED_DATA_FILE_KEYS = ["name", "ddname"]
REQUIRED_CFG_KEYS       = ["source", "edges", "unresolved"]


def validate(facts: dict) -> list[str]:
    """Return list of validation error strings. Empty = valid."""
    errors: list[str] = []

    # schema_version check
    sv = facts.get("schema_version")
    if sv != SCHEMA_VERSION:
        errors.append(f"schema_version is '{sv}', expected '{SCHEMA_VERSION}'")

    # Required top-level keys
    for key in REQUIRED_KEYS:
        if key not in facts:
            errors.append(f"Missing required key: '{key}'")

    # Type checks
    for bool_key in ("cics_present", "sql_present"):
        if bool_key in facts and not isinstance(facts[bool_key], bool):
            errors.append(f"'{bool_key}' must be bool, got {type(facts[bool_key]).__name__}")

    for list_key in ("paragraphs", "data_items", "external_calls",
                     "internal_performs", "copybooks_referenced"):
        if list_key in facts:
            if not isinstance(facts[list_key], list):
                errors.append(f"'{list_key}' must be list")
            elif not all(isinstance(x, str) for x in facts[list_key]):
                errors.append(f"'{list_key}' must be list[str]")

    if "data_files" in facts:
        if not isinstance(facts["data_files"], list):
            errors.append("'data_files' must be list")
        else:
            for i, df in enumerate(facts["data_files"]):
                for rk in REQUIRED_DATA_FILE_KEYS:
                    if rk not in df:
                        errors.append(f"data_files[{i}] missing key '{rk}'")

    if "cfg" in facts:
        if not isinstance(facts["cfg"], dict):
            errors.append("'cfg' must be dict")
        else:
            for rk in REQUIRED_CFG_KEYS:
                if rk not in facts["cfg"]:
                    errors.append(f"cfg missing key '{rk}'")

    return errors


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else None

    if not FACTS_DIR.exists():
        print(f"data/facts/ not found — run 'python scripts/extract_facts.py' first.")
        return 1

    if arg:
        prog = arg.upper().removesuffix(".JSON")
        paths = [FACTS_DIR / f"{prog}.json"]
    else:
        paths = sorted(FACTS_DIR.glob("*.json"))

    if not paths or not paths[0].exists():
        print(f"No facts files found.")
        return 1

    all_ok = True
    for path in paths:
        if not path.exists():
            print(f"  MISSING  {path.name}")
            all_ok = False
            continue
        try:
            facts = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ERROR    {path.name}: {e}")
            all_ok = False
            continue
        errs = validate(facts)
        if errs:
            print(f"  FAIL     {path.name}")
            for e in errs:
                print(f"           - {e}")
            all_ok = False
        else:
            cics = "C" if facts.get("cics_present") else "-"
            sql  = "S" if facts.get("sql_present")  else "-"
            print(f"  OK       {facts['program']:22s}  "
                  f"v{facts['schema_version']}  "
                  f"cics={cics} sql={sql}  "
                  f"paras={len(facts['paragraphs']):3d}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

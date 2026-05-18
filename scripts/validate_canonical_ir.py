#!/usr/bin/env python3
"""
validate_canonical_ir.py — Stage 5-H validation gate for the Canonical IR.

Validates that each data/canonical/<PROG>.canonical.json file satisfies
the structural contracts required for downstream consumption.

Usage:
    python scripts/validate_canonical_ir.py                 # all programs
    python scripts/validate_canonical_ir.py COMEN01C        # single program
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from config import (
    REPO_ROOT,
    RAW_CBL_DIR,
    FACTS_DIR,
    VALID_DIR,
    PASS1_ANNOTATIONS_DIR,
    FALLTHROUGH_DIR,
    CFG_DIR,
    CANONICAL_DIR,
)

from cobol_parse_utils import PARAGRAPH_NOISE, RESERVED_WORDS

VALIDATION_DIR = VALID_DIR / "canonical-ir"


# ---------------------------------------------------------------------------
# Rule groups for status labels (FIX 4)
# ---------------------------------------------------------------------------
SCHEMA_RULES = {"schema_version", "file_missing", "facts_missing"}
CICS_RULES = {"cics_preprocess_consistency", "stray_preprocessed_file"}
PARAGRAPHS_RULES = {
    "missing_paragraphs",
    "noise_paragraph",
    "missing_paragraph_fields",
    "performs_referential_integrity",
    "terminator_enum",
    "falls_through_to_referential_integrity",
}
CONSISTENCY_RULES = {"cfg_edges_mismatch", "annotation_missing"}  # stubs for future


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _get_status_for_group(program_failures: list[dict], rule_set: set[str]) -> str:
    """Return OK / FAIL / SKIP for a rule group."""
    if not program_failures:
        return "OK"
    for f in program_failures:
        if f.get("rule") in rule_set:
            return "FAIL"
    return "OK"


def validate_canonical(prog: str) -> dict[str, Any]:
    """Run all Stage 5-H contracts against a single canonical IR file."""
    canonical_path = CANONICAL_DIR / f"{prog}.canonical.json"
    facts_path = FACTS_DIR / f"{prog}.json"

    result = {
        "program": prog,
        "canonical_path": str(canonical_path),
        "gate_status": "PASS",
        "failures": [],
        "warnings": [],
    }

    canonical = _load_json(canonical_path)
    facts = _load_json(facts_path)

    if not canonical:
        result["gate_status"] = "FAIL"
        result["failures"].append({
            "rule": "file_missing",
            "severity": "error",
            "message": f"Canonical IR file not found: {canonical_path}"
        })
        return result

    if not facts:
        result["gate_status"] = "FAIL"
        result["failures"].append({
            "rule": "facts_missing",
            "severity": "error",
            "message": f"Facts file not found: {facts_path}"
        })
        return result

    # Build set of valid paragraph names for referential integrity checks
    paragraph_names: set[str] = {
        p.get("name") for p in canonical.get("paragraphs", []) if p.get("name")
    }

    # Allowed terminator values (Phase 2)
    VALID_TERMINATORS = {
        "implicit",
        "implicit-end-of-program",
        "goto",
        "stop-run",
        "goback",
        "explicit-exit",
        "cics-return",
        "cics-xctl",
    }

    # 1. Schema version
    if canonical.get("schema_version") != "1.4":
        result["failures"].append({
            "rule": "schema_version",
            "severity": "error",
            "message": f"Expected schema_version '1.4', got {canonical.get('schema_version')}"
        })

    # 2. CICS / Preprocess consistency
    cics_present = canonical.get("cics_present", False)
    preprocess_available = canonical.get("preprocess_available", False)

    if cics_present and preprocess_available:
        result["failures"].append({
            "rule": "cics_preprocess_consistency",
            "severity": "error",
            "message": "cics_present is true but preprocess_available is also true",
            "details": {
                "preprocessed_file": str(VALID_DIR / "reconstructed" / "cbl" / f"{prog}.pre.cbl")
            }
        })

    # 3. Paragraph completeness against facts
    facts_paragraphs = set(facts.get("paragraphs", []))
    canonical_paragraphs = {p.get("name") for p in canonical.get("paragraphs", []) if p.get("name")}

    missing = facts_paragraphs - canonical_paragraphs
    if missing:
        result["failures"].append({
            "rule": "missing_paragraphs",
            "severity": "error",
            "message": f"{len(missing)} paragraphs present in facts but missing from canonical IR",
            "details": {"missing": sorted(missing)}
        })

    # 4. Noise / Reserved word contamination (FIX 1)
    bad_names = [
        p["name"] for p in canonical.get("paragraphs", [])
        if p.get("name") in PARAGRAPH_NOISE or p.get("name") in RESERVED_WORDS
    ]
    if bad_names:
        result["failures"].append({
            "rule": "noise_paragraph",
            "severity": "error",
            "message": "Paragraph names contain noise or reserved tokens",
            "details": {"invalid_names": bad_names}
        })

    # 5. Required fields per paragraph
    required_fields = {"name", "terminator", "falls_through_to", "performs", "goto_targets", "reachable"}
    for p in canonical.get("paragraphs", []):
        missing_fields = required_fields - set(p.keys())
        if missing_fields:
            result["failures"].append({
                "rule": "missing_paragraph_fields",
                "severity": "error",
                "message": f"Paragraph '{p.get('name')}' is missing required fields",
                "details": {"paragraph": p.get("name"), "missing_fields": list(missing_fields)}
            })

        name = p.get("name") or "<unknown>"

        # Phase 2: terminator enum enforcement
        t = p.get("terminator")
        if t not in VALID_TERMINATORS:
            result["failures"].append({
                "rule": "terminator_enum",
                "severity": "error",
                "message": f"Paragraph '{name}' has invalid terminator value",
                "details": {"paragraph": name, "terminator": t}
            })

        # Phase 2: performs[] referential integrity
        for target in p.get("performs", []) or []:
            if target not in paragraph_names:
                result["failures"].append({
                    "rule": "performs_referential_integrity",
                    "severity": "error",
                    "message": f"Paragraph '{name}' performs unknown target '{target}'",
                    "details": {"paragraph": name, "invalid_perform_target": target}
                })

        # Phase 2: falls_through_to referential integrity
        tgt = p.get("falls_through_to")
        if tgt is not None and tgt not in paragraph_names:
            result["failures"].append({
                "rule": "falls_through_to_referential_integrity",
                "severity": "error",
                "message": f"Paragraph '{name}' falls through to unknown target '{tgt}'",
                "details": {"paragraph": name, "invalid_falls_through_to": tgt}
            })

    # 6. No paragraphs at all (legitimate for some utility programs like COBSWAIT)
    if not canonical.get("paragraphs"):
        result["warnings"].append({
            "rule": "no_paragraphs",
            "severity": "warning",
            "message": "Canonical IR contains no paragraphs — verify facts.json is also empty"
        })

    if result["failures"]:
        result["gate_status"] = "FAIL"

    return result


def run_single(prog: str) -> str:
    """Run validation for one program. Returns gate_status ('PASS' or 'FAIL')."""
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    report = validate_canonical(prog)

    out_path = VALIDATION_DIR / f"{prog}.canonical-validation.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Per-program grouped status output (FIX 4)
    failures = report.get("failures", [])
    schema_status = _get_status_for_group(failures, SCHEMA_RULES)
    cics_status = _get_status_for_group(failures, CICS_RULES)
    paragraphs_status = _get_status_for_group(failures, PARAGRAPHS_RULES)
    consistency_status = _get_status_for_group(failures, CONSISTENCY_RULES)

    status = report["gate_status"]
    print(f"[{status}] {prog:<12} "
          f"schema={schema_status}  "
          f"cics={cics_status}  "
          f"paragraphs={paragraphs_status}  "
          f"consistency={consistency_status}")

    return status


def run_all() -> int:
    """Run validation for all programs. Returns number of failures."""
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    cbl_files = sorted(RAW_CBL_DIR.glob("*.cbl")) + sorted(RAW_CBL_DIR.glob("*.CBL"))
    progs = sorted({f.stem.upper() for f in cbl_files})

    print(f"[corpus] validating canonical IR for {len(progs)} programs...")

    summary_list = []
    failures_by_rule: dict[str, int] = {}
    fail_count = 0

    for prog in progs:
        report = validate_canonical(prog)
        out_path = VALIDATION_DIR / f"{prog}.canonical-validation.json"
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        status = report["gate_status"]
        failures = report.get("failures", [])

        # Update per-rule counts
        for f in failures:
            rule = f.get("rule", "unknown")
            failures_by_rule[rule] = failures_by_rule.get(rule, 0) + 1

        if status == "FAIL":
            fail_count += 1

        summary_list.append({
            "program": prog,
            "status": status,
            "failure_count": len(failures)
        })

        # Print grouped status
        schema_status = _get_status_for_group(failures, SCHEMA_RULES)
        cics_status = _get_status_for_group(failures, CICS_RULES)
        paragraphs_status = _get_status_for_group(failures, PARAGRAPHS_RULES)
        consistency_status = _get_status_for_group(failures, CONSISTENCY_RULES)

        print(f"[{status}] {prog:<12} "
              f"schema={schema_status}  "
              f"cics={cics_status}  "
              f"paragraphs={paragraphs_status}  "
              f"consistency={consistency_status}")

    # Write proper summary.json (FIX 3)
    summary = {
        "programs_total": len(progs),
        "programs_pass": len(progs) - fail_count,
        "programs_fail": fail_count,
        "failures_by_rule": failures_by_rule
    }

    summary_path = VALIDATION_DIR / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\n[summary] {len(progs) - fail_count}/{len(progs)} programs passed Stage 5-H")
    return fail_count


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage 5-H Canonical IR Validator")
    ap.add_argument("program", nargs="?", help="Program name (optional)")
    args = ap.parse_args()

    if args.program:
        prog = args.program.upper()
        if not (RAW_CBL_DIR / f"{prog}.cbl").exists():
            print(f"ERROR: unknown program {prog}", file=sys.stderr)
            return 2
        status = run_single(prog)
        return 0 if status == "PASS" else 1
    else:
        fail_count = run_all()
        return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

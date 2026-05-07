#!/usr/bin/env python3
"""
validate_roundtrip.py — HermesCOBOL deterministic round-trip validator.

Mode A: Preprocess round-trip (non-CICS programs only)
  - Runs `cobc -E -I data/raw/cpy -I data/raw/cpy-bms <PROG>.cbl`
  - Saves output to validation/reconstructed/cbl/<PROG>.pre.cbl
  - SHA-256 hashes raw and preprocessed outputs (LF-normalized)
  - CICS programs are SKIPPED (not failed): GnuCOBOL cannot preprocess
    raw EXEC CICS blocks without a CICS translator. This is by design.

Mode B: Structural coverage check against canonical schema v1.0 facts
  - Independently scans data/raw/cbl/<PROG>.cbl for:
      paragraphs, 01-level data items, CALL/PERFORM targets,
      SELECT..ASSIGN files, EXEC CICS / EXEC SQL presence.
  - Compares against data/facts/<PROG>.json using canonical key names.
  - Runs for ALL programs including CICS programs.

Outputs:
  - validation/reports/<PROG>.validation.json per program
  - validation/reports/summary.json

Exit code:
  0 if all programs PASS (or PASS with cics_structural_only note)
  1 if any program FAIL

Usage:
  python scripts/validate_roundtrip.py             # all programs
  python scripts/validate_roundtrip.py CBACT01C    # single program

Read-only against data/raw/ and data/facts/. Writes only under validation/.
No LLMs. No network. Manual-first.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths — import from config, fall back to inline resolution
# ---------------------------------------------------------------------------
try:
    from scripts.config import (
        REPO_ROOT, RAW_CBL_DIR, RAW_CPY_DIR, RAW_CPY_BMS_DIR,
        FACTS_DIR, VALID_DIR, RECON_CBL_DIR, REPORTS_DIR,
    )
except ImportError:
    REPO_ROOT       = Path(__file__).resolve().parent.parent
    RAW_CBL_DIR     = REPO_ROOT / "data" / "raw" / "cbl"
    RAW_CPY_DIR     = REPO_ROOT / "data" / "raw" / "cpy"
    RAW_CPY_BMS_DIR = REPO_ROOT / "data" / "raw" / "cpy-bms"
    FACTS_DIR       = REPO_ROOT / "data" / "facts"
    VALID_DIR       = REPO_ROOT / "validation"
    RECON_CBL_DIR   = VALID_DIR / "reconstructed" / "cbl"
    REPORTS_DIR     = VALID_DIR / "reports"

# ---------------------------------------------------------------------------
# Regex patterns (mirror extract_facts.py exactly)
# ---------------------------------------------------------------------------
RE_PARAGRAPH = re.compile(
    r"^[ ]{0,11}([A-Z0-9][A-Z0-9-]*)[ \t]*\.[ \t]*(?:\*.*)?$",
    re.MULTILINE,
)
RE_SECTION = re.compile(
    r"^[ ]{0,11}([A-Z0-9][A-Z0-9-]*)[ \t]+SECTION[ \t]*\.[ \t]*$",
    re.MULTILINE | re.IGNORECASE,
)
RE_DATA_01 = re.compile(
    r"^[ ]{0,11}01[ \t]+([A-Z0-9][A-Z0-9-]*)",
    re.MULTILINE | re.IGNORECASE,
)
RE_CALL_LITERAL = re.compile(
    r"\bCALL[ \t]+['\"]([A-Z0-9][A-Z0-9-]*)['\"] ",
    re.IGNORECASE,
)
RE_PERFORM = re.compile(
    r"\bPERFORM[ \t]+([A-Z0-9][A-Z0-9-]*)", re.IGNORECASE
)
RE_SELECT = re.compile(
    r"\bSELECT[ \t]+([A-Z0-9][A-Z0-9-]*)[ \t]+ASSIGN[ \t]+TO[ \t]+([A-Z0-9][A-Z0-9-]*)",
    re.IGNORECASE,
)
RE_EXEC_CICS = re.compile(r"\bEXEC[ \t]+CICS\b", re.IGNORECASE)
RE_EXEC_SQL  = re.compile(r"\bEXEC[ \t]+SQL\b",  re.IGNORECASE)

RESERVED_WORDS = frozenset([
    "IDENTIFICATION", "ENVIRONMENT", "DATA", "PROCEDURE",
    "CONFIGURATION", "INPUT-OUTPUT", "FILE", "WORKING-STORAGE",
    "LINKAGE", "LOCAL-STORAGE", "REPORT", "SCREEN",
    "PROGRAM-ID", "AUTHOR", "INSTALLATION", "DATE-WRITTEN",
    "DATE-COMPILED", "SECURITY", "REMARKS",
    "FD", "SD", "RD",
])

PERFORM_NON_TARGETS = frozenset([
    "UNTIL", "VARYING", "TIMES", "WITH", "TEST",
    "THRU", "THROUGH", "BEFORE", "AFTER",
])


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def lf_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def sha256_lf(path: Path) -> str:
    h = hashlib.sha256()
    h.update(lf_bytes(path))
    return h.hexdigest()


def gnucobol_version() -> str:
    try:
        out = subprocess.run(
            ["cobc", "--version"],
            capture_output=True, text=True, check=False, timeout=15,
        )
        first = (out.stdout or out.stderr).splitlines()[0].strip()
        return first or "unknown"
    except Exception as e:
        return f"unavailable: {e}"


def strip_cobol_comments(text: str) -> str:
    out = []
    for line in text.splitlines():
        if len(line) >= 7 and line[6] in ("*", "/"):
            continue
        if line.strip():
            out.append(line)
    return "\n".join(out)


def raw_has_cics(cbl_path: Path) -> bool:
    """Scan raw source directly for EXEC CICS — no facts required."""
    try:
        text = cbl_path.read_text(encoding="utf-8", errors="replace")
        return bool(RE_EXEC_CICS.search(text))
    except Exception:
        return False


def facts_cics(facts: dict | None) -> bool | None:
    """Return cics_present from facts if available, else None."""
    if facts and isinstance(facts.get("cics_present"), bool):
        return facts["cics_present"]
    return None


def is_cics_program(cbl_path: Path, facts: dict | None) -> bool:
    """
    Determine if a program uses CICS.
    Prefer facts.cics_present (already scanned); fall back to raw scan.
    """
    fc = facts_cics(facts)
    if fc is not None:
        return fc
    return raw_has_cics(cbl_path)


# ---------------------------------------------------------------------------
# Raw structure scanner — mirrors extract_facts.py logic exactly
# ---------------------------------------------------------------------------
def extract_raw_structure(cbl_path: Path) -> dict:
    raw  = cbl_path.read_text(encoding="utf-8", errors="replace")
    text = strip_cobol_comments(raw)

    paragraphs: set[str] = set()
    for m in RE_PARAGRAPH.finditer(text):
        name = m.group(1).upper()
        if name not in RESERVED_WORDS and not name.endswith("-DIVISION"):
            paragraphs.add(name)
    for m in RE_SECTION.finditer(text):
        paragraphs.discard(m.group(1).upper())

    data_items: set[str] = {
        m.group(1).upper()
        for m in RE_DATA_01.finditer(text)
        if m.group(1).upper() != "FILLER"
    }

    calls: set[str] = {m.group(1).upper() for m in RE_CALL_LITERAL.finditer(text)}

    perform_targets: set[str] = {
        m.group(1).upper()
        for m in RE_PERFORM.finditer(text)
        if m.group(1).upper() not in PERFORM_NON_TARGETS
    }

    selects: list[dict] = [
        {"name": m.group(1).upper(), "ddname": m.group(2).upper()}
        for m in RE_SELECT.finditer(text)
    ]

    return {
        "paragraphs":      sorted(paragraphs),
        "data_items":      sorted(data_items),
        "calls":           sorted(calls),
        "perform_targets": sorted(perform_targets),
        "selects":         selects,
        "cics_present":    bool(RE_EXEC_CICS.search(text)),
        "sql_present":     bool(RE_EXEC_SQL.search(text)),
    }


# ---------------------------------------------------------------------------
# Facts loader — expects canonical schema v1.0 from extract_facts.py
# ---------------------------------------------------------------------------
def load_facts(prog: str) -> dict | None:
    path = FACTS_DIR / f"{prog}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"__load_error__": str(e)}


# ---------------------------------------------------------------------------
# Mode B: structural diff using canonical key names
# ---------------------------------------------------------------------------
def structural_diff(raw: dict, facts: dict | None) -> dict:
    if facts is None:
        return _diff_no_facts(raw, "missing")
    if "__load_error__" in facts:
        return _diff_no_facts(raw, facts["__load_error__"])

    schema_ver = facts.get("schema_version", "unknown")

    facts_paras = {p.upper() for p in facts.get("paragraphs", []) if isinstance(p, str)}
    facts_data  = {d.upper() for d in facts.get("data_items", []) if isinstance(d, str)}
    facts_calls = {c.upper() for c in facts.get("external_calls", []) if isinstance(c, str)}

    facts_sels: set[tuple[str, str]] = set()
    for f in facts.get("data_files", []):
        if isinstance(f, dict) and f.get("name") and f.get("ddname"):
            facts_sels.add((f["name"].upper(), f["ddname"].upper()))

    raw_paras = set(raw["paragraphs"])
    raw_data  = set(raw["data_items"])
    raw_calls = set(raw["calls"])
    raw_sels  = {(s["name"], s["ddname"]) for s in raw["selects"]}

    cics_fact = bool(facts.get("cics_present", False))
    sql_fact  = bool(facts.get("sql_present",  False))

    return {
        "facts_present":      True,
        "facts_error":        None,
        "schema_version":     schema_ver,
        "missing_paragraphs": sorted(raw_paras - facts_paras),
        "missing_data_items": sorted(raw_data  - facts_data),
        "missing_calls":      sorted(raw_calls - facts_calls),
        "missing_selects":    [f"{n}:{d}" for (n, d) in sorted(raw_sels - facts_sels)],
        "cics_mismatch":      raw["cics_present"] != cics_fact,
        "sql_mismatch":       raw["sql_present"]  != sql_fact,
    }


def _diff_no_facts(raw: dict, error: str) -> dict:
    return {
        "facts_present":      False,
        "facts_error":        error,
        "schema_version":     None,
        "missing_paragraphs": raw["paragraphs"],
        "missing_data_items": raw["data_items"],
        "missing_calls":      raw["calls"],
        "missing_selects":    [f'{s["name"]}:{s["ddname"]}' for s in raw["selects"]],
        "cics_mismatch":      raw["cics_present"],
        "sql_mismatch":       raw["sql_present"],
    }


# ---------------------------------------------------------------------------
# Mode A: cobc -E preprocess (non-CICS programs only)
# ---------------------------------------------------------------------------
def run_cobc_preprocess(cbl_path: Path, out_path: Path) -> tuple[bool, str]:
    """
    Run cobc -E with both copybook directories on the include path.
    Includes -ext flags so cobc resolves both .cpy and .CPY extensions.
    Returns (ok, error_string).
    """
    cmd = [
        "cobc", "-E",
        "-I", str(RAW_CPY_DIR),
        "-I", str(RAW_CPY_BMS_DIR),
        "-ext", "cpy",
        "-ext", "CPY",
        "-ext", "",
        str(cbl_path),
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False, timeout=120,
        )
    except FileNotFoundError:
        return False, "cobc not found on PATH"
    except subprocess.TimeoutExpired:
        return False, "cobc -E timed out after 120s"
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "cobc non-zero exit").strip()
        return False, err[:400]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result.stdout, encoding="utf-8")
    return True, ""


# ---------------------------------------------------------------------------
# Per-program validation
# ---------------------------------------------------------------------------
def validate_program(cbl_path: Path, gcv: str) -> dict:
    prog     = cbl_path.stem.upper()
    pre_path = RECON_CBL_DIR / f"{prog}.pre.cbl"

    facts = load_facts(prog)

    # --- CICS detection (prefer facts, fall back to raw scan) ---
    cics = is_cics_program(cbl_path, facts)

    # --- Mode A: preprocess ---
    raw_sha           = sha256_lf(cbl_path)
    preprocess_ok     = False
    preprocess_err    = None
    preprocess_skipped         = False
    preprocess_skipped_reason  = None
    pre_sha           = None

    if cics:
        # GnuCOBOL cannot preprocess raw EXEC CICS without a translator.
        # Mark as skipped — this is expected and by design, not a failure.
        preprocess_skipped        = True
        preprocess_skipped_reason = "cics_no_translator"
    else:
        ok, err = run_cobc_preprocess(cbl_path, pre_path)
        preprocess_ok  = ok
        preprocess_err = err or None
        if ok and pre_path.exists():
            pre_sha = sha256_lf(pre_path)

    # --- Mode B: structural coverage ---
    raw_struct = extract_raw_structure(cbl_path)
    diff       = structural_diff(raw_struct, facts)

    # --- Gate evaluation ---
    gate_fail_reasons: list[str] = []
    gate_note: str | None = None

    # Mode A gate: fail only on actual failure, not on intentional skip
    if not preprocess_skipped and not preprocess_ok:
        gate_fail_reasons.append("preprocess_failed")

    # Mode B gate (same for all programs)
    if not diff["facts_present"]:
        gate_fail_reasons.append("facts_missing")
    if diff["missing_paragraphs"]:
        gate_fail_reasons.append("missing_paragraphs")
    if diff["missing_data_items"]:
        gate_fail_reasons.append("missing_data_items")
    if diff["missing_calls"]:
        gate_fail_reasons.append("missing_calls")
    if diff["missing_selects"]:
        gate_fail_reasons.append("missing_selects")
    if diff["cics_mismatch"]:
        gate_fail_reasons.append("cics_mismatch")
    if diff["sql_mismatch"]:
        gate_fail_reasons.append("sql_mismatch")

    # Annotate CICS-only pass
    if not gate_fail_reasons and preprocess_skipped:
        gate_note = "cics_structural_only"

    gate_status = "PASS" if not gate_fail_reasons else "FAIL"

    return {
        "program":                   prog,
        "generated_at":              now_iso(),
        "gnucobol_version":          gcv,
        "raw_sha256":                raw_sha,
        "pre_sha256":                pre_sha,
        "preprocess_ok":             preprocess_ok,
        "preprocess_skipped":        preprocess_skipped,
        "preprocess_skipped_reason": preprocess_skipped_reason,
        "preprocess_error":          preprocess_err,
        "schema_version":            diff.get("schema_version"),
        "raw_structure_counts": {
            "paragraphs":      len(raw_struct["paragraphs"]),
            "data_items":      len(raw_struct["data_items"]),
            "calls":           len(raw_struct["calls"]),
            "perform_targets": len(raw_struct["perform_targets"]),
            "selects":         len(raw_struct["selects"]),
        },
        "cics_present":       raw_struct["cics_present"],
        "sql_present":        raw_struct["sql_present"],
        "facts_present":      diff["facts_present"],
        "facts_error":        diff["facts_error"],
        "missing_paragraphs": diff["missing_paragraphs"],
        "missing_data_items": diff["missing_data_items"],
        "missing_calls":      diff["missing_calls"],
        "missing_selects":    diff["missing_selects"],
        "cics_mismatch":      diff["cics_mismatch"],
        "sql_mismatch":       diff["sql_mismatch"],
        "gate_fail_reasons":  gate_fail_reasons,
        "gate_note":          gate_note,
        "gate_status":        gate_status,
    }


# ---------------------------------------------------------------------------
# Program selection
# ---------------------------------------------------------------------------
def select_programs(arg: str | None) -> list[Path]:
    if not RAW_CBL_DIR.exists():
        print(f"ERROR: {RAW_CBL_DIR} does not exist.", file=sys.stderr)
        sys.exit(2)
    if arg:
        stem = arg.upper().removesuffix(".CBL")
        candidate = RAW_CBL_DIR / f"{stem}.cbl"
        if not candidate.exists():
            candidate = RAW_CBL_DIR / f"{stem.lower()}.cbl"
        if not candidate.exists():
            print(f"ERROR: No .cbl file found for '{arg}' in {RAW_CBL_DIR}",
                  file=sys.stderr)
            sys.exit(2)
        return [candidate]
    programs = sorted(RAW_CBL_DIR.glob("*.cbl"))
    if not programs:
        print(f"ERROR: No .cbl files found in {RAW_CBL_DIR}", file=sys.stderr)
        sys.exit(2)
    return programs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    arg = sys.argv[1].upper() if len(sys.argv) > 1 else None

    VALID_DIR.mkdir(parents=True, exist_ok=True)
    RECON_CBL_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    gcv      = gnucobol_version()
    programs = select_programs(arg)

    print("HermesCOBOL round-trip validator  (schema v1.0, raw-data-only)")
    print(f"GnuCOBOL      : {gcv}")
    print(f"Programs      : {len(programs)}")
    print(f"cpy dir       : {RAW_CPY_DIR}  exists={RAW_CPY_DIR.exists()}")
    print(f"cpy-bms dir   : {RAW_CPY_BMS_DIR}  exists={RAW_CPY_BMS_DIR.exists()}")
    print(f"Facts dir     : {FACTS_DIR}  exists={FACTS_DIR.exists()}")
    print()

    per_program: list[dict] = []
    for cbl in programs:
        report = validate_program(cbl, gcv)
        (REPORTS_DIR / f"{cbl.stem.upper()}.validation.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        per_program.append(report)

        if report["preprocess_skipped"]:
            mode_a = f"SKIP({report['preprocess_skipped_reason']})"
        elif report["preprocess_ok"]:
            mode_a = "preprocess=OK"
        else:
            mode_a = "preprocess=FAIL"

        note    = f"  [{report['gate_note']}]" if report.get("gate_note") else ""
        reasons = ",".join(report["gate_fail_reasons"]) or "-"
        print(f"  [{report['gate_status']:4}] {report['program']:22s}  "
              f"{mode_a:30s}  {reasons}{note}")

    passed   = [r for r in per_program if r["gate_status"] == "PASS"]
    failed   = [r for r in per_program if r["gate_status"] == "FAIL"]
    skipped  = [r for r in per_program if r["preprocess_skipped"]]

    # Skipped reasons breakdown
    skipped_reasons: dict[str, int] = {}
    for r in skipped:
        reason = r["preprocess_skipped_reason"] or "unknown"
        skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1

    summary = {
        "generated_at":              now_iso(),
        "gnucobol_version":          gcv,
        "programs_total":            len(per_program),
        "programs_pass":             len(passed),
        "programs_fail":             len(failed),
        "programs_skipped_preprocess": len(skipped),
        "skipped_reasons":           skipped_reasons,
        "first_failures":            [r["program"] for r in failed[:10]],
        "counts": {
            "preprocess_failures":  sum(1 for r in per_program
                                        if not r["preprocess_ok"]
                                        and not r["preprocess_skipped"]),
            "preprocess_skipped":   len(skipped),
            "missing_paragraphs":   sum(len(r["missing_paragraphs"]) for r in per_program),
            "missing_data_items":   sum(len(r["missing_data_items"]) for r in per_program),
            "missing_calls":        sum(len(r["missing_calls"]) for r in per_program),
            "missing_selects":      sum(len(r["missing_selects"]) for r in per_program),
            "cics_mismatches":      sum(1 for r in per_program if r["cics_mismatch"]),
            "sql_mismatches":       sum(1 for r in per_program if r["sql_mismatch"]),
        },
    }

    (REPORTS_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print()
    print(f"Total   : {summary['programs_total']}")
    print(f"Pass    : {summary['programs_pass']}")
    print(f"Fail    : {summary['programs_fail']}")
    print(f"Skipped : {summary['programs_skipped_preprocess']}  "
          f"(Mode A skipped by design: {skipped_reasons})")
    print(f"Reports : {REPORTS_DIR}")

    return 0 if summary["programs_fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

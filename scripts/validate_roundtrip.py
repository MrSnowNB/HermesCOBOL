#!/usr/bin/env python3
"""
validate_roundtrip.py — HermesCOBOL deterministic round-trip validator.

Mode A: Preprocess round-trip
  - Runs `cobc -E -I data/raw/cpy data/raw/cbl/<PROG>.cbl`
  - Saves output to validation/reconstructed/cbl/<PROG>.pre.cbl
  - SHA-256 hashes raw and preprocessed outputs (LF-normalized)

Mode B: Structural coverage check
  - Independently scans data/raw/cbl/<PROG>.cbl for paragraphs,
    01-level data items, CALL/PERFORM targets, SELECT..ASSIGN files,
    EXEC CICS / EXEC SQL presence.
  - Compares against data/facts/<PROG>.json (if present).

Outputs:
  - validation/reports/<PROG>.validation.json per program
  - validation/reports/summary.json

Exit code:
  0 if all programs PASS, 1 otherwise.

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
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Paths — resolved from script location so cwd doesn't matter
# ---------------------------------------------------------------------------
REPO_ROOT     = Path(__file__).resolve().parent.parent
RAW_CBL_DIR   = REPO_ROOT / "data" / "raw" / "cbl"
RAW_CPY_DIR   = REPO_ROOT / "data" / "raw" / "cpy"
FACTS_DIR     = REPO_ROOT / "data" / "facts"
VALID_DIR     = REPO_ROOT / "validation"
RECON_CBL_DIR = VALID_DIR / "reconstructed" / "cbl"
REPORTS_DIR   = VALID_DIR / "reports"

# ---------------------------------------------------------------------------
# Regex patterns — conservative, comment-stripped source only
# ---------------------------------------------------------------------------
# Paragraph: 0-11 leading spaces, name, literal dot, optional inline comment
RE_PARAGRAPH = re.compile(
    r"^[ ]{0,11}([A-Z0-9][A-Z0-9-]{2,})\.[ \t]*(?:\*.*)?$",
    re.MULTILINE,
)
RE_SECTION = re.compile(
    r"^[ ]{0,11}([A-Z0-9][A-Z0-9-]*)[ \t]+SECTION[ \t]*\.[ \t]*$",
    re.MULTILINE | re.IGNORECASE,
)
# 01-level data items: level number 01 followed by a name
RE_DATA_01 = re.compile(
    r"^[ ]{1,11}01[ \t]+([A-Z0-9][A-Z0-9-]*)",
    re.MULTILINE | re.IGNORECASE,
)
# External CALLs: CALL 'PROGNAME' or CALL "PROGNAME"
RE_CALL = re.compile(
    r"\bCALL[ \t]+['\"]([A-Z0-9][A-Z0-9-]*)['\"] ",
    re.IGNORECASE,
)
# PERFORM targets (paragraph name following PERFORM keyword)
RE_PERFORM = re.compile(
    r"\bPERFORM[ \t]+([A-Z0-9][A-Z0-9-]{2,})",
    re.IGNORECASE,
)
# SELECT ... ASSIGN TO
RE_SELECT = re.compile(
    r"\bSELECT[ \t]+([A-Z0-9][A-Z0-9-]*)[ \t]+ASSIGN[ \t]+TO[ \t]+([A-Z0-9:\-\.]+)",
    re.IGNORECASE,
)
RE_EXEC_CICS = re.compile(r"\bEXEC[ \t]+CICS\b", re.IGNORECASE)
RE_EXEC_SQL  = re.compile(r"\bEXEC[ \t]+SQL\b",  re.IGNORECASE)

# Division/section headers and meta entries that look like paragraph names
RESERVED_WORDS = frozenset([
    "IDENTIFICATION", "ENVIRONMENT", "DATA", "PROCEDURE",
    "CONFIGURATION", "INPUT-OUTPUT", "FILE", "WORKING-STORAGE",
    "LINKAGE", "LOCAL-STORAGE", "REPORT", "SCREEN",
    "PROGRAM-ID", "AUTHOR", "INSTALLATION", "DATE-WRITTEN",
    "DATE-COMPILED", "SECURITY", "REMARKS",
    "FD", "SD", "RD", "COPY", "FILLER",
])


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def lf_bytes(path: Path) -> bytes:
    """Read file bytes and normalize CRLF/CR -> LF before hashing."""
    data = path.read_bytes()
    data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return data


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
    """
    Strip lines where column 7 (0-indexed: index 6) is '*' or '/'.
    Also strip blank lines. Preserves everything else.
    These are fixed-format comment indicators.
    """
    out = []
    for line in text.splitlines():
        if len(line) >= 7 and line[6] in ("*", "/"):
            continue
        if line.strip():
            out.append(line)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Raw structure scanner — reads data/raw/cbl/<PROG>.cbl directly
# ---------------------------------------------------------------------------
def extract_raw_structure(cbl_path: Path) -> dict:
    """
    Scan raw COBOL source for structural elements.
    Returns sets/lists of names found — this is the ground truth
    that facts JSON is compared against.
    """
    raw  = cbl_path.read_text(encoding="utf-8", errors="replace")
    text = strip_cobol_comments(raw)

    # -- Paragraphs --
    paragraphs: set[str] = set()
    for m in RE_PARAGRAPH.finditer(text):
        name = m.group(1).upper()
        if name not in RESERVED_WORDS and not name.endswith("-DIVISION"):
            paragraphs.add(name)
    # Remove anything that is actually a SECTION header
    for m in RE_SECTION.finditer(text):
        paragraphs.discard(m.group(1).upper())

    # -- 01-level data items (FILLER excluded) --
    data_items: set[str] = {
        m.group(1).upper()
        for m in RE_DATA_01.finditer(text)
        if m.group(1).upper() != "FILLER"
    }

    # -- External CALL targets --
    calls: set[str] = {m.group(1).upper() for m in RE_CALL.finditer(text)}

    # -- PERFORM targets (internal control flow) --
    perform_targets: set[str] = {
        m.group(1).upper()
        for m in RE_PERFORM.finditer(text)
        if m.group(1).upper() not in (
            "UNTIL", "VARYING", "TIMES", "WITH", "TEST", "THRU", "THROUGH"
        )
    }

    # -- SELECT ... ASSIGN TO file definitions --
    selects: list[dict] = [
        {"name": m.group(1).upper(), "ddname": m.group(2).upper().rstrip(".")}
        for m in RE_SELECT.finditer(text)
    ]

    cics_present = bool(RE_EXEC_CICS.search(text))
    sql_present  = bool(RE_EXEC_SQL.search(text))

    return {
        "paragraphs":      sorted(paragraphs),
        "data_items":      sorted(data_items),
        "calls":           sorted(calls),
        "perform_targets": sorted(perform_targets),
        "selects":         selects,
        "cics_present":    cics_present,
        "sql_present":     sql_present,
    }


# ---------------------------------------------------------------------------
# Facts JSON loader + tolerant field accessors
# ---------------------------------------------------------------------------
def load_facts(prog: str) -> dict | None:
    path = FACTS_DIR / f"{prog}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"__load_error__": str(e)}


def _facts_name_set(facts: dict, *keys: str) -> set[str]:
    """Walk candidate key names and flatten to a set of uppercase strings."""
    for k in keys:
        val = facts.get(k)
        if not isinstance(val, list):
            continue
        out: set[str] = set()
        for item in val:
            if isinstance(item, str):
                out.add(item.upper())
            elif isinstance(item, dict):
                for nk in ("name", "id", "target", "paragraph"):
                    if nk in item and isinstance(item[nk], str):
                        out.add(item[nk].upper())
                        break
        return out
    return set()


def _facts_selects(facts: dict) -> set[tuple[str, str]]:
    """Extract SELECT file pairs from facts under any plausible key name."""
    for k in ("selects", "data_files", "files", "data"):
        val = facts.get(k)
        # data sub-key holds select_files list
        if k == "data" and isinstance(val, dict):
            val = val.get("select_files", [])
        if not isinstance(val, list):
            continue
        out: set[tuple[str, str]] = set()
        for item in val:
            if not isinstance(item, dict):
                continue
            name = (item.get("name") or item.get("logical") or item.get("file") or "")
            dd   = (item.get("ddname") or item.get("assign") or item.get("dd") or "")
            if name and dd:
                out.add((str(name).upper(), str(dd).upper()))
        if out:
            return out
    return set()


# ---------------------------------------------------------------------------
# Mode B: structural diff
# ---------------------------------------------------------------------------
def structural_diff(raw: dict, facts: dict | None) -> dict:
    if facts is None:
        return {
            "facts_present": False,
            "facts_error": "missing",
            "missing_paragraphs": raw["paragraphs"],
            "missing_data_items": raw["data_items"],
            "missing_calls":      raw["calls"],
            "missing_selects":    [f'{s["name"]}:{s["ddname"]}' for s in raw["selects"]],
            "cics_mismatch":      raw["cics_present"],
            "sql_mismatch":       raw["sql_present"],
        }
    if "__load_error__" in facts:
        return {
            "facts_present": False,
            "facts_error": facts["__load_error__"],
            "missing_paragraphs": raw["paragraphs"],
            "missing_data_items": raw["data_items"],
            "missing_calls":      raw["calls"],
            "missing_selects":    [f'{s["name"]}:{s["ddname"]}' for s in raw["selects"]],
            "cics_mismatch":      raw["cics_present"],
            "sql_mismatch":       raw["sql_present"],
        }

    # Paragraph names from facts: flatten from list of dicts
    facts_paras = _facts_name_set(facts, "paragraphs")
    # Also accept names from PERFORM map as implicit coverage
    facts_data  = _facts_name_set(
        facts.get("data", {}), "working_storage_01s"
    ) if isinstance(facts.get("data"), dict) else set()
    facts_calls = _facts_name_set(facts, "external_calls", "calls")
    facts_sels  = _facts_selects(facts)

    raw_paras = set(raw["paragraphs"])
    raw_data  = set(raw["data_items"])
    raw_calls = set(raw["calls"])
    raw_sels  = {(s["name"], s["ddname"]) for s in raw["selects"]}

    missing_paras = sorted(raw_paras - facts_paras)
    missing_data  = sorted(raw_data  - facts_data)
    missing_calls = sorted(raw_calls - facts_calls)
    missing_sels  = sorted(raw_sels  - facts_sels)

    cics_fact = bool(facts.get("cics_present",
                    len(facts.get("cics_verbs", [])) > 0))
    sql_fact  = bool(facts.get("sql_present", False))

    return {
        "facts_present":    True,
        "facts_error":      None,
        "missing_paragraphs": missing_paras,
        "missing_data_items": missing_data,
        "missing_calls":      missing_calls,
        "missing_selects":    [f"{n}:{d}" for (n, d) in missing_sels],
        "cics_mismatch":      raw["cics_present"] != cics_fact,
        "sql_mismatch":       raw["sql_present"]  != sql_fact,
    }


# ---------------------------------------------------------------------------
# Mode A: cobc -E preprocess
# ---------------------------------------------------------------------------
def run_cobc_preprocess(cbl_path: Path, out_path: Path) -> tuple[bool, str]:
    cmd = ["cobc", "-E", "-I", str(RAW_CPY_DIR), str(cbl_path)]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            check=False, timeout=120,
        )
    except FileNotFoundError:
        return False, "cobc not found on PATH"
    except subprocess.TimeoutExpired:
        return False, "cobc -E timed out after 120s"

    if result.returncode != 0:
        err = (result.stderr or result.stdout or "cobc non-zero exit").strip()
        return False, err[:400]  # cap error string

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result.stdout, encoding="utf-8")
    return True, ""


# ---------------------------------------------------------------------------
# Per-program validation
# ---------------------------------------------------------------------------
def validate_program(cbl_path: Path, gcv: str) -> dict:
    prog     = cbl_path.stem.upper()
    pre_path = RECON_CBL_DIR / f"{prog}.pre.cbl"

    # Mode A
    raw_sha = sha256_lf(cbl_path)
    preprocess_ok, preprocess_err = run_cobc_preprocess(cbl_path, pre_path)
    pre_sha = sha256_lf(pre_path) if (preprocess_ok and pre_path.exists()) else None

    # Mode B
    raw_struct = extract_raw_structure(cbl_path)
    facts      = load_facts(prog)
    diff       = structural_diff(raw_struct, facts)

    # Gate evaluation
    gate_fail_reasons: list[str] = []
    if not preprocess_ok:
        gate_fail_reasons.append("preprocess_failed")
    if not diff.get("facts_present"):
        gate_fail_reasons.append("facts_missing")
    if diff.get("missing_paragraphs"):
        gate_fail_reasons.append("missing_paragraphs")
    if diff.get("missing_data_items"):
        gate_fail_reasons.append("missing_data_items")
    if diff.get("missing_calls"):
        gate_fail_reasons.append("missing_calls")
    if diff.get("missing_selects"):
        gate_fail_reasons.append("missing_selects")
    if diff.get("cics_mismatch"):
        gate_fail_reasons.append("cics_mismatch")
    if diff.get("sql_mismatch"):
        gate_fail_reasons.append("sql_mismatch")

    gate_status = "PASS" if not gate_fail_reasons else "FAIL"

    return {
        "program":          prog,
        "generated_at":     now_iso(),
        "gnucobol_version": gcv,
        "raw_sha256":       raw_sha,
        "pre_sha256":       pre_sha,
        "preprocess_ok":    preprocess_ok,
        "preprocess_error": preprocess_err or None,
        "raw_structure_counts": {
            "paragraphs":      len(raw_struct["paragraphs"]),
            "data_items":      len(raw_struct["data_items"]),
            "calls":           len(raw_struct["calls"]),
            "perform_targets": len(raw_struct["perform_targets"]),
            "selects":         len(raw_struct["selects"]),
        },
        "cics_present":       raw_struct["cics_present"],
        "sql_present":        raw_struct["sql_present"],
        "facts_present":      diff.get("facts_present", False),
        "facts_error":        diff.get("facts_error"),
        "missing_paragraphs": diff.get("missing_paragraphs", []),
        "missing_data_items": diff.get("missing_data_items", []),
        "missing_calls":      diff.get("missing_calls", []),
        "missing_selects":    diff.get("missing_selects", []),
        "cics_mismatch":      diff.get("cics_mismatch", False),
        "sql_mismatch":       diff.get("sql_mismatch", False),
        "gate_fail_reasons":  gate_fail_reasons,
        "gate_status":        gate_status,
    }


# ---------------------------------------------------------------------------
# Program selection
# ---------------------------------------------------------------------------
def select_programs(arg: str | None) -> list[Path]:
    if not RAW_CBL_DIR.exists():
        print(f"ERROR: {RAW_CBL_DIR} does not exist.", file=sys.stderr)
        print("Place raw .cbl files in data/raw/cbl/ first.", file=sys.stderr)
        sys.exit(2)

    if arg:
        # Accept with or without .cbl extension, any case
        stem = arg.upper().removesuffix(".CBL")
        candidate = RAW_CBL_DIR / f"{stem}.cbl"
        if not candidate.exists():
            # Try lowercase stem
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

    # Ensure output dirs exist
    VALID_DIR.mkdir(parents=True, exist_ok=True)
    RECON_CBL_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    gcv      = gnucobol_version()
    programs = select_programs(arg)

    print(f"HermesCOBOL round-trip validator")
    print(f"GnuCOBOL: {gcv}")
    print(f"Programs: {len(programs)}")
    print(f"Facts dir exists: {FACTS_DIR.exists()}")
    print()

    per_program: list[dict] = []
    for cbl in programs:
        report = validate_program(cbl, gcv)
        out    = REPORTS_DIR / f"{cbl.stem.upper()}.validation.json"
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        per_program.append(report)
        reasons = ",".join(report["gate_fail_reasons"]) or "-"
        print(f"  [{report['gate_status']:4}] {report['program']:20}  {reasons}")

    passed = [r for r in per_program if r["gate_status"] == "PASS"]
    failed = [r for r in per_program if r["gate_status"] == "FAIL"]

    summary = {
        "generated_at":     now_iso(),
        "gnucobol_version": gcv,
        "programs_total":   len(per_program),
        "programs_pass":    len(passed),
        "programs_fail":    len(failed),
        "first_failures":   [r["program"] for r in failed[:10]],
        "counts": {
            "preprocess_failures": sum(
                1 for r in per_program if not r["preprocess_ok"]),
            "missing_paragraphs":  sum(
                len(r["missing_paragraphs"]) for r in per_program),
            "missing_data_items":  sum(
                len(r["missing_data_items"]) for r in per_program),
            "missing_calls":       sum(
                len(r["missing_calls"]) for r in per_program),
            "missing_selects":     sum(
                len(r["missing_selects"]) for r in per_program),
            "cics_mismatches":     sum(
                1 for r in per_program if r["cics_mismatch"]),
            "sql_mismatches":      sum(
                1 for r in per_program if r["sql_mismatch"]),
        },
    }

    (REPORTS_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print()
    print(f"Total : {summary['programs_total']}")
    print(f"Pass  : {summary['programs_pass']}")
    print(f"Fail  : {summary['programs_fail']}")
    print(f"Reports -> {REPORTS_DIR}")

    return 0 if summary["programs_fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

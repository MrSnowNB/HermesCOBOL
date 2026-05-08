#!/usr/bin/env python3
"""
extract_facts.py — HermesCOBOL schema v1.1 extractor.

Reads:
  data/raw/cbl/<PROG>.cbl           raw source
  data/raw/cpy/                     copybooks (non-BMS)
  data/raw/cpy-bms/                 BMS map copybooks
  data/rekt/<PROG>.cbl.report/**    REKT CFG JSON (optional, Stage 2 output)

Writes:
  data/facts/<PROG>.json            canonical structured facts (schema v1.1)

Schema v1.1 additions over v1.0:
  paragraphs_defined    list[{name, source_line, area_a}]
  paragraphs_referenced list[str]
  paragraph_actions     {para_name: [action_tag, ...]}
  file_lineage          [{name, ddname, fd_record}]
  file_operations       {file_name: [{paragraph, operation, source_line}]}
  control_flow          {cfg_source, entry_points, exit_points, edges, unresolved}
  cics                  {commarea_used, commands, maps_used, mapsets_used,
                         aid_keys, screen_flow}  (null for non-CICS programs)

All v1.0 fields are preserved unchanged.

Usage:
  python scripts/extract_facts.py              # all programs
  python scripts/extract_facts.py CBACT01C     # single program

No LLMs. No network. Text-scan only.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_CBL_DIR     = REPO_ROOT / "data" / "raw" / "cbl"
RAW_CPY_DIR     = REPO_ROOT / "data" / "raw" / "cpy"
RAW_CPY_BMS_DIR = REPO_ROOT / "data" / "raw" / "cpy-bms"
FACTS_DIR       = REPO_ROOT / "data" / "facts"
REKT_DIR        = REPO_ROOT / "data" / "rekt"

# Prefer the combined extractor; fall back to the legacy shim if running
# the script directly from the scripts/ directory.
try:
    from scripts.hermes_v11_combined_extractor import enrich, PARAGRAPH_NOISE
except ImportError:
    try:
        from hermes_v11_combined_extractor import enrich, PARAGRAPH_NOISE
    except ImportError:
        from semantic_extract import enrich, PARAGRAPH_NOISE  # legacy shim

SCHEMA_VERSION = "1.1"

# ---------------------------------------------------------------------------
# Regex patterns (v1.0 baseline)
# ---------------------------------------------------------------------------
RE_PROGRAM_ID = re.compile(
    r"^\s{0,11}PROGRAM-ID\.\s+([A-Z0-9][A-Z0-9-]*)",
    re.MULTILINE | re.IGNORECASE,
)
RE_PARAGRAPH = re.compile(
    r"^\s{0,11}([A-Z0-9][A-Z0-9-]*)\s*\.\s*(?:\*.*)?$",
    re.MULTILINE,
)
RE_SECTION = re.compile(
    r"^\s{0,11}([A-Z0-9][A-Z0-9-]*)\s+SECTION\s*\.\s*$",
    re.MULTILINE | re.IGNORECASE,
)
RE_DATA_01 = re.compile(
    r"^\s{0,11}01\s+([A-Z0-9][A-Z0-9-]*)",
    re.MULTILINE | re.IGNORECASE,
)
RE_CALL_LITERAL = re.compile(
    r"\bCALL\s+['\"]([A-Z0-9][A-Z0-9-]*)['\"] ",
    re.IGNORECASE,
)
RE_PERFORM = re.compile(r"\bPERFORM\s+([A-Z0-9][A-Z0-9-]*)", re.IGNORECASE)
RE_COPY    = re.compile(r"\bCOPY\s+([A-Z0-9][A-Z0-9-]*)",    re.IGNORECASE)
RE_SELECT  = re.compile(
    r"\bSELECT\s+([A-Z0-9][A-Z0-9-]*)\s+ASSIGN\s+TO\s+([A-Z0-9][A-Z0-9-]*)",
    re.IGNORECASE,
)
RE_ORGANIZATION = re.compile(r"\bORGANIZATION\s+IS\s+([A-Z]+)",  re.IGNORECASE)
RE_ACCESS       = re.compile(r"\bACCESS\s+MODE\s+IS\s+([A-Z]+)", re.IGNORECASE)
RE_EXEC_CICS    = re.compile(r"\bEXEC\s+CICS\b", re.IGNORECASE)
RE_EXEC_SQL     = re.compile(r"\bEXEC\s+SQL\b",  re.IGNORECASE)

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
# Helpers
# ---------------------------------------------------------------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
        out.append(line)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# v1.0 baseline extraction (preserved, noise filter applied)
# ---------------------------------------------------------------------------
def extract_structure_v10(cbl_path: Path) -> dict:
    raw  = cbl_path.read_text(encoding="utf-8", errors="replace")
    text = strip_cobol_comments(raw)

    m = RE_PROGRAM_ID.search(text)
    program_id = m.group(1).upper() if m else cbl_path.stem.upper()

    paragraphs: set[str] = set()
    for m in RE_PARAGRAPH.finditer(text):
        name = m.group(1).upper()
        if name in RESERVED_WORDS:  continue
        if name in PARAGRAPH_NOISE: continue
        if name.endswith("-DIVISION"): continue
        paragraphs.add(name)
    for m in RE_SECTION.finditer(text):
        paragraphs.discard(m.group(1).upper())

    data_items: set[str] = {
        m.group(1).upper()
        for m in RE_DATA_01.finditer(text)
        if m.group(1).upper() != "FILLER"
    }
    external_calls: set[str] = {
        m.group(1).upper() for m in RE_CALL_LITERAL.finditer(text)
    }
    internal_performs: set[str] = {
        m.group(1).upper()
        for m in RE_PERFORM.finditer(text)
        if m.group(1).upper() not in PERFORM_NON_TARGETS
    }
    copybooks: set[str] = {
        m.group(1).upper() for m in RE_COPY.finditer(text)
    }
    data_files: list[dict] = []
    for m in RE_SELECT.finditer(text):
        window = text[m.start():m.start() + 400]
        om = RE_ORGANIZATION.search(window)
        am = RE_ACCESS.search(window)
        data_files.append({
            "name":         m.group(1).upper(),
            "ddname":       m.group(2).upper(),
            "organization": om.group(1).upper() if om else None,
            "access":       am.group(1).upper() if am else None,
        })

    return {
        "program":              program_id,
        "paragraphs":           sorted(paragraphs),
        "data_items":           sorted(data_items),
        "external_calls":       sorted(external_calls),
        "internal_performs":    sorted(internal_performs),
        "copybooks_referenced": sorted(copybooks),
        "data_files":           data_files,
        "cics_present":         bool(RE_EXEC_CICS.search(text)),
        "sql_present":          bool(RE_EXEC_SQL.search(text)),
    }


# ---------------------------------------------------------------------------
# Optional REKT CFG stub (v1.0 compat)
# ---------------------------------------------------------------------------
def attach_cfg_stub(program: str) -> dict:
    candidates = list(REKT_DIR.glob(f"{program}.cbl.report*"))
    if not candidates:
        return {"source": None, "edges": None, "unresolved": None}
    report_dir = sorted(candidates)[0]
    edges = 0
    unresolved = 0
    for jf in report_dir.rglob("*.json"):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict):
            if isinstance(data.get("edges"), list):
                edges += len(data["edges"])
            if isinstance(data.get("unresolved"), list):
                unresolved += len(data["unresolved"])
    return {
        "source":     str(report_dir.relative_to(REPO_ROOT)).replace("\\", "/"),
        "edges":      edges or None,
        "unresolved": unresolved or None,
    }


# ---------------------------------------------------------------------------
# Gate logic
# ---------------------------------------------------------------------------
def compute_gate(struct: dict) -> tuple[int, str, list[str]]:
    reasons: list[str] = []
    if not struct["paragraphs"]:
        reasons.append("no_paragraphs")
    if not struct["program"]:
        reasons.append("no_program_id")
    status = "PASS" if not reasons else "WARN"
    rc = 0 if not reasons else 1
    return rc, status, reasons


# ---------------------------------------------------------------------------
# Per-program extraction
# ---------------------------------------------------------------------------
def extract_program(cbl_path: Path, gcv: str) -> dict:
    struct = extract_structure_v10(cbl_path)
    cfg    = attach_cfg_stub(struct["program"])
    rc, status, reasons = compute_gate(struct)

    raw = cbl_path.read_text(encoding="utf-8", errors="replace")
    sem = enrich(
        program_name=struct["program"],
        raw_cobol=raw,
        preprocessed_cobol=None,
        rekt_json=None,
        base_facts=struct,
        rekt_dir=REKT_DIR if REKT_DIR.exists() else None,
    )

    return {
        "schema_version":       SCHEMA_VERSION,
        "program":              struct["program"],
        "source_file":          str(cbl_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "extracted_at":         now_iso(),
        "gnucobol_version":     gcv,
        "gate_rc":              rc,
        "gate_status":          status,
        "gate_reasons":         reasons,
        "cics_present":         struct["cics_present"],
        "sql_present":          struct["sql_present"],
        "paragraphs":           struct["paragraphs"],
        "data_items":           struct["data_items"],
        "external_calls":       struct["external_calls"],
        "internal_performs":    struct["internal_performs"],
        "data_files":           struct["data_files"],
        "copybooks_referenced": struct["copybooks_referenced"],
        "cfg":                  cfg,
        # v1.1 semantic enrichment
        "paragraphs_defined":    sem["paragraphs_defined"],
        "paragraphs_referenced": sem["paragraphs_referenced"],
        "paragraph_actions":     sem["paragraph_actions"],
        "file_lineage":          sem["file_lineage"],
        "file_operations":       sem["file_operations"],
        "control_flow":          sem["control_flow"],
        "cics":                  sem["cics"],
    }


# ---------------------------------------------------------------------------
# Program selection + main
# ---------------------------------------------------------------------------
def select_programs(arg: str | None) -> list[Path]:
    if not RAW_CBL_DIR.exists():
        print(f"ERROR: {RAW_CBL_DIR} does not exist.", file=sys.stderr)
        sys.exit(2)
    if arg:
        stem = arg.upper().removesuffix(".CBL")
        for candidate in [
            RAW_CBL_DIR / f"{stem}.cbl",
            RAW_CBL_DIR / f"{stem.lower()}.cbl",
        ]:
            if candidate.exists():
                return [candidate]
        print(f"ERROR: No .cbl file found for '{arg}' in {RAW_CBL_DIR}", file=sys.stderr)
        sys.exit(2)
    programs = sorted(RAW_CBL_DIR.glob("*.cbl"))
    if not programs:
        print(f"No .cbl files found in {RAW_CBL_DIR}", file=sys.stderr)
        sys.exit(2)
    return programs


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    FACTS_DIR.mkdir(parents=True, exist_ok=True)
    gcv      = gnucobol_version()
    programs = select_programs(arg)

    print("HermesCOBOL extract_facts  (schema v1.1)")
    print(f"GnuCOBOL : {gcv}")
    print(f"Programs : {len(programs)}")
    print(f"Facts dir: {FACTS_DIR}")
    print()

    any_fail = False
    for cbl in programs:
        try:
            facts = extract_program(cbl, gcv)
        except Exception as e:
            import traceback
            print(f"  [ERROR] {cbl.stem:22s} {e}")
            traceback.print_exc()
            any_fail = True
            continue

        out_path = FACTS_DIR / f"{facts['program']}.json"
        out_path.write_text(json.dumps(facts, indent=2), encoding="utf-8")

        cics    = "C" if facts["cics_present"] else "-"
        sql     = "S" if facts["sql_present"]  else "-"
        n_edges = len(facts["control_flow"].get("edges", []))
        cfg_src = facts["control_flow"].get("cfg_source", "?")
        print(
            f"  [{facts['gate_status']:4s}] {facts['program']:22s}  "
            f"cics={cics} sql={sql}  "
            f"paras={len(facts['paragraphs']):3d}  "
            f"calls={len(facts['external_calls']):2d}  "
            f"files={len(facts['data_files']):2d}  "
            f"edges={n_edges:3d}  cfg={cfg_src}"
        )
        if facts["gate_status"] == "WARN":
            print(f"           reasons: {facts['gate_reasons']}")
            any_fail = True

    print()
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())

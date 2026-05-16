#!/usr/bin/env python3
"""
assemble_canonical.py — Deterministic canonical IR assembler (Stage 5-G).

Merges:
  - data/facts/<PROG>.json
  - data/cfg/<PROG>.json
  - validation/pass1/<PROG>_annotations.json
  - data/fallthrough/<PROG>.json

into data/canonical/<PROG>.canonical.json

LLM-FREE. Pure deterministic merge + CICS graceful degradation.
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
    CFG_DIR,
    FALLTHROUGH_DIR,
    PASS1_ANNOTATIONS_DIR,
    VALID_DIR,
    REPORTS_DIR,
    SCHEMA_VERSION,
)

CANONICAL_DIR = REPO_ROOT / "data" / "canonical"

# Preprocessed location (used to detect Mode A availability)
PREPROC_DIR = REPO_ROOT / "data" / "preprocessed"
RECONSTRUCTED_CBL_DIR = VALID_DIR / "reconstructed" / "cbl"


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _has_preprocessed(prog: str) -> bool:
    """Check if a preprocessed version exists (Mode A success)."""
    candidates = [
        PREPROC_DIR / f"{prog}.pre.cbl",
        PREPROC_DIR / f"{prog}.cbl",
        RECONSTRUCTED_CBL_DIR / f"{prog}.pre.cbl",
    ]
    return any(p.exists() for p in candidates)


def _merge_paragraphs(
    facts: dict[str, Any],
    cfg: dict[str, Any],
    annotations: list[dict[str, Any]],
    fallthrough: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Build enriched paragraph-level IR.
    Preserves merge strategy from the reference assembler.
    """
    # Base paragraphs from facts (order-preserving)
    para_order: list[str] = facts.get("paragraphs", []) or []
    para_map: dict[str, dict[str, Any]] = {p: {"name": p} for p in para_order}

    # Enrich from fallthrough (terminator + falls_through_to)
    for p in fallthrough.get("paragraphs", []) or []:
        name = p.get("paragraph")
        if name in para_map:
            para_map[name].update(
                {
                    "terminator": p.get("terminator"),
                    "falls_through_to": p.get("falls_through_to"),
                    "last_verb": p.get("last_verb"),
                }
            )

    # Enrich from CFG (performs, goto_targets, reachable)
    for p in cfg.get("paragraphs", []) or []:
        name = p.get("name")
        if name in para_map:
            para_map[name].update(
                {
                    "performs": p.get("performs", []),
                    "goto_targets": p.get("goto_targets", []),
                    "reachable": p.get("reachable", True),
                }
            )

    # Attach pass1 annotation summary (last verb context, branch info)
    # Group annotations by paragraph for convenience
    ann_by_para: dict[str, list[dict]] = {}
    for ann in annotations or []:
        p = ann.get("paragraph")
        if p:
            ann_by_para.setdefault(p, []).append(ann)

    for name, anns in ann_by_para.items():
        if name in para_map:
            last_ann = anns[-1] if anns else {}
            para_map[name].update(
                {
                    "last_raw": last_ann.get("raw"),
                    "cfg_branch_context": last_ann.get("cfg_branch_context"),
                    "is_cics_branch": last_ann.get("is_cics_branch", False),
                }
            )

    # Final ordered list
    enriched = []
    for name in para_order:
        p = para_map.get(name, {"name": name})
        # Ensure stable keys
        p.setdefault("terminator", "implicit")
        p.setdefault("falls_through_to", None)
        p.setdefault("performs", [])
        p.setdefault("goto_targets", [])
        enriched.append(p)

    return enriched


def assemble_program(prog: str) -> dict[str, Any]:
    """Assemble canonical IR for one program."""
    facts = _load_json(FACTS_DIR / f"{prog}.json") or {}
    cfg = _load_json(CFG_DIR / f"{prog}.json") or {}
    annotations = _load_json(PASS1_ANNOTATIONS_DIR / f"{prog}_annotations.json") or []
    fallthrough = _load_json(FALLTHROUGH_DIR / f"{prog}.json") or {}

    preprocess_available = _has_preprocessed(prog)

    # CICS graceful handling: we still produce the canonical record
    # even if preprocess is unavailable (17 CICS programs).
    canonical = {
        "program": prog,
        "schema_version": "1.4",  # canonical IR schema for Stage 5-G
        "source_file": str(RAW_CBL_DIR / f"{prog}.cbl"),
        "preprocess_available": preprocess_available,
        "cics_present": facts.get("cics_present", False),
        "sql_present": facts.get("sql_present", False),
        "paragraphs": _merge_paragraphs(facts, cfg, annotations, fallthrough),
        # Preserve key top-level collections from the various extractors
        "data_files": facts.get("data_files", []),
        "external_calls": facts.get("external_calls", []),
        "copybooks_referenced": facts.get("copybooks_referenced", []),
        "cfg_paragraphs": cfg.get("paragraphs", []),
        "cics_commands": cfg.get("cics_commands", []),
        "cics_branches": sum(1 for a in annotations if a.get("is_cics_branch")),
        "cfg_edges_resolved": sum(
            1 for a in annotations
            if a.get("cfg_perform_target") or a.get("cfg_goto_target")
        ),
    }

    return canonical


def run_single(prog: str) -> None:
    CANONICAL_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CANONICAL_DIR / f"{prog}.canonical.json"

    data = assemble_program(prog)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    status = "CICS (no preprocess)" if not data["preprocess_available"] else "OK"
    print(f"[ok] {prog}  paragraphs={len(data['paragraphs'])}  ({status})")


def run_all() -> None:
    CANONICAL_DIR.mkdir(parents=True, exist_ok=True)

    cbl_files = sorted(RAW_CBL_DIR.glob("*.cbl")) + sorted(RAW_CBL_DIR.glob("*.CBL"))
    seen: set[str] = set()
    progs = []
    for f in cbl_files:
        stem = f.stem.upper()
        if stem not in seen:
            seen.add(stem)
            progs.append(stem)

    print(f"[corpus] assembling canonical IR for {len(progs)} programs...")

    summary = []
    for prog in progs:
        try:
            data = assemble_program(prog)
            out_path = CANONICAL_DIR / f"{prog}.canonical.json"
            out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

            summary.append(
                {
                    "program": prog,
                    "paragraphs": len(data["paragraphs"]),
                    "preprocess_available": data["preprocess_available"],
                    "cics_present": data["cics_present"],
                }
            )
            status = "CICS" if not data["preprocess_available"] else "OK"
            print(f"[ok] {prog}  paragraphs={len(data['paragraphs'])}  ({status})")
        except Exception as exc:
            print(f"[ERROR] {prog}: {exc}")

    # Write summary
    summary_path = CANONICAL_DIR / "_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    cics_count = sum(1 for s in summary if not s["preprocess_available"])
    print(f"\n[ok] {len(summary)}/31 complete  (CICS without preprocess: {cics_count})")
    print(f"      canonical IR written to {CANONICAL_DIR}/")


def main() -> int:
    ap = argparse.ArgumentParser(description="Canonical IR assembler (Stage 5-G)")
    ap.add_argument(
        "program",
        nargs="?",
        help="Program name (e.g. CBACT01C). If omitted, process all 31.",
    )
    args = ap.parse_args()

    if args.program:
        prog = args.program.upper()
        if not (RAW_CBL_DIR / f"{prog}.cbl").exists():
            # Try case-insensitive match
            matches = [p.stem.upper() for p in RAW_CBL_DIR.glob("*.cbl")]
            if prog not in matches:
                print(f"ERROR: unknown program {prog}", file=sys.stderr)
                return 2
        run_single(prog)
    else:
        run_all()

    return 0


if __name__ == "__main__":
    sys.exit(main())

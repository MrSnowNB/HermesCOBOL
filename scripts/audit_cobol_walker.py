#!/usr/bin/env python3
"""
audit_cobol_walker.py — Generate and optionally validate the CobolWalker baseline.

Walks all 31 programs with both include_dead_code=False and True.
Produces a deterministic JSON summary used for Gate 10 regression.

Output: validation/walker-baseline.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.cobol_program_dict import CobolProgramDict
from scripts.cobol_walker import CobolWalker

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DIR = REPO_ROOT / "data" / "canonical"
BASELINE_PATH = REPO_ROOT / "validation" / "walker-baseline.json"


def build_baseline() -> list[dict[str, Any]]:
    """Walk every program and collect the required summary fields."""
    results: list[dict[str, Any]] = []

    for canon_path in sorted(CANONICAL_DIR.glob("*.canonical.json")):
        prog_name = canon_path.stem.replace(".canonical", "")
        prog = CobolProgramDict(prog_name)
        walker = CobolWalker(prog)

        live = list(walker.walk(include_dead_code=False))
        full = list(walker.walk(include_dead_code=True))

        results.append(
            {
                "program": prog_name,
                "entry_paragraph": prog.entry_paragraph,
                "live_count": len(live),
                "full_count": len(full),
                "first_five": live[:5],
                "last_three": full[-3:] if full else [],
            }
        )

    return results


def write_baseline(data: list[dict[str, Any]]) -> None:
    """Write the baseline JSON (pretty-printed for readability)."""
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Baseline written to {BASELINE_PATH.relative_to(REPO_ROOT)}")


def main() -> None:
    data = build_baseline()
    write_baseline(data)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
cobol_program_dict.py — Unified, validated access layer over the Canonical IR.

This class is the single source of truth for a COBOL program after all
Stage 5-H extraction and cleaning work.

Design rules (per SPEC):
- data/canonical/<PROG>.canonical.json is the ONLY required file.
- All other sources (byte_layouts, data_flow, cfg) are optional enrichment.
- Missing optional files must result in [] or None — never raise.
- The class must be fully functional with only the canonical IR.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class CobolProgramDict:
    """
    Clean, validated, dict-like view of a COBOL program.

    Primary (required) source : data/canonical/<PROG>.canonical.json
    Optional enrichment       : byte_layouts, data_flow, cfg

    Example:
        prog = CobolProgramDict("CBACT01C")
        print(len(prog.paragraphs))
        print(prog.is_cics)
        p = prog.paragraph("0000-MAIN")
    """

    def __init__(self, program: str, base_dir: Path | None = None):
        self.name: str = program.upper()
        self._base_dir = base_dir or Path(__file__).resolve().parents[1] / "data"

        # === REQUIRED: Canonical IR ===
        canonical_path = self._base_dir / "canonical" / f"{self.name}.canonical.json"
        if not canonical_path.exists():
            raise FileNotFoundError(
                f"Required canonical IR not found: {canonical_path}"
            )

        self._canonical: dict[str, Any] = json.loads(
            canonical_path.read_text(encoding="utf-8")
        )

        # === OPTIONAL ENRICHMENT (graceful degradation) ===
        self._byte_layouts = self._safe_load("byte_layouts")
        self._data_flow = self._safe_load("data_flow")
        self._cfg = self._safe_load("cfg")

        # === DERIVED VIEWS (built from canonical primarily) ===
        self._paragraphs: dict[str, dict] = {
            p["name"]: p for p in self._canonical.get("paragraphs", [])
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _safe_load(self, subdir: str) -> dict[str, Any] | None:
        """Load an optional enrichment file. Returns None on any failure."""
        path = self._base_dir / subdir / f"{self.name}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Core Properties (always available from canonical)
    # ------------------------------------------------------------------

    @property
    def is_cics(self) -> bool:
        return bool(self._canonical.get("cics_present", False))

    @property
    def paragraphs(self) -> dict[str, dict]:
        """All paragraphs with their full enriched records from canonical IR."""
        return self._paragraphs

    def paragraph(self, name: str) -> dict:
        """Return a single paragraph record (raises KeyError if not found)."""
        name = name.upper()
        if name not in self._paragraphs:
            raise KeyError(f"Paragraph not found: {name}")
        return self._paragraphs[name]

    @property
    def entry_paragraph(self) -> str:
        """First paragraph from the CFG root (the actual driver used for reachability computation).

        Prefers the first paragraph listed in cfg_paragraphs when present.
        Falls back to the first paragraph in canonical source order if cfg_paragraphs
        is empty or missing.
        """
        cfg_paras = self._canonical.get("cfg_paragraphs", [])
        if cfg_paras:
            first = cfg_paras[0].get("name")
            if first:
                return first
        # Fallback to source order
        paras = self._canonical.get("paragraphs", [])
        if not paras:
            return ""
        return paras[0]["name"]

    @property
    def reachable_paragraphs(self) -> list[str]:
        """Paragraphs marked reachable=True in the canonical IR."""
        return [p["name"] for p in self._canonical.get("paragraphs", []) if p.get("reachable", True)]

    @property
    def dead_code_paragraphs(self) -> list[str]:
        """Paragraphs marked reachable=False."""
        return [p["name"] for p in self._canonical.get("paragraphs", []) if not p.get("reachable", True)]

    # ------------------------------------------------------------------
    # Optional Enrichment Properties (return [] or None if missing)
    # ------------------------------------------------------------------

    @property
    def data_items(self) -> list[dict]:
        """Byte layout / data item information (from byte_layouts if available)."""
        if self._byte_layouts is None:
            return []
        return self._byte_layouts.get("data_items", [])

    @property
    def external_calls(self) -> list[str]:
        """External CALL targets from the canonical IR (always present)."""
        return self._canonical.get("external_calls", [])

    @property
    def copybooks_referenced(self) -> list[str]:
        """Copybooks referenced by the program (from canonical IR)."""
        return self._canonical.get("copybooks_referenced", [])

    @property
    def cfg_paragraphs(self) -> list[dict]:
        """Raw paragraph records from the CFG source (optional)."""
        if self._cfg is None:
            return []
        return self._cfg.get("paragraphs", [])

    # ------------------------------------------------------------------
    # Convenience / Debug
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<CobolProgramDict {self.name} paragraphs={len(self.paragraphs)} cics={self.is_cics}>"

    def __len__(self) -> int:
        return len(self.paragraphs)


# ----------------------------------------------------------------------
# Quick smoke test (run directly for manual verification)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    prog = CobolProgramDict("CBACT01C")
    print(prog)
    print("Entry:", prog.entry_paragraph)
    print("Reachable count:", len(prog.reachable_paragraphs))
    print("Dead code count:", len(prog.dead_code_paragraphs))
    print("Data items (optional):", len(prog.data_items))
    print("External calls:", prog.external_calls)
    print("OK")
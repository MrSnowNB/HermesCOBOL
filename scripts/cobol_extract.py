#!/usr/bin/env python3
"""
cobol_extract.py — Safe, hallucination-resistant COBOL extraction tool (v1)

Only returns data that exists in the HermesCOBOL artifacts.
Explicitly reports missing/incomplete sections.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Set


def _load_json(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None



def _walk_paragraphs(paragraphs: List[Dict], include_dead_code: bool = False) -> List[str]:
    """Deterministic DFS pre-order walk using performs + falls_through_to."""
    if not paragraphs:
        return []

    # Build lookup
    para_map = {p["name"]: p for p in paragraphs}
    
    # Find entry point (first reachable or first paragraph)
    entry = None
    for p in paragraphs:
        if p.get("reachable", True):
            entry = p["name"]
            break
    if entry is None:
        entry = paragraphs[0]["name"]

    visited: Set[str] = set()
    order: List[str] = []

    def dfs(name: str):
        if name in visited or name not in para_map:
            return
        visited.add(name)
        order.append(name)
        
        p = para_map[name]
        
        # Follow performs in order
        for target in p.get("performs", []):
            dfs(target)
        
        # Then fallthrough
        fall = p.get("falls_through_to")
        if fall:
            dfs(fall)

    dfs(entry)

    # Add dead code if requested
    if include_dead_code:
        for p in paragraphs:
            if p["name"] not in visited:
                order.append(p["name"])

    return order


def extract(
    program: str,
    mode: str = "facts",
    strict: bool = False,
    strict_data: bool = False,
    base_dir: Path | None = None,
) -> Dict[str, Any]:
    """
    Extract verified COBOL data. Never hallucinates missing information.
    """
    program = program.upper()
    base = base_dir or (Path(__file__).resolve().parents[1] / "data")

    result = {
        "program": program,
        "mode": mode,
        "source_artifacts": [],
        "completeness": {},
        "data": None,
        "warnings": [],
        "refusal_reason": None,
    }

    facts = _load_json(base / "facts" / f"{program}.json") or {}
    canonical = _load_json(base / "canonical" / f"{program}.canonical.json")
    data_flow = _load_json(base / "data_flow" / f"{program}.json")

    missing = []
    if canonical is None:
        missing.append("canonical")
    if data_flow is None:
        missing.append("data_flow")

    is_cics = facts.get("cics_present", False)


    # Strict data mode handling
    if strict_data:
        result["strict_data"] = True
        critical_missing = [m for m in missing if m in ("canonical", "data_flow")]
        if critical_missing:
            result["refusal_reason"] = f"strict_data=True: missing critical artifacts {critical_missing}"
            result["data"] = None
            return result
    else:
        result["strict_data"] = False
    result["completeness"] = {
        "paragraphs": "complete" if canonical else "missing",
        "data_items": "partial" if canonical else "missing",
        "data_flow": "complete" if data_flow else "missing",
        "cics_details": "partial" if is_cics else "complete",
        "missing_sections": missing,
    }

    if mode == "facts":
        result["source_artifacts"] = ["facts"]
        result["data"] = {
            "paragraphs": facts.get("paragraphs", []),
            "data_items": facts.get("data_items", []),
            "copybooks_referenced": facts.get("copybooks_referenced", []),
            "data_files": facts.get("data_files", []),
            "cics_present": is_cics,
            "external_calls": facts.get("external_calls", []),
        }
        return result

    if mode == "structure":
        if canonical is None:
            result["refusal_reason"] = "canonical IR required for structure mode"
            return result
        result["source_artifacts"] = ["canonical"]
        result["data"] = {
            "paragraphs": canonical.get("paragraphs", []),
            "cics_present": canonical.get("cics_present", False),
        }
        return result

    if mode == "walk":
        if canonical is None:
            result["refusal_reason"] = "canonical IR required for walk mode"
            return result
        paras = canonical.get("paragraphs", [])
        execution_order = _walk_paragraphs(paras, include_dead_code=False)
        result["source_artifacts"] = ["canonical"]
        result["data"] = {
            "execution_order": execution_order,
            "total_paragraphs": len(paras),
            "entry_paragraph": execution_order[0] if execution_order else None,
        }
        return result

    if mode == "data_flow":
        if data_flow is None:
            result["refusal_reason"] = "data_flow artifacts not available"
            return result
        result["source_artifacts"] = ["data_flow"]
        result["data"] = data_flow
        return result

    if mode == "full":
        result["source_artifacts"] = ["facts", "canonical"]
        result["data"] = {
            "facts": facts,
            "canonical_available": canonical is not None,
        }
        return result

    result["refusal_reason"] = f"unknown mode: {mode}"
    return result


if __name__ == "__main__":
    import sys
    prog = sys.argv[1] if len(sys.argv) > 1 else "COACTUPC"
    mode = sys.argv[2] if len(sys.argv) > 2 else "facts"
    print(json.dumps(extract(prog, mode=mode), indent=2, default=str))

#!/usr/bin/env python3
"""
schema.py — Canonical output schema for structured_facts.json

This module documents and validates the data contract produced by
extract_facts.py. It is informational; no external libraries required.

Schema version: 1.0
"""

# ---------------------------------------------------------------------------
# structured_facts.json schema (annotated)
# ---------------------------------------------------------------------------
#
# {
#   "program":              str,   # program name (uppercase, no extension)
#   "source_lines":         int,   # lines after cobc -E expansion
#   "rekt_available":       bool,  # whether REKT CFG JSON was found
#   "rekt_node_count":      int,   # total nodes in REKT CFG
#   "rekt_edge_count":      int,   # total edges in REKT CFG
#   "para_count":           int,   # number of PROCEDURE DIVISION paragraphs
#   "rekt_sentence_total":  int,   # total REKT CODE_VERTEX sentences (full count)
#
#   "paragraphs": [
#     {
#       "name":        str,         # paragraph label
#       "line_start":  int,         # 1-based line in expanded source
#       "line_end":    int,
#       "performs":    [{"target": str, "thru"?: str}],
#       "gotos":       [str],
#       "terminator":  str          # STOP RUN | GOBACK | EXIT PROGRAM |
#                                   # EXEC CICS RETURN | implicit
#     }
#   ],
#
#   "data": {
#     "select_files":        [{"logical": str, "ddname": str}],
#     "fd_names":            [str],
#     "working_storage_01s": [{"name": str, "pic": str|null}]
#   },
#
#   "external_calls":  [str],       # programs named in CALL statements
#   "cics_verbs":      [{"verb": str, "text": str}],
#   "rekt_sentences":  [           # capped at MAX_REKT_SENTENCES
#     {"id": str, "type": str, "text": str}
#   ]
# }

REQUIRED_TOP_LEVEL_KEYS = [
    "program", "source_lines", "rekt_available", "rekt_node_count",
    "rekt_edge_count", "para_count", "rekt_sentence_total",
    "paragraphs", "data", "external_calls", "cics_verbs", "rekt_sentences",
]

def validate(facts: dict) -> list:
    """Return list of validation errors. Empty list = valid."""
    errors = []
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in facts:
            errors.append(f"Missing key: {key}")
    if "data" in facts:
        for sub in ("select_files", "fd_names", "working_storage_01s"):
            if sub not in facts["data"]:
                errors.append(f"Missing data sub-key: {sub}")
    return errors


if __name__ == "__main__":
    import json, sys
    from pathlib import Path
    facts_dir = Path("data/facts")
    if not facts_dir.exists():
        print("data/facts/ not found — run Stage 3 first."); sys.exit(1)
    all_ok = True
    for f in sorted(facts_dir.glob("*.json")):
        facts = json.loads(f.read_text())
        errs  = validate(facts)
        if errs:
            print(f"  FAIL {f.name}: {errs}")
            all_ok = False
        else:
            print(f"  OK   {f.name}")
    sys.exit(0 if all_ok else 1)

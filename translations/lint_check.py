"""
lint_check.py
Pre-commit / test guard to prevent stale global state imports.
"""

import glob


def check_no_global_state_import():
    """Returns list of violations (file:line) or empty list if clean."""
    violations = []
    for filepath in glob.glob("coactupc_*.py"):
        with open(filepath, encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                if "from state import state" in line:
                    violations.append(f"{filepath}:{i}")
    return violations

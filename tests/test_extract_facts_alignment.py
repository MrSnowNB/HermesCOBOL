"""Regression test for 3.4 paragraph-detection scoping fix.
Asserts that facts['paragraphs'] (the simple list from extract_structure_v10
with _slice_procedure_division scoping) matches the names in
facts['paragraphs_defined'] (the rich list from enrich(), now reconciled).
If a future change re-introduces the +2 drift (PROGRAM-ID continuation,
DATE-WRITTEN value, DATE-COMPILED value being miscounted as paragraphs),
this test will catch it before commit. Locks in the fix that closed the
remaining 2 of the original 3 WARN cases that survived a7a1688
(Step 2-fix-v2).
"""
import json
import subprocess
import sys
from pathlib import Path
import pytest
REPO_ROOT = Path(__file__).resolve().parent.parent
FACTS_DIR = REPO_ROOT / "data" / "facts"
EXTRACT_SCRIPT = REPO_ROOT / "scripts" / "extract_facts.py"
@pytest.fixture(scope="session", autouse=True)
def regenerate_facts():
    """Regenerate data/facts/ from source once per test session.
    Removes the hazard of the parametrized tests running against stale
    on-disk JSON. extract_facts.py is deterministic for a fixed corpus
    and GnuCOBOL version, so this is safe to run unconditionally.
    """
    result = subprocess.run(
        [sys.executable, str(EXTRACT_SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"extract_facts.py failed to regenerate facts:\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    yield
def _corpus_programs():
    """Collect program names from data/facts/ at collection time.
    Returns sorted list of program stems (e.g. 'COACTUPC', 'COCRDLIC', ...).
    Note: collection happens before the session fixture runs, so this
    relies on data/facts/ existing from a prior pipeline run. If the
    directory is empty, the parametrize list is empty and the test is
    a no-op (which would itself be a failure signal).
    """
    if not FACTS_DIR.exists():
        return []
    return sorted(p.stem for p in FACTS_DIR.glob("*.json"))
@pytest.mark.parametrize("program", _corpus_programs())
def test_paragraphs_match_paragraphs_defined(program):
    """facts['paragraphs'] set-equals {p['name'] for p in paragraphs_defined}.
    This is the canonical invariant after the 3.4 scoping fix:
    - paragraphs (simple list) is produced by extract_structure_v10 with
      _slice_procedure_division(text) scoping.
    - paragraphs_defined (rich list) is produced by enrich() in
      hermes_v11_combined_extractor.py, then reconciled in extract_program
      against the authoritative simple list.
    - Both lists must contain the same paragraph names.
    """
    facts = json.loads((FACTS_DIR / f"{program}.json").read_text())
    simple_set = set(facts.get("paragraphs", []))
    rich_names = {p["name"].upper() for p in facts.get("paragraphs_defined", [])}
    extras_in_simple = simple_set - rich_names
    extras_in_rich = rich_names - simple_set
    assert simple_set == rich_names, (
        f"{program}: simple-only={sorted(extras_in_simple)}, "
        f"rich-only={sorted(extras_in_rich)}"
    )
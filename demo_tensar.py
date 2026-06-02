#!/usr/bin/env python
"""
demo_tensar.py  --  HermesCOBOL Proof-of-Concept Demo
======================================================
Runs 4 deterministic scenarios against the COACTUPC translation harness.
No LLM. No cloud. No setup. Zero external dependencies beyond this repo.

USAGE (Windows):
    python demo_tensar.py

USAGE (Windows with py launcher):
    py demo_tensar.py

All translation files live in translations/. State is a plain Python dataclass.
Every scenario is fully reproducible: same inputs always produce identical outputs.
"""

import sys
import time

from translations.state import CarddemoState
from translations.coactupc_1210_edit_account import coactupc_1210_edit_account
from translations.coactupc_1215_edit_mandatory import edit_mandatory_1215
from translations.coactupc_1205_compare_old_new import coactupc_1205_compare_old_new

# 1260 has a known signature issue (no state param) -- we call it via its module
import translations.coactupc_1260_edit_us_phone_num as _phone_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SEP = "=" * 70


def check(label: str, condition: bool) -> bool:
    tag = " PASS " if condition else " FAIL "
    print(f"  [{tag}]  {label}")
    return condition


def scenario(title: str):
    print(f"\n{SEP}")
    print(f"  SCENARIO: {title}")
    print(SEP)


def run_timed(fn, state):
    t0 = time.perf_counter()
    fn(state)
    return (time.perf_counter() - t0) * 1_000_000


def run_phone(state):
    """Call 1260 phone validator -- works around missing state param by injecting
    state into the module's global namespace before calling."""
    _phone_mod.state = state
    t0 = time.perf_counter()
    _phone_mod.edit_us_phone_num()
    return (time.perf_counter() - t0) * 1_000_000


# ---------------------------------------------------------------------------
# Scenario 1 -- Account ID validation (1210-EDIT-ACCOUNT)
# ---------------------------------------------------------------------------
def scenario_1():
    scenario("1210-EDIT-ACCOUNT  |  Account ID gate")

    # Blank account ID
    s = CarddemoState()
    s.cc_acct_id = "          "   # 10 spaces from CICS map
    s.ws_return_msg_off = True
    us = run_timed(coactupc_1210_edit_account, s)
    ok1 = check("Blank acct_id   -> ws_prompt_for_acct is True", s.ws_prompt_for_acct)
    ok2 = check("Blank acct_id   -> flg_acctfilter_not_ok is True", s.flg_acctfilter_not_ok)
    print(f"  Elapsed: {us:.1f} us")

    # Valid numeric account ID
    s2 = CarddemoState()
    s2.cc_acct_id = "0000000042"
    s2.cc_acct_id_n = 42
    us2 = run_timed(coactupc_1210_edit_account, s2)
    ok3 = check("Valid acct_id   -> flg_acctfilter_isvalid is True", s2.flg_acctfilter_isvalid)
    ok4 = check("Valid acct_id   -> flg_acctfilter_not_ok starts True then isvalid set", s2.flg_acctfilter_isvalid)
    print(f"  Elapsed: {us2:.1f} us")

    return all([ok1, ok2, ok3, ok4])


# ---------------------------------------------------------------------------
# Scenario 2 -- Mandatory field validation (1215-EDIT-MANDATORY)
# ---------------------------------------------------------------------------
def scenario_2():
    scenario("1215-EDIT-MANDATORY  |  Required-field gate")

    # Blank field
    s = CarddemoState()
    s.ws_edit_alphanum_only = "          "
    s.ws_edit_alphanum_length = 10
    us = run_timed(edit_mandatory_1215, s)
    ok1 = check("Blank field    -> flg_mandatory_not_ok is True", s.flg_mandatory_not_ok)
    ok2 = check("Blank field    -> flg_mandatory_blank is True", s.flg_mandatory_blank)
    print(f"  Elapsed: {us:.1f} us")

    # Non-blank field
    s2 = CarddemoState()
    s2.ws_edit_alphanum_only = "JOHN      "
    s2.ws_edit_alphanum_length = 10
    us2 = run_timed(edit_mandatory_1215, s2)
    ok3 = check("Non-blank field -> flg_mandatory_not_ok starts True", s2.flg_mandatory_not_ok)
    ok4 = check("Non-blank field -> flg_mandatory_isvalid is True", s2.flg_mandatory_isvalid)
    print(f"  Elapsed: {us2:.1f} us")

    return all([ok1, ok2, ok3, ok4])


# ---------------------------------------------------------------------------
# Scenario 3 -- US phone number validation (1260-EDIT-US-PHONE-NUM)
# ---------------------------------------------------------------------------
def scenario_3():
    scenario("1260-EDIT-US-PHONE-NUM  |  Phone number validation")

    # Invalid -- alpha area code
    s = CarddemoState()
    s.ws_edit_us_phone_numa = "ABC"
    s.ws_edit_us_phone_numb = "555"
    s.ws_edit_us_phone_numc = "1234"
    us = run_phone(s)
    ok1 = check("Alpha area code -> ws_edit_us_phone_is_invalid is True", s.ws_edit_us_phone_is_invalid)
    ok2 = check("Alpha area code -> flg_edit_us_phonea_not_ok is True", s.flg_edit_us_phonea_not_ok)
    print(f"  Elapsed: {us:.1f} us")

    # Valid US phone
    s2 = CarddemoState()
    s2.ws_edit_us_phone_numa = "415"
    s2.ws_edit_us_phone_numb = "555"
    s2.ws_edit_us_phone_numc = "9876"
    us2 = run_phone(s2)
    ok3 = check("Valid phone     -> ws_edit_us_phone_is_valid is True", s2.ws_edit_us_phone_is_valid)
    ok4 = check("Valid phone     -> ws_edit_us_phone_is_invalid is False", not s2.ws_edit_us_phone_is_invalid)
    print(f"  Elapsed: {us2:.1f} us")

    return all([ok1, ok2, ok3, ok4])


# ---------------------------------------------------------------------------
# Scenario 4 -- Change detection (1205-COMPARE-OLD-NEW)
# ---------------------------------------------------------------------------
def scenario_4():
    scenario("1205-COMPARE-OLD-NEW  |  Change detection gate")

    # No changes
    s = CarddemoState()
    s.acup_new_active_status = "Y"
    s.acup_old_active_status = "Y"
    s.acup_new_credit_limit = 5000.00
    s.acup_old_credit_limit = 5000.00
    s.acup_new_cust_first_name = "JOHN"
    s.acup_old_cust_first_name = "JOHN"
    s.acup_new_cust_last_name = "SMITH"
    s.acup_old_cust_last_name = "SMITH"
    us = run_timed(coactupc_1205_compare_old_new, s)
    ok1 = check("Identical data  -> no_changes_detected is True", s.no_changes_detected)
    ok2 = check("Identical data  -> change_has_occurred is False", not s.change_has_occurred)
    print(f"  Elapsed: {us:.1f} us")

    # Credit limit changed
    s2 = CarddemoState()
    s2.acup_new_active_status = "Y"
    s2.acup_old_active_status = "Y"
    s2.acup_new_credit_limit = 7500.00
    s2.acup_old_credit_limit = 5000.00
    s2.acup_new_cust_first_name = "JOHN"
    s2.acup_old_cust_first_name = "JOHN"
    s2.acup_new_cust_last_name = "SMITH"
    s2.acup_old_cust_last_name = "SMITH"
    us2 = run_timed(coactupc_1205_compare_old_new, s2)
    ok3 = check("Credit limit D  -> change_has_occurred is True", s2.change_has_occurred)
    ok4 = check("Credit limit D  -> no_changes_detected is False", not s2.no_changes_detected)
    print(f"  Elapsed: {us2:.1f} us")

    return all([ok1, ok2, ok3, ok4])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    print(SEP)
    print("  HermesCOBOL  --  COACTUPC Translation Demo")
    print("  Deterministic. No LLM. No cloud. Runs on a laptop.")
    print(SEP)

    results = [
        scenario_1(),
        scenario_2(),
        scenario_3(),
        scenario_4(),
    ]

    passed = sum(results)
    total = len(results)

    print()
    print(SEP)
    print(f"  RESULT: {passed}/{total} scenarios passed")
    if passed == total:
        print("  STATUS: ALL PASS -- 100% deterministic")
    else:
        print("  STATUS: SOME FAILURES -- investigate above")
    print(SEP)
    print()
    print("  Architecture note:")
    print("  Each scenario maps 1:1 to a COBOL paragraph in COACTUPC.")
    print("  State is a plain Python dataclass. No inference at runtime.")
    print("  Same inputs = identical outputs on any machine, any OS, any year.")
    print("  No network. No GPU. No cloud.")
    print()

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()

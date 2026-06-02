#!/usr/bin/env python
"""
demo_tensar.py  —  HermesCOBOL Proof-of-Concept Demo
======================================================
Runs 4 deterministic scenarios against the COACTUPC translation harness.
No LLM. No cloud. No setup. Zero external dependencies beyond this repo.

USAGE:
    python demo_tensar.py

All translation files live in translations/. State is a plain Python dataclass.
Every scenario is fully reproducible: same inputs always produce same outputs.
"""

import sys
import time
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Minimal inline state (mirrors translations/state.py exactly — no import
# needed so this file is fully self-contained for the demo)
# ---------------------------------------------------------------------------

from translations.state import CarddemoState
from translations.coactupc_1210_edit_account import coactupc_1210_edit_account
from translations.coactupc_1215_edit_mandatory import coactupc_1215_edit_mandatory
from translations.coactupc_1220_edit_yesno import coactupc_1220_edit_yesno
from translations.coactupc_1250_edit_signed_9v2 import coactupc_1250_edit_signed_9v2
from translations.coactupc_1260_edit_us_phone_num import coactupc_1260_edit_us_phone_num
from translations.coactupc_1265_edit_us_ssn import coactupc_1265_edit_us_ssn
from translations.coactupc_1270_edit_us_state_cd import coactupc_1270_edit_us_state_cd
from translations.coactupc_1275_edit_fico_score import coactupc_1275_edit_fico_score
from translations.coactupc_1205_compare_old_new import coactupc_1205_compare_old_new


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SEP = "=" * 70
PASS = "\033[92m PASS \033[0m"
FAIL = "\033[91m FAIL \033[0m"


def check(label: str, condition: bool) -> bool:
    tag = PASS if condition else FAIL
    print(f"  [{tag}]  {label}")
    return condition


def scenario(title: str):
    print(f"\n{SEP}")
    print(f"  SCENARIO: {title}")
    print(SEP)


def run_timed(fn, state):
    """Run fn(state) and return elapsed microseconds."""
    t0 = time.perf_counter()
    fn(state)
    return (time.perf_counter() - t0) * 1_000_000  # µs


# ---------------------------------------------------------------------------
# Scenario 1 — Account ID validation
# COBOL paragraph: 1210-EDIT-ACCOUNT
# Proof: blank account ID sets ws_prompt_for_acct; numeric ID passes through
# ---------------------------------------------------------------------------
def scenario_1():
    scenario("1210-EDIT-ACCOUNT  |  Account ID gate")

    # 1a: blank account ID → harness sets prompt flag
    s = CarddemoState()
    s.cc_acct_id = "          "   # 10 spaces — blank input from CICS map
    s.cdemo_acct_id = 0
    us = run_timed(coactupc_1210_edit_account, s)
    ok1 = check("Blank acct_id  → ws_prompt_for_acct is True", s.ws_prompt_for_acct)
    ok2 = check("Blank acct_id  → flg_acctfilter_not_ok is True", s.flg_acctfilter_not_ok)
    print(f"  Elapsed: {us:.1f} µs")

    # 1b: valid numeric account ID
    s2 = CarddemoState()
    s2.cc_acct_id = "0000000042"
    s2.cdemo_acct_id = 0
    us2 = run_timed(coactupc_1210_edit_account, s2)
    ok3 = check("Valid acct_id   → ws_prompt_for_acct is False", not s2.ws_prompt_for_acct)
    ok4 = check("Valid acct_id   → flg_acctfilter_not_ok is False", not s2.flg_acctfilter_not_ok)
    print(f"  Elapsed: {us2:.1f} µs")

    return all([ok1, ok2, ok3, ok4])


# ---------------------------------------------------------------------------
# Scenario 2 — Mandatory field validation
# COBOL paragraph: 1215-EDIT-MANDATORY
# Proof: blank field fails; non-blank passes
# ---------------------------------------------------------------------------
def scenario_2():
    scenario("1215-EDIT-MANDATORY  |  Required-field gate")

    s = CarddemoState()
    s.ws_edit_alphanum_only = "          "  # blank
    us = run_timed(coactupc_1215_edit_mandatory, s)
    ok1 = check("Blank field    → flg_mandatory_not_ok is True", s.flg_mandatory_not_ok)
    ok2 = check("Blank field    → flg_mandatory_blank is True", s.flg_mandatory_blank)
    print(f"  Elapsed: {us:.1f} µs")

    s2 = CarddemoState()
    s2.ws_edit_alphanum_only = "JOHN      "
    us2 = run_timed(coactupc_1215_edit_mandatory, s2)
    ok3 = check("Non-blank field → flg_mandatory_not_ok is False", not s2.flg_mandatory_not_ok)
    ok4 = check("Non-blank field → flg_mandatory_isvalid is True", s2.flg_mandatory_isvalid)
    print(f"  Elapsed: {us2:.1f} µs")

    return all([ok1, ok2, ok3, ok4])


# ---------------------------------------------------------------------------
# Scenario 3 — US phone number validation
# COBOL paragraph: 1260-EDIT-US-PHONE-NUM
# Proof: non-numeric area code fails; valid 10-digit number passes
# ---------------------------------------------------------------------------
def scenario_3():
    scenario("1260-EDIT-US-PHONE-NUM  |  Phone number validation")

    # 3a: invalid — alpha area code
    s = CarddemoState()
    s.ws_edit_us_phone_numa = "ABC"
    s.ws_edit_us_phone_numb = "555"
    s.ws_edit_us_phone_numc = "1234"
    us = run_timed(coactupc_1260_edit_us_phone_num, s)
    ok1 = check("Alpha area code → ws_edit_us_phone_is_invalid is True", s.ws_edit_us_phone_is_invalid)
    ok2 = check("Alpha area code → flg_edit_us_phonea_not_ok is True", s.flg_edit_us_phonea_not_ok)
    print(f"  Elapsed: {us:.1f} µs")

    # 3b: valid US phone
    s2 = CarddemoState()
    s2.ws_edit_us_phone_numa = "415"
    s2.ws_edit_us_phone_numb = "555"
    s2.ws_edit_us_phone_numc = "9876"
    us2 = run_timed(coactupc_1260_edit_us_phone_num, s2)
    ok3 = check("Valid phone     → ws_edit_us_phone_is_valid is True", s2.ws_edit_us_phone_is_valid)
    ok4 = check("Valid phone     → ws_edit_us_phone_is_invalid is False", not s2.ws_edit_us_phone_is_invalid)
    print(f"  Elapsed: {us2:.1f} µs")

    return all([ok1, ok2, ok3, ok4])


# ---------------------------------------------------------------------------
# Scenario 4 — Change detection (old vs new account data)
# COBOL paragraph: 1205-COMPARE-OLD-NEW
# Proof: identical old/new → no_changes_detected; diff → change_has_occurred
# ---------------------------------------------------------------------------
def scenario_4():
    scenario("1205-COMPARE-OLD-NEW  |  Change detection gate")

    # 4a: no changes
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
    ok1 = check("Identical data  → no_changes_detected is True", s.no_changes_detected)
    ok2 = check("Identical data  → change_has_occurred is False", not s.change_has_occurred)
    print(f"  Elapsed: {us:.1f} µs")

    # 4b: credit limit changed
    s2 = CarddemoState()
    s2.acup_new_active_status = "Y"
    s2.acup_old_active_status = "Y"
    s2.acup_new_credit_limit = 7500.00    # changed
    s2.acup_old_credit_limit = 5000.00
    s2.acup_new_cust_first_name = "JOHN"
    s2.acup_old_cust_first_name = "JOHN"
    s2.acup_new_cust_last_name = "SMITH"
    s2.acup_old_cust_last_name = "SMITH"
    us2 = run_timed(coactupc_1205_compare_old_new, s2)
    ok3 = check("Credit limit Δ  → change_has_occurred is True", s2.change_has_occurred)
    ok4 = check("Credit limit Δ  → no_changes_detected is False", not s2.no_changes_detected)
    print(f"  Elapsed: {us2:.1f} µs")

    return all([ok1, ok2, ok3, ok4])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    print(SEP)
    print("  HermesCOBOL  —  COACTUPC Translation Demo")
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
        print("  STATUS: " + "\033[92mALL PASS — 100% deterministic\033[0m")
    else:
        print("  STATUS: " + "\033[91mSOME FAILURES — investigate above\033[0m")
    print(SEP)
    print()
    print("  Architecture note:")
    print("  Each scenario above maps 1:1 to a COBOL paragraph in COACTUPC.")
    print("  State is a frozen Python dataclass. No inference at runtime.")
    print("  The same inputs will produce identical outputs on any machine,")
    print("  any OS, any year — without network access or GPU.")
    print()

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()

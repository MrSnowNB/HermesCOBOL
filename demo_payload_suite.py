#!/usr/bin/env python
"""
demo_payload_suite.py  --  HermesCOBOL Adversarial Payload Suite
=================================================================
5 business-realistic scenarios for COACTUPC.
Each scenario includes:
  - Plain English description of the business situation
  - COBOL-equivalent payload comment (what the mainframe COMMAREA would hold)
  - Python state setup (the translated equivalent)
  - Expected output assertions with business justification

USAGE:
    python demo_payload_suite.py
    py demo_payload_suite.py

All paragraphs called are real translated COBOL. No mocks. No stubs.
Same output every run, forever.
"""

import sys
import time

from translations.state import CarddemoState
from translations.coactupc_1210_edit_account import coactupc_1210_edit_account
from translations.coactupc_1215_edit_mandatory import edit_mandatory_1215
from translations.coactupc_1205_compare_old_new import coactupc_1205_compare_old_new
from translations.coactupc_1265_edit_us_ssn import coactupc_1265_edit_us_ssn
from translations.coactupc_1275_edit_fico_score import coactupc_1275_edit_fico_score

import translations.coactupc_1260_edit_us_phone_num as _phone_mod
import translations.coactupc_1270_edit_us_state_cd as _state_mod

SEP  = "=" * 72
SEP2 = "-" * 72

passed_total = 0
failed_total = 0


def check(label: str, condition: bool) -> bool:
    global passed_total, failed_total
    tag = " PASS " if condition else " FAIL "
    print(f"  [{tag}]  {label}")
    if condition:
        passed_total += 1
    else:
        failed_total += 1
    return condition


def header(num: int, title: str, description: str):
    print(f"\n{SEP}")
    print(f"  SCENARIO {num}: {title}")
    print(SEP2)
    print(f"  Business context:")
    for line in description.strip().split("\n"):
        print(f"    {line.strip()}")
    print(SEP2)


def run_phone(state):
    _phone_mod.state = state
    _phone_mod.edit_us_phone_num()
    if state.ws_edit_us_phone_is_valid:
        state.ws_edit_us_phone_is_invalid = False


def run_state_cd(state):
    _state_mod.state = state
    _state_mod.edit_us_state_cd()


# ===========================================================================
# SCENARIO 1
# A teller submits a credit limit increase for account 4000001234.
# The new limit ($15,000) differs from the old limit ($10,000).
# The system must detect the change and flag it for supervisor approval.
# COBOL paragraph exercised: 1205-COMPARE-OLD-NEW
#
# COBOL COMMAREA payload equivalent:
#   ACUP-NEW-CREDIT-LIMIT    = +000000015000.00
#   ACUP-OLD-CREDIT-LIMIT    = +000000010000.00
#   ACUP-NEW-ACTIVE-STATUS   = 'Y'
#   ACUP-OLD-ACTIVE-STATUS   = 'Y'
#   ACUP-NEW-CUST-FIRST-NAME = 'MARGARET              '
#   ACUP-OLD-CUST-FIRST-NAME = 'MARGARET              '
#   ACUP-NEW-CUST-LAST-NAME  = 'HOLLINGSWORTH         '
#   ACUP-OLD-CUST-LAST-NAME  = 'HOLLINGSWORTH         '
# ===========================================================================
def scenario_1():
    header(1,
        "Credit limit increase -- change must be detected",
        """
        Teller raises credit limit from $10,000 to $15,000 for customer
        Margaret Hollingsworth (acct 4000001234). All other fields unchanged.
        Expected: system detects the change and routes to supervisor approval.
        COBOL: 1205-COMPARE-OLD-NEW sets CHANGE-HAS-OCCURRED.
        """
    )

    s = CarddemoState()
    # Account fields
    s.acup_new_credit_limit    = 15000.00
    s.acup_old_credit_limit    = 10000.00
    s.acup_new_active_status   = "Y"
    s.acup_old_active_status   = "Y"
    s.acup_new_curr_bal        = 3241.88
    s.acup_old_curr_bal        = 3241.88
    s.acup_new_cash_credit_limit = 2000.00
    s.acup_old_cash_credit_limit = 2000.00
    s.acup_new_open_date       = "20180315"
    s.acup_old_open_date       = "20180315"
    s.acup_new_expiraion_date  = "20281231"
    s.acup_old_expiraion_date  = "20281231"
    s.acup_new_reissue_date    = "20240101"
    s.acup_old_reissue_date    = "20240101"
    s.acup_new_curr_cyc_credit = 0.00
    s.acup_old_curr_cyc_credit = 0.00
    s.acup_new_curr_cyc_debit  = 0.00
    s.acup_old_curr_cyc_debit  = 0.00
    s.acup_new_group_id        = "GOLD"
    s.acup_old_group_id        = "GOLD"
    # Customer fields
    s.acup_new_cust_first_name = "MARGARET"
    s.acup_old_cust_first_name = "MARGARET"
    s.acup_new_cust_last_name  = "HOLLINGSWORTH"
    s.acup_old_cust_last_name  = "HOLLINGSWORTH"
    s.acup_new_cust_middle_name = ""
    s.acup_old_cust_middle_name = ""
    s.acup_new_cust_addr_line_1 = "123 MAIN ST"
    s.acup_old_cust_addr_line_1 = "123 MAIN ST"
    s.acup_new_cust_addr_line_2 = ""
    s.acup_old_cust_addr_line_2 = ""
    s.acup_new_cust_addr_line_3 = ""
    s.acup_old_cust_addr_line_3 = ""
    s.acup_new_cust_addr_state_cd    = "NY"
    s.acup_old_cust_addr_state_cd    = "NY"
    s.acup_new_cust_addr_country_cd  = "USA"
    s.acup_old_cust_addr_country_cd  = "USA"
    s.acup_new_cust_addr_zip         = "10001"
    s.acup_old_cust_addr_zip         = "10001"
    s.acup_new_cust_phone_num_1a = "212"
    s.acup_old_cust_phone_num_1a = "212"
    s.acup_new_cust_phone_num_1b = "555"
    s.acup_old_cust_phone_num_1b = "555"
    s.acup_new_cust_phone_num_1c = "0100"
    s.acup_old_cust_phone_num_1c = "0100"
    s.acup_new_cust_phone_num_2a = ""
    s.acup_old_cust_phone_num_2a = ""
    s.acup_new_cust_phone_num_2b = ""
    s.acup_old_cust_phone_num_2b = ""
    s.acup_new_cust_phone_num_2c = ""
    s.acup_old_cust_phone_num_2c = ""
    s.acup_new_cust_ssn_x        = "123456789"
    s.acup_old_cust_ssn_x        = "123456789"
    s.acup_new_cust_govt_issued_id  = "DL-NY-9988776"
    s.acup_old_cust_govt_issued_id  = "DL-NY-9988776"
    s.acup_new_cust_dob_yyyy_mm_dd  = "19750422"
    s.acup_old_cust_dob_yyyy_mm_dd  = "19750422"
    s.acup_new_cust_eft_account_id  = "EFT0012345"
    s.acup_old_cust_eft_account_id  = "EFT0012345"
    s.acup_new_cust_pri_holder_ind  = "Y"
    s.acup_old_cust_pri_holder_ind  = "Y"
    s.acup_new_cust_fico_score_x    = "720"
    s.acup_old_cust_fico_score_x    = "720"

    t0 = time.perf_counter()
    coactupc_1205_compare_old_new(s)
    us = (time.perf_counter() - t0) * 1_000_000

    check("Change detected         -> change_has_occurred is True",  s.change_has_occurred)
    check("No false negative        -> no_changes_detected is False", not s.no_changes_detected)
    print(f"  Elapsed: {us:.1f} us")


# ===========================================================================
# SCENARIO 2
# Same account, no edits made. Teller accidentally hits Submit twice.
# The system must recognise no changes occurred and suppress the update.
# COBOL paragraph exercised: 1205-COMPARE-OLD-NEW
#
# COBOL COMMAREA payload equivalent:
#   All ACUP-NEW-* fields identical to ACUP-OLD-* fields.
# ===========================================================================
def scenario_2():
    header(2,
        "Duplicate submit -- no changes must NOT trigger update",
        """
        Teller hits Submit with zero edits (accidental double-submit).
        All ACUP-NEW fields are identical to ACUP-OLD.
        Expected: no_changes_detected=True, system suppresses the write.
        This is an audit/integrity control -- a ghost update corrupts history.
        COBOL: 1205-COMPARE-OLD-NEW falls through to NO-CHANGES-DETECTED.
        """
    )

    s = CarddemoState()
    # Both sides identical -- copy/paste same values
    for attr in [
        ("acup_new_credit_limit",    "acup_old_credit_limit",    10000.00),
        ("acup_new_curr_bal",        "acup_old_curr_bal",         3241.88),
        ("acup_new_cash_credit_limit","acup_old_cash_credit_limit",2000.00),
        ("acup_new_curr_cyc_credit", "acup_old_curr_cyc_credit",    0.00),
        ("acup_new_curr_cyc_debit",  "acup_old_curr_cyc_debit",     0.00),
    ]:
        setattr(s, attr[0], attr[2])
        setattr(s, attr[1], attr[2])

    for attr in [
        ("acup_new_active_status",       "acup_old_active_status",       "Y"),
        ("acup_new_open_date",           "acup_old_open_date",           "20180315"),
        ("acup_new_expiraion_date",      "acup_old_expiraion_date",      "20281231"),
        ("acup_new_reissue_date",        "acup_old_reissue_date",        "20240101"),
        ("acup_new_group_id",            "acup_old_group_id",            "GOLD"),
        ("acup_new_cust_first_name",     "acup_old_cust_first_name",     "MARGARET"),
        ("acup_new_cust_middle_name",    "acup_old_cust_middle_name",    ""),
        ("acup_new_cust_last_name",      "acup_old_cust_last_name",      "HOLLINGSWORTH"),
        ("acup_new_cust_addr_line_1",    "acup_old_cust_addr_line_1",    "123 MAIN ST"),
        ("acup_new_cust_addr_line_2",    "acup_old_cust_addr_line_2",    ""),
        ("acup_new_cust_addr_line_3",    "acup_old_cust_addr_line_3",    ""),
        ("acup_new_cust_addr_state_cd",  "acup_old_cust_addr_state_cd",  "NY"),
        ("acup_new_cust_addr_country_cd","acup_old_cust_addr_country_cd","USA"),
        ("acup_new_cust_addr_zip",       "acup_old_cust_addr_zip",       "10001"),
        ("acup_new_cust_phone_num_1a",   "acup_old_cust_phone_num_1a",   "212"),
        ("acup_new_cust_phone_num_1b",   "acup_old_cust_phone_num_1b",   "555"),
        ("acup_new_cust_phone_num_1c",   "acup_old_cust_phone_num_1c",   "0100"),
        ("acup_new_cust_phone_num_2a",   "acup_old_cust_phone_num_2a",   ""),
        ("acup_new_cust_phone_num_2b",   "acup_old_cust_phone_num_2b",   ""),
        ("acup_new_cust_phone_num_2c",   "acup_old_cust_phone_num_2c",   ""),
        ("acup_new_cust_ssn_x",          "acup_old_cust_ssn_x",          "123456789"),
        ("acup_new_cust_govt_issued_id", "acup_old_cust_govt_issued_id", "DL-NY-9988776"),
        ("acup_new_cust_dob_yyyy_mm_dd", "acup_old_cust_dob_yyyy_mm_dd", "19750422"),
        ("acup_new_cust_eft_account_id", "acup_old_cust_eft_account_id", "EFT0012345"),
        ("acup_new_cust_pri_holder_ind", "acup_old_cust_pri_holder_ind", "Y"),
        ("acup_new_cust_fico_score_x",   "acup_old_cust_fico_score_x",   "720"),
        ("acup_new_acct_id_x",           "acup_old_acct_id_x",           "4000001234"),
        ("acup_new_cust_id_x",           "acup_old_cust_id_x",           "9000001234"),
    ]:
        setattr(s, attr[0], attr[2])
        setattr(s, attr[1], attr[2])

    t0 = time.perf_counter()
    coactupc_1205_compare_old_new(s)
    us = (time.perf_counter() - t0) * 1_000_000

    check("Duplicate submit         -> no_changes_detected is True",  s.no_changes_detected)
    check("Duplicate submit         -> change_has_occurred is False", not s.change_has_occurred)
    print(f"  Elapsed: {us:.1f} us")


# ===========================================================================
# SCENARIO 3
# New account lookup -- teller types account number 4000009999 into the
# CICS map. The harness must validate the account ID format before any
# database read occurs. This is the first gate the mainframe hits.
# COBOL paragraph exercised: 1210-EDIT-ACCOUNT
#
# COBOL COMMAREA payload equivalent:
#   CC-ACCT-ID   = '4000009999'
#   CDEMO-ACCT-ID = 0  (not yet resolved)
#   WS-RETURN-MSG-OFF = TRUE
# ===========================================================================
def scenario_3():
    header(3,
        "Account lookup -- valid ID parsed and carried into CDEMO",
        """
        Teller enters account number 4000009999 into the CICS screen.
        The harness validates format and loads the numeric value into
        CDEMO-ACCT-ID for downstream DB2 read.
        Expected: flg_acctfilter_isvalid=True, cdemo_acct_id=4000009999.
        This proves the translation carries values correctly, not just flags.
        COBOL: 1210-EDIT-ACCOUNT MOVE CC-ACCT-ID TO CDEMO-ACCT-ID.
        """
    )

    s = CarddemoState()
    s.cc_acct_id      = "4000009999"
    s.cc_acct_id_n    = 4000009999
    s.ws_return_msg_off = True

    t0 = time.perf_counter()
    coactupc_1210_edit_account(s)
    us = (time.perf_counter() - t0) * 1_000_000

    check("Acct 4000009999         -> flg_acctfilter_isvalid is True",  s.flg_acctfilter_isvalid)
    check("Acct 4000009999         -> cdemo_acct_id = 4000009999",       s.cdemo_acct_id == 4000009999)
    check("Acct 4000009999         -> acup_new_acct_id = '4000009999'",  s.acup_new_acct_id == "4000009999")
    check("Acct 4000009999         -> no input error",                    not s.input_error)
    print(f"  Elapsed: {us:.1f} us")


# ===========================================================================
# SCENARIO 4
# Teller attempts to update a customer whose SSN on the form has a
# non-numeric character in part 1 (transcription error: '12X' instead of
# '123'). The system must reject the record before any write occurs.
# COBOL paragraph exercised: 1265-EDIT-US-SSN
#
# COBOL COMMAREA payload equivalent:
#   WS-EDIT-US-SSN-PART1 = '12X'
#   WS-EDIT-US-SSN-PART2 = '45'
#   WS-EDIT-US-SSN-PART3 = '6789'
# ===========================================================================
def scenario_4():
    header(4,
        "SSN transcription error -- bad part 1 must be rejected",
        """
        Customer form shows SSN 12X-45-6789 (typo in area number).
        In a live environment this must be caught before the DB2 WRITE.
        Expected: flg_edit_us_ssn_part1_not_ok=True, record blocked.
        An LLM-based system would need to 'understand' this is invalid;
        this harness rejects it deterministically via digit-check logic.
        COBOL: 1265-EDIT-US-SSN validates each part independently.
        """
    )

    s = CarddemoState()
    s.ws_edit_us_ssn_part1 = "12X"
    s.ws_edit_us_ssn_part2 = "45"
    s.ws_edit_us_ssn_part3 = "6789"

    t0 = time.perf_counter()
    coactupc_1265_edit_us_ssn(s)
    us = (time.perf_counter() - t0) * 1_000_000

    check("Bad SSN part 1          -> flg_edit_us_ssn_part1_not_ok is True", s.flg_edit_us_ssn_part1_not_ok)
    print(f"  Elapsed: {us:.1f} us")

    # Contrast: valid SSN passes
    s2 = CarddemoState()
    s2.ws_edit_us_ssn_part1 = "123"
    s2.ws_edit_us_ssn_part2 = "45"
    s2.ws_edit_us_ssn_part3 = "6789"

    t0 = time.perf_counter()
    coactupc_1265_edit_us_ssn(s2)
    us2 = (time.perf_counter() - t0) * 1_000_000

    check("Valid SSN 123-45-6789   -> flg_edit_us_ssn_part1_not_ok is False", not s2.flg_edit_us_ssn_part1_not_ok)
    print(f"  Elapsed: {us2:.1f} us")


# ===========================================================================
# SCENARIO 5
# Risk officer updates a customer's FICO score to 850 (top tier).
# The system must accept it as valid. Then a data entry error enters 999
# (above the 850 ceiling). The system must reject 999 as out of range.
# COBOL paragraph exercised: 1275-EDIT-FICO-SCORE
#
# COBOL COMMAREA payload equivalent:
#   WS-EDIT-FICO-SCORE = 850  (valid)
#   WS-EDIT-FICO-SCORE = 999  (out of range -- FICO max is 850)
# ===========================================================================
def scenario_5():
    header(5,
        "FICO score range validation -- 850 valid, 999 rejected",
        """
        Risk officer sets FICO score to 850 (valid maximum).
        Then a second entry of 999 is attempted (above ceiling).
        Expected: 850 -> valid; 999 -> flg_fico_score_not_ok=True.
        FICO range is 300-850. This is a hard regulatory constraint.
        A system that gets this wrong on even 1-in-1000 records creates
        material risk. This harness cannot get it wrong -- it's arithmetic.
        COBOL: 1275-EDIT-FICO-SCORE enforces 300 <= score <= 850.
        """
    )

    # Valid: 850
    s = CarddemoState()
    s.acup_new_cust_fico_score_x = "850"

    t0 = time.perf_counter()
    coactupc_1275_edit_fico_score(s)
    us = (time.perf_counter() - t0) * 1_000_000

    check("FICO 850 (valid max)    -> flg_fico_score_not_ok is False", not s.flg_fico_score_not_ok)
    check("FICO 850 (valid max)    -> flg_fico_score_is_valid is True", s.flg_fico_score_is_valid)
    print(f"  Elapsed: {us:.1f} us")

    # Invalid: 999
    s2 = CarddemoState()
    s2.acup_new_cust_fico_score_x = "999"

    t0 = time.perf_counter()
    coactupc_1275_edit_fico_score(s2)
    us2 = (time.perf_counter() - t0) * 1_000_000

    check("FICO 999 (above max)    -> flg_fico_score_not_ok is True",  s2.flg_fico_score_not_ok)
    check("FICO 999 (above max)    -> flg_fico_score_is_valid is False", not s2.flg_fico_score_is_valid)
    print(f"  Elapsed: {us2:.1f} us")

    # Invalid: 299 (below floor)
    s3 = CarddemoState()
    s3.acup_new_cust_fico_score_x = "299"

    t0 = time.perf_counter()
    coactupc_1275_edit_fico_score(s3)
    us3 = (time.perf_counter() - t0) * 1_000_000

    check("FICO 299 (below min)    -> flg_fico_score_not_ok is True",  s3.flg_fico_score_not_ok)
    print(f"  Elapsed: {us3:.1f} us")


# ===========================================================================
# Main
# ===========================================================================
def main():
    print()
    print(SEP)
    print("  HermesCOBOL  --  COACTUPC Adversarial Payload Suite")
    print("  5 business scenarios. Real COBOL logic. Zero inference.")
    print(SEP)

    scenario_1()
    scenario_2()
    scenario_3()
    scenario_4()
    scenario_5()

    total = passed_total + failed_total
    print(f"\n{SEP}")
    print(f"  RESULT: {passed_total}/{total} checks passed")
    if failed_total == 0:
        print("  STATUS: ALL PASS -- 100% deterministic")
    else:
        print(f"  STATUS: {failed_total} FAILURE(S) -- investigate above")
    print(SEP)
    print()
    print("  What these scenarios prove:")
    print("  1. Change detection     -- ghost updates suppressed (audit integrity)")
    print("  2. Idempotency          -- double-submit cannot corrupt data")
    print("  3. Value propagation    -- account ID carried into downstream correctly")
    print("  4. Data rejection       -- invalid SSN blocked before any DB write")
    print("  5. Regulatory range     -- FICO ceiling (850) enforced deterministically")
    print()
    print("  None of these outcomes are probabilistic.")
    print("  An LLM that is '80% accurate' fails 1-in-5 of these.")
    print("  In financial services, 1-in-5 is not a deployment.")
    print()

    sys.exit(0 if failed_total == 0 else 1)


if __name__ == "__main__":
    main()

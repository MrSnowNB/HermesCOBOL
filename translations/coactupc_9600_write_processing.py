"""9600-WRITE-PROCESSING paragraph translation."""

from typing import Any
from translations.coactupc_9xxx_stubs import (
    DFHRESP_NORMAL,
    DFHRESP_NOTFND,
    check_change_in_rec,
)


def write_processing(state: Any) -> None:
    """9600-WRITE-PROCESSING"""

    # Read the account file for update
    state.ws_card_rid_acct_id = state.cc_acct_id

    if state.ws_card_rid_acct_id in state.acct_db:
        state.ws_resp_cd = DFHRESP_NORMAL
        state.account_record = state.acct_db[state.ws_card_rid_acct_id]
    else:
        state.ws_resp_cd = DFHRESP_NOTFND

    if state.ws_resp_cd != DFHRESP_NORMAL:
        state.input_error = True
        if state.ws_return_msg_off:
            state.could_not_lock_acct_for_update = True
        return

    # Read the customer file for update
    state.ws_card_rid_cust_id = state.cdemo_cust_id

    if state.ws_card_rid_cust_id in state.cust_db:
        state.ws_resp_cd = DFHRESP_NORMAL
        state.customer_record = state.cust_db[state.ws_card_rid_cust_id]
    else:
        state.ws_resp_cd = DFHRESP_NOTFND

    if state.ws_resp_cd != DFHRESP_NORMAL:
        state.input_error = True
        if state.ws_return_msg_off:
            state.could_not_lock_cust_for_update = True
        return

    # Did someone change the record while we were out?
    check_change_in_rec(state)

    if state.data_was_changed_before_update:
        return

    # Prepare the update
    state.acct_update_record = {}

    # Account Master data
    state.acct_update_id = state.acup_new_acct_id
    state.acct_update_active_status = state.acup_new_active_status
    # NOTE: COBOL uses ACUP-NEW-CURR-BAL-N etc. (numeric redefinition).
    # State.py canonical names for NEW values omit the _n suffix.
    state.acct_update_curr_bal = state.acup_new_curr_bal
    state.acct_update_credit_limit = state.acup_new_credit_limit
    state.acct_update_cash_credit_limit = state.acup_new_cash_credit_limit
    state.acct_update_curr_cyc_credit = state.acup_new_curr_cyc_credit
    state.acct_update_curr_cyc_debit = state.acup_new_curr_cyc_debit

    state.acct_update_open_date = (
        f"{state.acup_new_open_year}-"
        f"{state.acup_new_open_mon}-"
        f"{state.acup_new_open_day}"
    )

    state.acct_update_expiraion_date = (
        f"{state.acup_new_exp_year}-"
        f"{state.acup_new_exp_mon}-"
        f"{state.acup_new_exp_day}"
    )

    # Reissue date anomaly preserved exactly as specified
    # COBOL: MOVE ACCT-REISSUE-DATE TO ACCT-UPDATE-REISSUE-DATE
    # (immediately overwritten by STRING below)
    state.acct_update_reissue_date = (
        f"{state.acup_new_reissue_year}-"
        f"{state.acup_new_reissue_mon}-"
        f"{state.acup_new_reissue_day}"
    )
    state.acct_update_group_id = state.acup_new_group_id

    # Customer data
    state.cust_update_record = {}

    state.cust_update_id = state.acup_new_cust_id
    state.cust_update_first_name = state.acup_new_cust_first_name
    state.cust_update_middle_name = state.acup_new_cust_middle_name
    state.cust_update_last_name = state.acup_new_cust_last_name
    state.cust_update_addr_line_1 = state.acup_new_cust_addr_line_1
    state.cust_update_addr_line_2 = state.acup_new_cust_addr_line_2
    state.cust_update_addr_line_3 = state.acup_new_cust_addr_line_3
    state.cust_update_addr_state_cd = state.acup_new_cust_addr_state_cd
    state.cust_update_addr_country_cd = state.acup_new_cust_addr_country_cd
    state.cust_update_addr_zip = state.acup_new_cust_addr_zip

    state.cust_update_phone_num_1 = (
        f"({state.acup_new_cust_phone_num_1a})"
        f"{state.acup_new_cust_phone_num_1b}-"
        f"{state.acup_new_cust_phone_num_1c}"
    )

    state.cust_update_phone_num_2 = (
        f"({state.acup_new_cust_phone_num_2a})"
        f"{state.acup_new_cust_phone_num_2b}-"
        f"{state.acup_new_cust_phone_num_2c}"
    )

    state.cust_update_ssn = state.acup_new_cust_ssn
    state.cust_update_govt_issued_id = state.acup_new_cust_govt_issued_id

    state.cust_update_dob_yyyy_mm_dd = (
        f"{state.acup_new_cust_dob_year}-"
        f"{state.acup_new_cust_dob_mon}-"
        f"{state.acup_new_cust_dob_day}"
    )

    state.cust_update_eft_account_id = state.acup_new_cust_eft_account_id
    state.cust_update_pri_card_ind = state.acup_new_cust_pri_holder_ind
    state.cust_update_fico_credit_score = state.acup_new_cust_fico_score

    # Snapshot before account update for possible rollback
    state._acct_record_before_update = state.acct_db.get(
        state.ws_card_rid_acct_id
    )

    # Update account
    try:
        state.acct_db[state.ws_card_rid_acct_id] = state.acct_update_record
        state.ws_resp_cd = DFHRESP_NORMAL
    except Exception:
        state.ws_resp_cd = -1

    if state.ws_resp_cd != DFHRESP_NORMAL:
        state.locked_but_update_failed = True
        return

    # Update customer
    try:
        state.cust_db[state.ws_card_rid_cust_id] = state.cust_update_record
        state.ws_resp_cd = DFHRESP_NORMAL
    except Exception:
        state.ws_resp_cd = -1

    if state.ws_resp_cd != DFHRESP_NORMAL:
        state.locked_but_update_failed = True
        # Rollback account
        if state._acct_record_before_update is not None:
            state.acct_db[state.ws_card_rid_acct_id] = (
                state._acct_record_before_update
            )
        return

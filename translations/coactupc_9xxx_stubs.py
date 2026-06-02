"""Stubs for 9xxx paragraphs (called by 9000-READ-ACCT)."""

DFHRESP_NORMAL = 0
DFHRESP_NOTFND = 13

def getcardxref_byacct(state):
    """9200-GETCARDXREF-BYACCT"""

    try:
        if state.ws_card_rid_acct_id in state.card_xref_db:
            state.ws_resp_cd = DFHRESP_NORMAL
            record = state.card_xref_db[state.ws_card_rid_acct_id]
            state.cdemo_cust_id = record["xref_cust_id"]
            state.cdemo_card_num = record["xref_card_num"]
        else:
            state.ws_resp_cd = DFHRESP_NOTFND
            state.input_error = True
            state.flg_acctfilter_not_ok = True
            if state.ws_return_msg_off:
                state.ws_return_msg = (
                    f"Account:{state.ws_card_rid_acct_id}"
                    f" not found in Cross ref file."
                    f"  Resp:{state.ws_resp_cd}"
                    f" Reas:{state.ws_reas_cd}"
                )
    except Exception:
        state.ws_resp_cd = -1
        state.error_resp = state.ws_resp_cd
        state.error_resp2 = state.ws_reas_cd
        state.input_error = True
        state.flg_acctfilter_not_ok = True
        state.error_opname = "READ"
        state.error_file = state.lit_cardxrefname_acct_path
        state.ws_return_msg = state.ws_file_error_message


def getacctdata_byacct(state):
    """9300-GETACCTDATA-BYACCT"""

    try:
        if state.ws_card_rid_acct_id in state.acct_db:
            state.ws_resp_cd = DFHRESP_NORMAL
            state.found_acct_in_master = True
        else:
            state.ws_resp_cd = DFHRESP_NOTFND
            state.input_error = True
            state.flg_acctfilter_not_ok = True
            state.error_resp = state.ws_resp_cd
            state.error_resp2 = state.ws_reas_cd
            if state.ws_return_msg_off:
                state.ws_return_msg = (
                    f"Account:{state.ws_card_rid_acct_id}"
                    " not found in Acct Master file."
                    f"Resp:{state.error_resp}"
                    f" Reas:{state.error_resp2}"
                )
    except Exception:
        state.ws_resp_cd = -1
        state.input_error = True
        state.flg_acctfilter_not_ok = True
        state.error_opname = "READ"
        state.error_file = state.lit_acctfilename
        state.error_resp = state.ws_resp_cd
        state.error_resp2 = state.ws_reas_cd
        state.ws_return_msg = state.ws_file_error_message


def getcustdata_bycust(state):
    """9400-GETCUSTDATA-BYCUST"""

    try:
        if state.ws_card_rid_cust_id in state.cust_db:
            state.ws_resp_cd = DFHRESP_NORMAL
            state.found_cust_in_master = True
        else:
            state.ws_resp_cd = DFHRESP_NOTFND
            state.input_error = True
            state.flg_custfilter_not_ok = True
            state.error_resp = state.ws_resp_cd
            state.error_resp2 = state.ws_reas_cd
            if state.ws_return_msg_off:
                state.ws_return_msg = (
                    f"CustId:{state.ws_card_rid_cust_id}"
                    " not found in customer master."
                    f"Resp: {state.error_resp}"
                    f" REAS:{state.error_resp2}"
                )
    except Exception:
        state.ws_resp_cd = -1
        state.input_error = True
        state.flg_custfilter_not_ok = True
        state.error_opname = "READ"
        state.error_file = state.lit_custfilename
        state.error_resp = state.ws_resp_cd
        state.error_resp2 = state.ws_reas_cd
        state.ws_return_msg = state.ws_file_error_message


def store_fetched_data(state):
    """9500-STORE-FETCHED-DATA"""

    acct = state.acct_db.get(state.ws_card_rid_acct_id, {})
    cust = state.cust_db.get(state.ws_card_rid_cust_id, {})
    xref = state.card_xref_db.get(state.ws_card_rid_acct_id, {})

    state.acup_old_details = {}

    state.cdemo_acct_id = acct.get("acct_id", "")
    state.cdemo_cust_id = cust.get("cust_id", "")
    state.cdemo_cust_fname = cust.get("cust_first_name", "")
    state.cdemo_cust_mname = cust.get("cust_middle_name", "")
    state.cdemo_cust_lname = cust.get("cust_last_name", "")
    state.cdemo_acct_status = acct.get("acct_active_status", "")
    state.cdemo_card_num = xref.get("xref_card_num", "")

    state.acup_old_acct_id = acct.get("acct_id", "")
    state.acup_old_active_status = acct.get("acct_active_status", "")
    state.acup_old_curr_bal_n = acct.get("acct_curr_bal", "")
    state.acup_old_credit_limit_n = acct.get("acct_credit_limit", "")
    state.acup_old_cash_credit_limit_n = acct.get("acct_cash_credit_limit", "")
    state.acup_old_curr_cyc_credit_n = acct.get("acct_curr_cyc_credit", "")
    state.acup_old_curr_cyc_debit_n = acct.get("acct_curr_cyc_debit", "")

    open_date = acct.get("acct_open_date", "")
    state.acup_old_open_year = open_date[0:4] if len(open_date) >= 4 else ""
    state.acup_old_open_mon = open_date[5:7] if len(open_date) >= 7 else ""
    state.acup_old_open_day = open_date[8:10] if len(open_date) >= 10 else ""

    exp_date = acct.get("acct_expiration_date", "")
    state.acup_old_exp_year = exp_date[0:4] if len(exp_date) >= 4 else ""
    state.acup_old_exp_mon = exp_date[5:7] if len(exp_date) >= 7 else ""
    state.acup_old_exp_day = exp_date[8:10] if len(exp_date) >= 10 else ""

    reissue_date = acct.get("acct_reissue_date", "")
    state.acup_old_reissue_year = reissue_date[0:4] if len(reissue_date) >= 4 else ""
    state.acup_old_reissue_mon = reissue_date[5:7] if len(reissue_date) >= 7 else ""
    state.acup_old_reissue_day = reissue_date[8:10] if len(reissue_date) >= 10 else ""

    state.acup_old_group_id = acct.get("acct_group_id", "")

    state.acup_old_cust_id = cust.get("cust_id", "")
    state.acup_old_cust_ssn = cust.get("cust_ssn", "")

    dob = cust.get("cust_dob_yyyy_mm_dd", "")
    state.acup_old_cust_dob_year = dob[0:4] if len(dob) >= 4 else ""
    state.acup_old_cust_dob_mon = dob[5:7] if len(dob) >= 7 else ""
    state.acup_old_cust_dob_day = dob[8:10] if len(dob) >= 10 else ""

    # NOTE: store full dob as YYYYMMDD (no dashes) for check_change_in_rec
    state.acup_old_cust_dob_yyyy_mm_dd = (
        state.acup_old_cust_dob_year
        + state.acup_old_cust_dob_mon
        + state.acup_old_cust_dob_day
    )

    state.acup_old_cust_fico_score = cust.get("cust_fico_credit_score", "")
    state.acup_old_cust_first_name = cust.get("cust_first_name", "")
    state.acup_old_cust_middle_name = cust.get("cust_middle_name", "")
    state.acup_old_cust_last_name = cust.get("cust_last_name", "")
    state.acup_old_cust_addr_line_1 = cust.get("cust_addr_line_1", "")
    state.acup_old_cust_addr_line_2 = cust.get("cust_addr_line_2", "")
    state.acup_old_cust_addr_line_3 = cust.get("cust_addr_line_3", "")
    state.acup_old_cust_addr_state_cd = cust.get("cust_addr_state_cd", "")
    state.acup_old_cust_addr_country_cd = cust.get("cust_addr_country_cd", "")
    state.acup_old_cust_addr_zip = cust.get("cust_addr_zip", "")
    state.acup_old_cust_phone_num_1 = cust.get("cust_phone_num_1", "")
    state.acup_old_cust_phone_num_2 = cust.get("cust_phone_num_2", "")
    state.acup_old_cust_govt_issued_id = cust.get("cust_govt_issued_id", "")
    state.acup_old_cust_eft_account_id = cust.get("cust_eft_account_id", "")
    state.acup_old_cust_pri_holder_ind = cust.get("cust_pri_card_holder_ind", "")


def check_change_in_rec(state):
    """9700-CHECK-CHANGE-IN-REC"""
    acct = state.acct_db.get(state.ws_card_rid_acct_id, {})
    cust = state.cust_db.get(state.ws_card_rid_cust_id, {})

    # Account comparisons
    if acct.get("acct_active_status", "") != state.acup_old_active_status:
        state.data_was_changed_before_update = True
        return
    if acct.get("acct_curr_bal") != state.acup_old_curr_bal_n:
        state.data_was_changed_before_update = True
        return
    if acct.get("acct_credit_limit") != state.acup_old_credit_limit_n:
        state.data_was_changed_before_update = True
        return
    if acct.get("acct_cash_credit_limit") != state.acup_old_cash_credit_limit_n:
        state.data_was_changed_before_update = True
        return
    if acct.get("acct_curr_cyc_credit") != state.acup_old_curr_cyc_credit_n:
        state.data_was_changed_before_update = True
        return
    if acct.get("acct_curr_cyc_debit") != state.acup_old_curr_cyc_debit_n:
        state.data_was_changed_before_update = True
        return

    # Date fields: live "YYYY-MM-DD", old split into year/mon/day parts
    open_date = acct.get("acct_open_date", "")
    if (open_date[0:4] != state.acup_old_open_year or
            open_date[5:7] != state.acup_old_open_mon or
            open_date[8:10] != state.acup_old_open_day):
        state.data_was_changed_before_update = True
        return

    exp_date = acct.get("acct_expiration_date", "")
    if (exp_date[0:4] != state.acup_old_exp_year or
            exp_date[5:7] != state.acup_old_exp_mon or
            exp_date[8:10] != state.acup_old_exp_day):
        state.data_was_changed_before_update = True
        return

    reissue_date = acct.get("acct_reissue_date", "")
    if (reissue_date[0:4] != state.acup_old_reissue_year or
            reissue_date[5:7] != state.acup_old_reissue_mon or
            reissue_date[8:10] != state.acup_old_reissue_day):
        state.data_was_changed_before_update = True
        return

    # group_id: case-insensitive
    if acct.get("acct_group_id", "").upper() != state.acup_old_group_id.upper():
        state.data_was_changed_before_update = True
        return

    # Customer string fields: case-insensitive
    str_fields = [
        ("cust_first_name",         "acup_old_cust_first_name"),
        ("cust_middle_name",        "acup_old_cust_middle_name"),
        ("cust_last_name",          "acup_old_cust_last_name"),
        ("cust_addr_line_1",        "acup_old_cust_addr_line_1"),
        ("cust_addr_line_2",        "acup_old_cust_addr_line_2"),
        ("cust_addr_line_3",        "acup_old_cust_addr_line_3"),
        ("cust_addr_state_cd",      "acup_old_cust_addr_state_cd"),
        ("cust_addr_country_cd",    "acup_old_cust_addr_country_cd"),
        ("cust_addr_zip",           "acup_old_cust_addr_zip"),
        ("cust_phone_num_1",        "acup_old_cust_phone_num_1"),
        ("cust_phone_num_2",        "acup_old_cust_phone_num_2"),
        ("cust_ssn",                "acup_old_cust_ssn"),
        ("cust_govt_issued_id",     "acup_old_cust_govt_issued_id"),
        ("cust_eft_account_id",     "acup_old_cust_eft_account_id"),
        ("cust_pri_card_holder_ind","acup_old_cust_pri_holder_ind"),
        ("cust_fico_credit_score",  "acup_old_cust_fico_score"),
    ]
    for db_key, old_attr in str_fields:
        live = cust.get(db_key, "").upper()
        old = getattr(state, old_attr, "").upper()
        if live != old:
            state.data_was_changed_before_update = True
            return

    # DOB anomaly:
    # live: "YYYY-MM-DD" → [0:4], [5:7], [8:10]
    # old:  "YYYYMMDD"   → [0:4], [4:6], [6:8]
    live_dob = cust.get("cust_dob_yyyy_mm_dd", "")
    old_dob = state.acup_old_cust_dob_yyyy_mm_dd
    if (live_dob[0:4] != old_dob[0:4] or
            live_dob[5:7] != old_dob[4:6] or
            live_dob[8:10] != old_dob[6:8]):
        state.data_was_changed_before_update = True
        return

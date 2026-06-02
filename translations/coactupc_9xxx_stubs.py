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
        # OTHER path - capture real code before overwriting
        state.ws_resp_cd = -1  # unknown/other
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
        # OTHER path
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
        # OTHER path
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

    # Read from source records
    acct = state.acct_db.get(state.ws_card_rid_acct_id, {})
    cust = state.cust_db.get(state.ws_card_rid_cust_id, {})
    xref = state.card_xref_db.get(state.ws_card_rid_acct_id, {})

    # INITIALIZE ACUP-OLD-DETAILS
    state.acup_old_details = {}

    # Commarea population
    state.cdemo_acct_id = acct.get("acct_id", "")
    state.cdemo_cust_id = cust.get("cust_id", "")
    state.cdemo_cust_fname = cust.get("cust_first_name", "")
    state.cdemo_cust_mname = cust.get("cust_middle_name", "")
    state.cdemo_cust_lname = cust.get("cust_last_name", "")
    state.cdemo_acct_status = acct.get("acct_active_status", "")
    state.cdemo_card_num = xref.get("xref_card_num", "")

    # Account Master fields
    state.acup_old_acct_id = acct.get("acct_id", "")
    state.acup_old_active_status = acct.get("acct_active_status", "")
    state.acup_old_curr_bal_n = acct.get("acct_curr_bal", "")
    state.acup_old_credit_limit_n = acct.get("acct_credit_limit", "")
    state.acup_old_cash_credit_limit_n = acct.get("acct_cash_credit_limit", "")
    state.acup_old_curr_cyc_credit_n = acct.get("acct_curr_cyc_credit", "")
    state.acup_old_curr_cyc_debit_n = acct.get("acct_curr_cyc_debit", "")

    # Date parsing - Open Date
    open_date = acct.get("acct_open_date", "")
    state.acup_old_open_year = open_date[0:4] if len(open_date) >= 4 else ""
    state.acup_old_open_mon = open_date[5:7] if len(open_date) >= 7 else ""
    state.acup_old_open_day = open_date[8:10] if len(open_date) >= 10 else ""

    # Expiry Date
    exp_date = acct.get("acct_expiration_date", "")
    state.acup_old_exp_year = exp_date[0:4] if len(exp_date) >= 4 else ""
    state.acup_old_exp_mon = exp_date[5:7] if len(exp_date) >= 7 else ""
    state.acup_old_exp_day = exp_date[8:10] if len(exp_date) >= 10 else ""

    # Reissue Date
    reissue_date = acct.get("acct_reissue_date", "")
    state.acup_old_reissue_year = reissue_date[0:4] if len(reissue_date) >= 4 else ""
    state.acup_old_reissue_mon = reissue_date[5:7] if len(reissue_date) >= 7 else ""
    state.acup_old_reissue_day = reissue_date[8:10] if len(reissue_date) >= 10 else ""

    state.acup_old_group_id = acct.get("acct_group_id", "")

    # Customer Master fields
    state.acup_old_cust_id = cust.get("cust_id", "")
    state.acup_old_cust_ssn = cust.get("cust_ssn", "")

    # DOB date parsing
    dob = cust.get("cust_dob_yyyy_mm_dd", "")
    state.acup_old_cust_dob_year = dob[0:4] if len(dob) >= 4 else ""
    state.acup_old_cust_dob_mon = dob[5:7] if len(dob) >= 7 else ""
    state.acup_old_cust_dob_day = dob[8:10] if len(dob) >= 10 else ""

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
    """9700-CHECK-CHANGE-IN-REC stub"""
    # TODO: implement when paragraph is translated
    pass

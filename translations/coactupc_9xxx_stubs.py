"""Stubs for 9xxx paragraphs (called by 9000-READ-ACCT)."""

DFHRESP_NORMAL = 0
DFHRESP_NOTFND = 13
def getcardxref_byacct(state):
    """9200-GETCARDXREF-BYACCT"""

    DFHRESP_NORMAL = 0
    DFHRESP_NOTFND = 13

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

    DFHRESP_NORMAL = 0
    DFHRESP_NOTFND = 13

    try:
        if state.ws_card_rid_acct_id in state.acct_db:
            state.ws_resp_cd = DFHRESP_NORMAL
            state.found_acct_in_master = True
        else:
            state.ws_resp_cd = DFHRESP_NOTFND
            state.input_error = True
            state.flg_acctfilter_not_ok = True
            if state.ws_return_msg_off:
                state.error_resp = state.ws_resp_cd
                state.error_resp2 = state.ws_reas_cd
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
    # TODO: 9400-GETCUSTDATA-BYCUST — implement when paragraph is translated
    pass


def store_fetched_data(state):
    """9500-STORE-FETCHED-DATA"""
    # TODO: 9500-STORE-FETCHED-DATA — implement when paragraph is translated
    pass

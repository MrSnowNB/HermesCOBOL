"""9000-READ-ACCT translation."""

def read_acct(state):
    """9000-READ-ACCT"""

    from translations.coactupc_9xxx_stubs import (
        getcardxref_byacct,
        getacctdata_byacct,
    )

    # INITIALIZE ACUP-OLD-DETAILS
    state.acup_old_details = {}

    state.ws_no_info_message = True

    state.acup_old_acct_id = state.cc_acct_id
    state.ws_card_rid_acct_id = state.cc_acct_id

    getcardxref_byacct(state)
    if state.flg_acctfilter_not_ok:
        return

    getacctdata_byacct(state)
    if state.flg_acctfilter_not_ok:  # COBOL: IF DID-NOT-FIND-ACCT-IN-ACCTDAT (commented out in 9300)
        return

    state.ws_card_rid_cust_id = state.cdemo_cust_id

    # 9400 and 9500 are not reached when 9300 sets flg_acctfilter_not_ok

"""9000-READ-ACCT translation."""

from coactupc_9xxx_stubs import (
    getcardxref_byacct,
    getacctdata_byacct,
    getcustdata_bycust,
    store_fetched_data,
)


def read_acct(state):
    """9000-READ-ACCT"""

    # INITIALIZE ACUP-OLD-DETAILS
    state.acup_old_details = {}

    state.ws_no_info_message = True

    state.acup_old_acct_id = state.cc_acct_id
    state.ws_card_rid_acct_id = state.cc_acct_id

    getcardxref_byacct(state)
    if state.flg_acctfilter_not_ok:
        return

    getacctdata_byacct(state)
    if state.did_not_find_acct_in_acctdat:
        return

    state.ws_card_rid_cust_id = state.cdemo_cust_id

    getcustdata_bycust(state)
    if state.did_not_find_cust_in_custdat:
        return

    store_fetched_data(state)

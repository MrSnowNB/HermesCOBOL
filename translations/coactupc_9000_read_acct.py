"""9000-READ-ACCT translation."""

from translations.coactupc_9xxx_stubs import (
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
    # COBOL: IF DID-NOT-FIND-ACCT-IN-ACCTDAT
    # Note: 9300 sets flg_acctfilter_not_ok instead;
    # DID-NOT-FIND-ACCT-IN-ACCTDAT is commented out in source.
    if state.flg_acctfilter_not_ok:
        return

    state.ws_card_rid_cust_id = state.cdemo_cust_id

    getcustdata_bycust(state)
    # COBOL: IF DID-NOT-FIND-CUST-IN-CUSTDAT
    # Note: 9400 sets flg_custfilter_not_ok instead;
    # DID-NOT-FIND-CUST-IN-CUSTDAT is commented out in source.
    if state.flg_custfilter_not_ok:
        return

    store_fetched_data(state)

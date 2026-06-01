"""
coactupc_2000_decide_action.py
Implements 2000-DECIDE-ACTION paragraph.
"""

from state import state


def decide_action():
    """2000-DECIDE-ACTION"""

    # WHEN ACUP-DETAILS-NOT-FETCHED
    if state.acup_details_not_fetched:
        pass  # No details shown yet

    # WHEN CCARD-AID-PFK12 (Cancel)
    elif state.ccard_aid_pfk12:
        if state.flg_acctfilter_isvalid:
            state.ws_return_msg_off = True
            # TODO: 9000-READ-ACCT — implement when 9000 paragraph is translated
            pass
            if state.found_cust_in_master:
                state.acup_show_details = True

    # WHEN ACUP-SHOW-DETAILS
    elif state.acup_show_details:
        if state.input_error or state.no_changes_detected:
            pass
        else:
            state.acup_changes_ok_not_confirmed = True

    # WHEN ACUP-CHANGES-NOT-OK
    elif state.acup_changes_not_ok:
        pass

    # WHEN ACUP-CHANGES-OK-NOT-CONFIRMED AND CCARD-AID-PFK05
    elif state.acup_changes_ok_not_confirmed and state.ccard_aid_pfk05:
        # TODO: 9600-WRITE-PROCESSING — implement when 9600 paragraph is translated
        pass
        if state.could_not_lock_acct_for_update:
            state.acup_changes_okayed_lock_error = True
        elif state.locked_but_update_failed:
            state.acup_changes_okayed_but_failed = True
        elif state.data_was_changed_before_update:
            state.acup_show_details = True
        else:
            state.acup_changes_okayed_and_done = True

    # WHEN ACUP-CHANGES-OK-NOT-CONFIRMED (no PF5)
    elif state.acup_changes_ok_not_confirmed:
        pass

    # WHEN ACUP-CHANGES-OKAYED-AND-DONE
    elif state.acup_changes_okayed_and_done:
        state.acup_show_details = True
        if not state.cdemo_from_tranid or state.cdemo_from_tranid.strip() == "":
            state.cdemo_acct_id = 0
            state.cdemo_card_num = 0
            state.cdemo_acct_status = ""

    # WHEN OTHER
    else:
        state.abend_culprit = state.lit_thispgm
        state.abend_code = "0001"
        state.abend_reason = ""
        state.abend_msg = "UNEXPECTED DATA SCENARIO"
        raise RuntimeError(
            f"ABEND {state.abend_code}: {state.abend_msg} [{state.abend_culprit}]"
        )

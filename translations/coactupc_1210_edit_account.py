from translations.state import CarddemoState


def coactupc_1210_edit_account(state: CarddemoState) -> None:
    # seq=1: SET FLG-ACCTFILTER-NOT-OK TO TRUE
    state.flg_acctfilter_not_ok = True

    # seq=2: IF CC-ACCT-ID EQUAL LOW-VALUES
    #        OR CC-ACCT-ID EQUAL SPACES
    if not state.cc_acct_id or not state.cc_acct_id.strip():
        # seq=3: SET INPUT-ERROR TO TRUE
        state.input_error = True
        # seq=4: SET FLG-ACCTFILTER-BLANK TO TRUE
        state.flg_acctfilter_blank = True
        # seq=5: IF WS-RETURN-MSG-OFF
        if state.ws_return_msg_off:
            # seq=6: SET WS-PROMPT-FOR-ACCT TO TRUE
            state.ws_prompt_for_acct = True
        # seq=7: END-IF
        # seq=8: MOVE ZEROES TO CDEMO-ACCT-ID ACUP-NEW-ACCT-ID
        state.cdemo_acct_id = 0
        state.acup_new_acct_id = ""
        # seq=9: GO TO 1210-EDIT-ACCOUNT-EXIT
        return  # GO TO 1210-EDIT-ACCOUNT-EXIT
    # seq=10: END-IF

    # seq=11: MOVE CC-ACCT-ID TO ACUP-NEW-ACCT-ID
    state.acup_new_acct_id = state.cc_acct_id

    # seq=12: IF CC-ACCT-ID IS NOT NUMERIC
    #        OR CC-ACCT-ID-N EQUAL ZEROS
    if not state.cc_acct_id.isdigit() or state.cc_acct_id_n == 0:
        # seq=13: SET INPUT-ERROR TO TRUE
        state.input_error = True
        # seq=14: IF WS-RETURN-MSG-OFF
        if state.ws_return_msg_off:
            # seq=15: STRING ... INTO WS-RETURN-MSG
            state.ws_return_msg = 'Account Number if supplied must be a 11 digit Non-Zero Number'
        # seq=16: END-IF
        # seq=17: MOVE ZEROES TO CDEMO-ACCT-ID
        state.cdemo_acct_id = 0
        # seq=18: GO TO 1210-EDIT-ACCOUNT-EXIT
        return  # GO TO 1210-EDIT-ACCOUNT-EXIT
    else:
        # seq=19: MOVE CC-ACCT-ID TO CDEMO-ACCT-ID
        state.cdemo_acct_id = int(state.cc_acct_id)
        # seq=20: SET FLG-ACCTFILTER-ISVALID TO TRUE
        state.flg_acctfilter_isvalid = True
    # seq=21: END-IF

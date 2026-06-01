from translations.state import CarddemoState


def coactupc_1215_edit_mandatory(state: CarddemoState) -> None:
    # seq=1: SET FLG-MANDATORY-NOT-OK TO TRUE
    state.flg_mandatory_not_ok = True

    # seq=2: IF WS-EDIT-ALPHANUM-ONLY EQUAL LOW-VALUES
    if not state.ws_edit_alphanum_only or not state.ws_edit_alphanum_only.strip():
        # seq=3: SET INPUT-ERROR TO TRUE
        state.input_error = True
        # seq=4: SET FLG-MANDATORY-BLANK TO TRUE
        state.flg_mandatory_blank = True
        # seq=5: IF WS-RETURN-MSG-OFF
        if getattr(state, 'ws_return_msg_off', False):
            # seq=6: STRING WS-EDIT-VARIABLE-NAME ... INTO WS-RETURN-MSG
            state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name + ' is a required field'
        # seq=7: END-IF
        # seq=8: GO TO 1215-EDIT-MANDATORY-EXIT
        return  # GO TO 1215-EDIT-MANDATORY-EXIT
    else:
        # seq=9: SET FLG-MANDATORY-ISVALID TO TRUE
        state.flg_mandatory_isvalid = True
    # seq=10: END-IF

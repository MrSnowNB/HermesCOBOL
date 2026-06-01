"""
coactupc_1275_edit_fico_score.py
Implements 1275-EDIT-FICO-SCORE paragraph.
"""



def edit_fico_score():
    """1275-EDIT-FICO-SCORE"""

    fico_str = state.ws_edit_signed_number_9v2_x.strip()

    # Non-numeric or blank check
    if not fico_str or not fico_str.lstrip("+-").isdigit():
        state.input_error = True
        state.flg_fico_score_not_ok = True
        if not state.ws_return_msg_off:
            state.ws_return_msg = (
                f"{state.ws_edit_variable_name.strip()}: "
                "should be between 300 and 850"
            )
        return

    score = int(fico_str)

    if not (300 <= score <= 850):
        state.input_error = True
        state.flg_fico_score_not_ok = True
        if not state.ws_return_msg_off:
            state.ws_return_msg = (
                f"{state.ws_edit_variable_name.strip()}: "
                "should be between 300 and 850"
            )
        return

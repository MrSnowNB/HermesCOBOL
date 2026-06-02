"""
coactupc_1265_edit_us_ssn.py
Implements 1265-EDIT-US-SSN paragraph.
"""

from translations.coactupc_1245_edit_num_reqd import edit_num_reqd_1245


def is_invalid_ssn_part1(value: str) -> bool:
    """COBOL: INVALID-SSN-PART1 condition"""
    v = value.strip().zfill(3)
    return v == "000" or v == "666" or int(v) >= 900


def edit_us_ssn():
    """1265-EDIT-US-SSN"""

    # ===================== Part 1 (3 digits) =====================
    state.ws_edit_variable_name = "SSN: First 3 chars"
    state.ws_edit_alphanum_only = state.acup_new_cust_ssn_1
    state.ws_edit_alphanum_length = 3

    # PERFORM 1245-EDIT-NUM-REQD
    edit_num_reqd_1245(state)

    # MOVE WS-EDIT-ALPHANUM-ONLY-FLAGS TO WS-EDIT-US-SSN-PART1-FLGS
    if state.flg_alphanum_isvalid:
        state.ws_edit_us_ssn_part1_flgs = "ISVALID"
    elif state.flg_alphanum_blank:
        state.ws_edit_us_ssn_part1_flgs = "BLANK"
    else:
        state.ws_edit_us_ssn_part1_flgs = "NOT-OK"

    if state.flg_alphanum_isvalid:
        state.ws_edit_us_ssn_part1 = state.acup_new_cust_ssn_1
        if is_invalid_ssn_part1(state.ws_edit_us_ssn_part1):
            state.input_error = True
            state.flg_edit_us_ssn_part1_not_ok = True
            if not state.ws_return_msg_off:
                state.ws_return_msg = (
                    f"{state.ws_edit_variable_name.strip()}: "
                    "should not be 000, 666, or between 900 and 999"
                )
    else:
        # Part 1 failed numeric check -- flag it
        state.flg_edit_us_ssn_part1_not_ok = True
        state.input_error = True

    # ===================== Part 2 (2 digits) =====================
    state.ws_edit_variable_name = "SSN 4th & 5th chars"
    state.ws_edit_alphanum_only = state.acup_new_cust_ssn_2
    state.ws_edit_alphanum_length = 2
    state.flg_alphanum_isvalid = False

    edit_num_reqd_1245(state)

    if state.flg_alphanum_isvalid:
        state.ws_edit_us_ssn_part2_flgs = "ISVALID"
    elif state.flg_alphanum_blank:
        state.ws_edit_us_ssn_part2_flgs = "BLANK"
    else:
        state.ws_edit_us_ssn_part2_flgs = "NOT-OK"

    if state.flg_alphanum_isvalid:
        part2 = state.acup_new_cust_ssn_2.strip()
        if int(part2) == 0:
            state.flg_edit_us_ssn_part2_not_ok = True
            state.input_error = True

    # ===================== Part 3 (4 digits) =====================
    state.ws_edit_variable_name = "SSN Last 4 chars"
    state.ws_edit_alphanum_only = state.acup_new_cust_ssn_3
    state.ws_edit_alphanum_length = 4
    state.flg_alphanum_isvalid = False

    edit_num_reqd_1245(state)

    if state.flg_alphanum_isvalid:
        state.ws_edit_us_ssn_part3_flgs = "ISVALID"
    elif state.flg_alphanum_blank:
        state.ws_edit_us_ssn_part3_flgs = "BLANK"
    else:
        state.ws_edit_us_ssn_part3_flgs = "NOT-OK"

    if state.flg_alphanum_isvalid:
        part3 = state.acup_new_cust_ssn_3.strip()
        if int(part3) == 0:
            state.flg_edit_us_ssn_part3_not_ok = True
            state.input_error = True

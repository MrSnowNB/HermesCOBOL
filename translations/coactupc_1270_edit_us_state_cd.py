"""
coactupc_1270_edit_us_state_cd.py
Implements 1270-EDIT-US-STATE-CD paragraph.
"""


VALID_US_STATE_CODES = frozenset({
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
    "DC","PR","VI","GU","MP","AS","UM"
})
# COBOL: VALID-US-STATE-CODE condition (88-level table)
# Includes DC + US territories per NANP/USPS standard


def edit_us_state_cd():
    """1270-EDIT-US-STATE-CD"""
    state.us_state_code_to_edit = state.acup_new_cust_addr_state_cd

    if state.us_state_code_to_edit.strip().upper() not in VALID_US_STATE_CODES:
        state.input_error = True
        state.flg_state_not_ok = True
        if not state.ws_return_msg_off:
            state.ws_return_msg = (
                f"{state.ws_edit_variable_name.strip()}"
                ": is not a valid state code"
            )
        return  # GO TO 1270-EDIT-US-STATE-CD-EXIT

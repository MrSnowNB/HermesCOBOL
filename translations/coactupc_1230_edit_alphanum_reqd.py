"""
coactupc_1230_edit_alphanum_reqd.py

Evidence-based translation of 1230-EDIT-ALPHANUM-REQD paragraph.
Source: Redis COBOL IR query for "1230 EDIT ALPHANUM REQD"
"""

from translations.state import CarddemoState


def edit_alphanum_reqd_1230(state: CarddemoState) -> None:
    """
    1230-EDIT-ALPHANUM-REQD

    Note: COBOL source has typo FLG-ALPHNANUM-NOT-OK
    Normalized to flg_alphanum_not_ok in Python translation
    """

    # Always set first
    state.flg_alphanum_not_ok = True

    field_value = state.ws_edit_alphanum_only[:state.ws_edit_alphanum_length]

    # Blank check
    if not field_value.strip():
        state.input_error = True
        # TODO: flg_alphanum_blank not present in state.py
        return

    # Alphanumeric check (letters, digits, and spaces)
    all_alphanum = all(c.isalnum() or c == ' ' for c in field_value)

    if not all_alphanum:
        state.input_error = True
        state.flg_alphanum_not_ok = True
        return

    # All checks passed
    # TODO: flg_alphanum_isvalid not present in state.py
    state.flg_alphanum_isvalid = True

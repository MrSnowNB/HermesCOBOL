"""
coactupc_1240_edit_alphanum_opt.py

Evidence-based translation of 1240-EDIT-ALPHANUM-OPT paragraph.
Source: Redis COBOL IR query for "1240 EDIT ALPHANUM OPT"
"""

from translations.state import CarddemoState


def edit_alphanum_opt_1240(state: CarddemoState) -> None:
    """
    1240-EDIT-ALPHANUM-OPT

    Note: COBOL source has typo FLG-ALPHNANUM-*
    Normalized to flg_alphanum_* in Python translation
    """

    state.flg_alphanum_not_ok = True

    field = state.ws_edit_alphanum_only[:state.ws_edit_alphanum_length]

    # Blank = optional = valid
    if not field.strip():
        state.flg_alphanum_isvalid = True
        return

    # Non-blank: must be alphanumeric (letters + digits + space)
    all_alphanum = all(c.isalnum() or c == ' ' for c in field)

    if not all_alphanum:
        state.input_error = True
        state.flg_alphanum_not_ok = True
        return

    state.flg_alphanum_isvalid = True

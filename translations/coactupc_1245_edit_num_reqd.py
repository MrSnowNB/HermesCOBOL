"""
coactupc_1245_edit_num_reqd.py

Evidence-based translation of 1245-EDIT-NUM-REQD paragraph.
Source: Redis COBOL IR query for "1245 EDIT NUM REQD"
"""

from translations.state import CarddemoState


def edit_num_reqd_1245(state: CarddemoState) -> None:
    """
    1245-EDIT-NUM-REQD

    Note: 1245 is numeric-only but reuses alphanum flags
    per COBOL source — no separate numeric flag set exists
    """

    state.flg_alphanum_not_ok = True

    field = state.ws_edit_alphanum_only[:state.ws_edit_alphanum_length]

    # Blank check
    if not field.strip():
        state.input_error = True
        # TODO: flg_alphanum_blank not present in state.py
        return

    # Second IF...CONTINUE in COBOL is a no-op here
    # (we already returned on blank above)

    # Must be strictly ASCII digits 0-9
    all_numeric = all(c.isdigit() for c in field)

    if not all_numeric:
        state.input_error = True
        state.flg_alphanum_not_ok = True
        return

    state.flg_alphanum_isvalid = True

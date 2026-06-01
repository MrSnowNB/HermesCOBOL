"""
coactupc_1235_edit_alpha_opt.py

Evidence-based translation of 1235-EDIT-ALPHA-OPT paragraph.
Source: Redis COBOL IR query for "1235 EDIT ALPHA OPT"
"""

from translations.state import CarddemoState


def edit_alpha_opt_1235(state: CarddemoState) -> None:
    """
    1235-EDIT-ALPHA-OPT

    Corrected logic from IR:
        SET FLG-ALPHA-NOT-OK TO TRUE
        IF WS-EDIT-ALPHANUM-ONLY(...) is blank (LOW-VALUES)
            SET FLG-ALPHA-ISVALID TO TRUE
            GO TO 1235-EDIT-ALPHA-OPT-EXIT
        # Non-blank: must pass alpha check
        INSPECT ...
    """

    state.flg_alpha_not_ok = True

    field = state.ws_edit_alphanum_only[:state.ws_edit_alphanum_length]

    # Blank = optional = valid (this is what makes it OPT)
    if not field.strip():
        state.flg_alpha_isvalid = True
        return  # GO TO 1235-EDIT-ALPHA-OPT-EXIT

    # Non-blank content must be all alphabetic
    all_alpha = all(c.isalpha() or c == ' ' for c in field)

    if not all_alpha:
        state.input_error = True
        state.flg_alpha_not_ok = True
        return

    state.flg_alpha_isvalid = True

"""
coactupc_1225_edit_alpha_reqd.py

Evidence-based translation of 1225-EDIT-ALPHA-REQD paragraph.
Source: Redis COBOL IR query for "1225 EDIT ALPHA REQD"
"""

from translations.state import CarddemoState


def edit_alpha_reqd_1225(state: CarddemoState) -> None:
    """
    1225-EDIT-ALPHA-REQD

    Logic (per IR + clarification):
        SET FLG-ALPHA-NOT-OK TO TRUE
        IF WS-EDIT-ALPHANUM-ONLY(1:WS-EDIT-ALPHANUM-LENGTH) is blank
            SET INPUT-ERROR TO TRUE
            SET FLG-ALPHA-BLANK TO TRUE
            GO TO 1225-EDIT-ALPHA-REQD-EXIT

        INSPECT WS-EDIT-ALPHANUM-ONLY(1:WS-EDIT-ALPHANUM-LENGTH)
            checking all characters are alphabetic or space

        IF not all alphabetic:
            SET INPUT-ERROR TO TRUE
            SET FLG-ALPHA-NOT-OK TO TRUE
            GO TO EXIT

        SET FLG-ALPHA-ISVALID TO TRUE
    """

    # Always set first
    state.flg_alpha_not_ok = True

    field_value = state.ws_edit_alphanum_only[:state.ws_edit_alphanum_length]

    # Blank check
    if not field_value.strip():
        state.input_error = True
        # TODO: flg_alpha_blank not present in state.py
        return

    # INSPECT logic: all characters must be alphabetic or space
    # (MOVE LIT-ALL-ALPHA-FROM-X is WS setup only - not modeled)
    all_alpha = all(c.isalpha() or c == ' ' for c in field_value)

    if not all_alpha:
        state.input_error = True
        state.flg_alpha_not_ok = True
        return

    # All checks passed
    # TODO: flg_alpha_isvalid not present in state.py
    state.flg_alpha_isvalid = True

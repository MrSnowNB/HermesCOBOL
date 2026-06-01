"""
coactupc_1220_edit_yesno.py

Evidence-based translation of 1220-EDIT-YESNO paragraph.
Source: Redis COBOL IR query for "1220 EDIT YESNO yes no validation"
"""

from translations.state import CarddemoState


def edit_yesno_1220(state: CarddemoState) -> None:
    """
    1220-EDIT-YESNO

    Original COBOL IR logic:
        IF WS-EDIT-YES-NO EQUAL LOW-VALUES
            SET INPUT-ERROR TO TRUE
            SET FLG-YES-NO-BLANK TO TRUE
            IF WS-RETURN-MSG-OFF STRING GO TO 1220-EDIT-YESNO-EXIT

        IF FLG-YES-NO-ISVALID
            CONTINUE
        ELSE
            SET INPUT-ERROR TO TRUE
            SET FLG-YES-NO-NOT-OK TO TRUE
    """

    # LOW-VALUES check approximated as empty / whitespace-only
    # (LOW-VALUES in COBOL = null bytes / empty string)
    yes_no_value = state.ws_edit_yes_no or ""
    if not yes_no_value.strip():
        state.input_error = True
        # TODO: flg_yes_no_blank not present in state.py
        # Early return for GO TO 1220-EDIT-YESNO-EXIT
        return

    # IF FLG-YES-NO-ISVALID CONTINUE pattern
    # (if already valid, fall through / do nothing)
    if not state.flg_yes_no_isvalid:
        state.input_error = True
        # TODO: flg_yes_no_not_ok not present in state.py
        return

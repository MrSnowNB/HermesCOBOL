"""
coactupc_1215_edit_mandatory.py

Evidence-based translation of 1215-EDIT-MANDATORY paragraph.
Source: Redis COBOL IR query for "1215 EDIT MANDATORY field validation"
"""

from translations.state import CarddemoState


def edit_mandatory_1215(state: CarddemoState) -> None:
    """
    1215-EDIT-MANDATORY

    Original COBOL IR (exact):
        SET FLG-MANDATORY-NOT-OK TO TRUE
        IF WS-EDIT-ALPHANUM-ONLY(1:WS-EDIT-ALPHANUM-LENGTH)
            SET INPUT-ERROR TO TRUE
            SET FLG-MANDATORY-BLANK TO TRUE
            IF WS-RETURN-MSG-OFF
                STRING
                GO TO 1215-EDIT-MANDATORY-EXIT
        SET FLG-MANDATORY-ISVALID TO TRUE
    """

    state.flg_mandatory_not_ok = True

    # Proper substring check using fields from state.py
    edit_length = state.ws_edit_alphanum_length
    field_value = state.ws_edit_alphanum_only

    # Check if the field is effectively blank/invalid using the length-bounded substring
    if not field_value or field_value[:edit_length].strip() == "":
        state.flg_mandatory_blank = True
        state.input_error = True          # Set the real INPUT-ERROR flag
        # Early return = GO TO 1215-EDIT-MANDATORY-EXIT
        return

    # Reached only if the mandatory check passed
    state.flg_mandatory_isvalid = True

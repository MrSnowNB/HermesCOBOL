"""
coactupc_1215_edit_mandatory.py

Evidence-based translation of 1215-EDIT-MANDATORY paragraph.
Source: Redis COBOL IR query for "1215 EDIT MANDATORY field validation"
Query returned paragraph 1215-EDIT-MANDATORY as top result.

Strict constraints followed:
- Accepts full CarddemoState from translations/state.py
- Uses only fields that exist in state.py (TODO comments for missing ones)
- GO TO XXX-EXIT translated as early return
- No invented field names
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

    # Existing fields in CarddemoState (from state.py)
    state.flg_mandatory_not_ok = True

    # TODO: WS-EDIT-ALPHANUM-LENGTH is not defined in CarddemoState
    # TODO: INPUT-ERROR is not defined in CarddemoState (input_ok exists but inverse not modeled)
    # TODO: WS-RETURN-MSG-OFF logic not modeled in state.py

    # Current available fields:
    #   state.ws_edit_alphanum_only
    #   state.flg_mandatory_blank
    #   state.flg_mandatory_isvalid

    # Placeholder logic based strictly on retrieved IR (incomplete)
    # The original performs a substring check on WS-EDIT-ALPHANUM-ONLY(1:WS-EDIT-ALPHANUM-LENGTH)
    # Since WS-EDIT-ALPHANUM-LENGTH is missing, we cannot replicate the exact condition.

    if not state.ws_edit_alphanum_only or state.ws_edit_alphanum_only.strip() == "":
        state.flg_mandatory_blank = True
        # TODO: Set INPUT-ERROR equivalent when field is added to state.py
        # Early return = GO TO 1215-EDIT-MANDATORY-EXIT
        return

    # If we reach here without early return, mark as valid
    state.flg_mandatory_isvalid = True

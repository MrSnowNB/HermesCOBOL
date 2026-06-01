"""
coactupc_1250_edit_signed_9v2.py

Evidence-based translation of 1250-EDIT-SIGNED-9V2 paragraph.
Source: Redis COBOL IR query for "1250 EDIT SIGNED 9V2"
"""

import re
from translations.state import CarddemoState


# COBOL equivalent: FUNCTION TEST-NUMVAL-C(field) = 0
# 9V2 = up to 9 digits, 2 decimal places, signed allowed
def is_valid_signed_numval_c(value: str) -> bool:
    """
    Approximates COBOL FUNCTION TEST-NUMVAL-C.
    Accepts: optional leading +/-, digits, optional decimal point.
    Rejects: letters, symbols, multiple signs, multiple decimals.
    """
    stripped = value.strip()
    if not stripped:
        return False
    pattern = r'^[+-]?\d{1,9}(\.\d{1,2})?$'
    return bool(re.match(pattern, stripped))


def edit_signed_9v2_1250(state: CarddemoState) -> None:
    """
    1250-EDIT-SIGNED-9V2
    """

    state.flg_signed_number_not_ok = True

    field = state.ws_edit_signed_number_9v2_x.strip()

    # Blank / LOW-VALUES check
    if not field or field == '\x00' * len(field):
        state.input_error = True
        # TODO: flg_signed_number_blank not present in state.py
        return

    if not is_valid_signed_numval_c(field):
        state.input_error = True
        state.flg_signed_number_not_ok = True
        return

    # TODO: flg_signed_number_isvalid not present in state.py
    state.flg_signed_number_isvalid = True

"""
coactupc_1280_edit_us_state_zip_cd.py
Implements 1280-EDIT-US-STATE-ZIP-CD paragraph.
"""

from state import state

# COBOL: VALID-US-STATE-ZIP-CD2-COMBO condition
# Source: USPS ZIP Code prefix assignments by state
STATE_ZIP2_RANGES = {
    "AL": [(35, 36)],
    "AK": [(99, 99)],
    "AZ": [(85, 86)],
    "AR": [(71, 72)],
    "CA": [(90, 96)],
    "CO": [(80, 81)],
    "CT": [(6, 6)],
    "DE": [(19, 19)],
    "FL": [(32, 34)],
    "GA": [(30, 31)],
    "HI": [(96, 96)],
    "ID": [(83, 83)],
    "IL": [(60, 62)],
    "IN": [(46, 47)],
    "IA": [(50, 52)],
    "KS": [(66, 67)],
    "KY": [(40, 42)],
    "LA": [(70, 71)],
    "ME": [(3, 4)],
    "MD": [(20, 21)],
    "MA": [(1, 2)],
    "MI": [(48, 49)],
    "MN": [(55, 56)],
    "MS": [(38, 39)],
    "MO": [(63, 65)],
    "MT": [(59, 59)],
    "NE": [(68, 69)],
    "NV": [(88, 89)],
    "NH": [(3, 3)],
    "NJ": [(7, 8)],
    "NM": [(87, 88)],
    "NY": [(10, 14)],
    "NC": [(27, 28)],
    "ND": [(58, 58)],
    "OH": [(43, 45)],
    "OK": [(73, 74)],
    "OR": [(97, 97)],
    "PA": [(15, 19)],
    "RI": [(2, 2)],
    "SC": [(29, 29)],
    "SD": [(57, 57)],
    "TN": [(37, 38)],
    "TX": [(75, 79)],
    "UT": [(84, 84)],
    "VT": [(5, 5)],
    "VA": [(20, 24)],
    "WA": [(98, 99)],
    "WV": [(24, 26)],
    "WI": [(53, 54)],
    "WY": [(82, 83)],
    "DC": [(20, 20)],
    "PR": [(0, 0)],   # 00xxx
}


def is_valid_state_zip2_combo(state_cd: str, zip2: str) -> bool:
    """
    COBOL: VALID-US-STATE-ZIP-CD2-COMBO condition
    Checks if first 2 digits of ZIP are valid for given state.
    Based on USPS ZIP prefix ranges.
    """
    sc = state_cd.strip().upper()
    if not zip2.strip().isdigit():
        return False
    zp = int(zip2.strip().zfill(2))
    ranges = STATE_ZIP2_RANGES.get(sc, [])
    return any(lo <= zp <= hi for lo, hi in ranges)


def edit_us_state_zip_cd():
    """1280-EDIT-US-STATE-ZIP-CD"""
    if not is_valid_state_zip2_combo(
        state.acup_new_cust_addr_state_cd,
        state.acup_new_cust_addr_zip[:2]
    ):
        state.input_error = True
        state.flg_state_not_ok = True
        state.flg_zipcode_not_ok = True
        if not state.ws_return_msg_off:
            state.ws_return_msg = "Invalid zip code for state"
        return  # GO TO 1280-EDIT-US-STATE-ZIP-CD-EXIT

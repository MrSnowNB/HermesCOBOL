from translations.state import CarddemoState
from translations.coactupc_1100_receive_map import coactupc_1100_receive_map
from translations.coactupc_1200_edit_map_inputs import coactupc_1200_edit_map_inputs

def coactupc_1000_process_inputs(state: CarddemoState) -> None:
    """1000-PROCESS-INPUTS - 6 statements translated from COBOL IR."""

    # seq=53: PERFORM 1100-RECEIVE-MAP
    coactupc_1100_receive_map(state)

    # seq=54: PERFORM 1200-EDIT-MAP-INPUTS
    coactupc_1200_edit_map_inputs(state)

    # seq=55: MOVE WS-RETURN-MSG TO CCARD-ERROR-MSG
    state.cc_work_areas_cc_work_area_ccard_error_msg = state.ws_misc_storage_ws_return_msg

    # seq=56: MOVE LIT-THISPGM TO CCARD-NEXT-PROG
    state.cc_work_areas_cc_work_area_ccard_next_prog = state.ws_literals_lit_thispgm

    # seq=57: MOVE LIT-THISMAPSET TO CCARD-NEXT-MAPSET
    state.cc_work_areas_cc_work_area_ccard_next_mapset = state.ws_literals_lit_thismapset

    # seq=58: MOVE LIT-THISMAP TO CCARD-NEXT-MAP
    state.cc_work_areas_cc_work_area_ccard_next_map = state.ws_literals_lit_thismap


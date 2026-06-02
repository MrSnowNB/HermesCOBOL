import pytest
from translations.state import CarddemoState
from translations import (
    coactupc_0000_main,
    coactupc_1000_process_inputs,
    coactupc_1100_receive_map,
    coactupc_1200_edit_map_inputs,
    coactupc_1205_compare_old_new,
)


# ============================================================================
# 1200-EDIT-MAP-INPUTS tests
# ============================================================================

def test_1200_sets_input_ok_true():
    """seq=1: SET INPUT-OK TO TRUE"""
    state = CarddemoState()
    coactupc_1200_edit_map_inputs.coactupc_1200_edit_map_inputs(state)
    assert state.input_ok is True


def test_1200_details_not_fetched_returns_early():
    """Early return at seq=8 when ACUP-DETAILS-NOT-FETCHED"""
    state = CarddemoState()
    state.acup_details_not_fetched = True
    coactupc_1200_edit_map_inputs.coactupc_1200_edit_map_inputs(state)
    assert state.found_account_data is False


def test_1200_no_changes_found_returns_early():
    """Early return at seq=19 when NO-CHANGES-FOUND"""
    state = CarddemoState()
    state.acup_details_not_fetched = False
    state.no_changes_found = True
    coactupc_1200_edit_map_inputs.coactupc_1200_edit_map_inputs(state)
    assert state.acup_changes_not_ok is False


def test_1200_happy_path_sets_flags():
    """seq=11-21: happy path sets account + customer flags"""
    state = CarddemoState()
    state.acup_details_not_fetched = False
    state.no_changes_found = False
    coactupc_1200_edit_map_inputs.coactupc_1200_edit_map_inputs(state)
    assert state.found_account_data is True
    assert state.found_acct_in_master is True
    assert state.flg_acctfilter_isvalid is True
    assert state.found_cust_in_master is True
    assert state.flg_custfilter_isvalid is True
    assert state.acup_changes_not_ok is True


def test_1200_active_status_copied_to_edit_yes_no():
    """seq=23: MOVE ACUP-NEW-ACTIVE-STATUS TO WS-EDIT-YES-NO"""
    state = CarddemoState()
    state.acup_details_not_fetched = False
    state.no_changes_found = False
    state.ws_this_progcommarea_acup_new_details_acup_new_acct_data_acup_new_active_status = "Y"
    coactupc_1200_edit_map_inputs.coactupc_1200_edit_map_inputs(state)
    assert state.ws_misc_storage_ws_generic_edits_ws_edit_yes_no == "Y"


# ============================================================================
# 0000-MAIN smoke tests
# ============================================================================

def test_0000_main_smoke():
    state = CarddemoState()
    coactupc_0000_main.coactupc_0000_main(state)


def test_0000_main_with_tranid():
    state = CarddemoState()
    state.ws_literals_lit_thistranid = "ACUP"
    coactupc_0000_main.coactupc_0000_main(state)
    assert state is not None


# ============================================================================
# 1000-PROCESS-INPUTS smoke tests
# ============================================================================

def test_1000_process_inputs_smoke():
    state = CarddemoState()
    coactupc_1000_process_inputs.coactupc_1000_process_inputs(state)


def test_1000_process_inputs_sets_return_msg():
    state = CarddemoState()
    coactupc_1000_process_inputs.coactupc_1000_process_inputs(state)
    assert state is not None


# ============================================================================
# 1100-RECEIVE-MAP smoke tests
# ============================================================================

def test_1100_receive_map_smoke():
    state = CarddemoState()
    coactupc_1100_receive_map.coactupc_1100_receive_map(state)


def test_1100_receive_map_with_mapname():
    state = CarddemoState()
    state.ws_literals_lit_thismap = "ACUPMAP"
    coactupc_1100_receive_map.coactupc_1100_receive_map(state)
    assert state is not None

# 1205-COMPARE-OLD-NEW tests
def test_1205_no_changes_sets_no_changes_found():
    state = CarddemoState()
    coactupc_1205_compare_old_new.coactupc_1205_compare_old_new(state)
    assert state.no_changes_found is True
    assert state.change_has_occurred is False

def test_1205_acct_field_diff_triggers_change():
    state = CarddemoState()
    state.acup_new_acct_id_x = "NEW"
    state.acup_old_acct_id_x = "OLD"
    coactupc_1205_compare_old_new.coactupc_1205_compare_old_new(state)
    assert state.change_has_occurred is True

def test_1205_cust_field_diff_triggers_change():
    state = CarddemoState()
    state.acup_new_acct_id_x = state.acup_old_acct_id_x = "SAME"
    state.acup_new_cust_first_name = "JOHN"
    state.acup_old_cust_first_name = "JANE"
    coactupc_1205_compare_old_new.coactupc_1205_compare_old_new(state)
    assert state.change_has_occurred is True

def test_1205_no_changes_detected_on_full_match():
    state = CarddemoState()
    coactupc_1205_compare_old_new.coactupc_1205_compare_old_new(state)
    assert state.no_changes_detected is True


# ============================================================================
# 9200-GETCARDXREF-BYACCT tests
# ============================================================================

def test_getcardxref_byacct_normal():
    from translations.state import CarddemoState
    from translations.coactupc_9xxx_stubs import getcardxref_byacct, DFHRESP_NORMAL
    state = CarddemoState()
    state.ws_card_rid_acct_id = "ACCT001"
    state.card_xref_db = {
        "ACCT001": {"xref_cust_id": "CUST99", "xref_card_num": "4111111111111111"}
    }
    getcardxref_byacct(state)
    assert state.ws_resp_cd == DFHRESP_NORMAL
    assert state.cdemo_cust_id == "CUST99"
    assert state.cdemo_card_num == "4111111111111111"
    assert state.input_error == False
    assert state.flg_acctfilter_not_ok == False


def test_getcardxref_byacct_notfnd():
    from translations.state import CarddemoState
    from translations.coactupc_9xxx_stubs import getcardxref_byacct, DFHRESP_NOTFND
    state = CarddemoState()
    state.ws_card_rid_acct_id = "MISSING"
    state.card_xref_db = {}
    state.ws_return_msg_off = True
    state.ws_reas_cd = 0
    getcardxref_byacct(state)
    assert state.ws_resp_cd == DFHRESP_NOTFND
    assert state.input_error == True
    assert state.flg_acctfilter_not_ok == True
    assert "MISSING" in state.ws_return_msg
    assert "not found" in state.ws_return_msg


def test_getcardxref_byacct_other():
    from translations.state import CarddemoState
    from translations.coactupc_9xxx_stubs import getcardxref_byacct
    state = CarddemoState()
    state.ws_card_rid_acct_id = "ACCT001"
    state.card_xref_db = None  # will trigger TypeError on 'in' check
    state.lit_cardxrefname_acct_path = "CARDXREF"
    state.ws_file_error_message = "FILE ERROR"
    state.ws_reas_cd = 0
    getcardxref_byacct(state)
    assert state.ws_resp_cd == -1
    assert state.input_error == True
    assert state.flg_acctfilter_not_ok == True
    assert state.error_opname == "READ"
    assert state.error_file == "CARDXREF"
    assert state.ws_return_msg == "FILE ERROR"

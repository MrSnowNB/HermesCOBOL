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


# ============================================================================
# 9300-GETACCTDATA-BYACCT tests
# ============================================================================

def test_getacctdata_byacct_normal():
    from translations.state import CarddemoState
    from translations.coactupc_9xxx_stubs import getacctdata_byacct
    state = CarddemoState()
    state.acct_db = {"0000000000000001": {"acct_id": "0000000000000001"}}
    state.ws_card_rid_acct_id = "0000000000000001"
    state.ws_return_msg_off = True

    getacctdata_byacct(state)

    assert state.found_acct_in_master is True
    assert state.input_error is False
    assert state.flg_acctfilter_not_ok is False


def test_getacctdata_byacct_notfnd():
    from translations.state import CarddemoState
    from translations.coactupc_9xxx_stubs import getacctdata_byacct
    state = CarddemoState()
    state.acct_db = {}
    state.ws_card_rid_acct_id = "0000000000000001"
    state.ws_return_msg_off = True

    getacctdata_byacct(state)

    assert state.found_acct_in_master is False
    assert state.input_error is True
    assert state.flg_acctfilter_not_ok is True
    assert "not found in Acct Master file" in state.ws_return_msg


def test_getacctdata_byacct_other():
    from translations.state import CarddemoState
    from translations.coactupc_9xxx_stubs import getacctdata_byacct
    state = CarddemoState()
    state.acct_db = None  # force exception
    state.ws_card_rid_acct_id = "0000000000000001"
    state.lit_acctfilename = "ACCTDAT"
    state.ws_return_msg_off = True
def test_read_acct_exits_after_9300_on_acctfilter_not_ok():
    from translations.state import CarddemoState
    from translations.coactupc_9000_read_acct import read_acct
    state = CarddemoState()
    state.cc_acct_id = "ACCT001"
    state.card_xref_db = {
        "ACCT001": {"xref_cust_id": "C1", "xref_card_num": "4111"}
    }
    state.acct_db = {}  # triggers NOTFND in 9300
    state.ws_return_msg_off = False
    read_acct(state)
    assert state.flg_acctfilter_not_ok == True
    assert state.ws_card_rid_cust_id == ""



def test_getcustdata_bycust_normal():
    from translations.state import CarddemoState
    from translations.coactupc_9xxx_stubs import getcustdata_bycust
    state = CarddemoState()
    state.cust_db = {"CUST001": {"cust_id": "CUST001"}}
    state.ws_card_rid_cust_id = "CUST001"
    state.ws_return_msg_off = True

    getcustdata_bycust(state)

    assert state.found_cust_in_master is True
    assert state.input_error is False
    assert state.flg_custfilter_not_ok is False


def test_getcustdata_bycust_notfnd():
    from translations.state import CarddemoState
    from translations.coactupc_9xxx_stubs import getcustdata_bycust
    state = CarddemoState()
    state.cust_db = {}
    state.ws_card_rid_cust_id = "CUST001"
    state.ws_return_msg_off = True

    getcustdata_bycust(state)

    assert state.found_cust_in_master is False
    assert state.input_error is True
    assert state.flg_custfilter_not_ok is True
    assert "not found in customer master" in state.ws_return_msg


def test_getcustdata_bycust_other():
    from translations.state import CarddemoState
    from translations.coactupc_9xxx_stubs import getcustdata_bycust
    state = CarddemoState()
    state.cust_db = None  # force exception
    state.ws_card_rid_cust_id = "CUST001"
    state.lit_custfilename = "CUSTDAT"
    state.ws_return_msg_off = True

    getcustdata_bycust(state)

    assert state.ws_resp_cd == -1
    assert state.input_error is True
    assert state.flg_custfilter_not_ok is True
    assert state.error_opname == "READ"
    assert state.error_file == "CUSTDAT"


def test_read_acct_exits_after_9400_on_custfilter_not_ok():
    from translations.state import CarddemoState
    from translations.coactupc_9000_read_acct import read_acct
    state = CarddemoState()
    state.cc_acct_id = "ACCT001"
    state.card_xref_db = {
        "ACCT001": {"xref_cust_id": "C1", "xref_card_num": "4111"}
    }
    state.acct_db = {"ACCT001": {}}
    state.cust_db = {}  # triggers NOTFND in 9400
    state.ws_return_msg_off = False
    read_acct(state)
    assert state.flg_custfilter_not_ok == True
    # store_fetched_data must NOT have run
    assert state.acup_old_details == {}



def test_store_fetched_data_full_path():
    from translations.state import CarddemoState
    from translations.coactupc_9xxx_stubs import store_fetched_data
    state = CarddemoState()

    state.acct_db = {
        "ACCT001": {
            "acct_id": "ACCT001",
            "acct_active_status": "Y",
            "acct_curr_bal": "1000.00",
            "acct_credit_limit": "5000.00",
            "acct_cash_credit_limit": "2000.00",
            "acct_curr_cyc_credit": "300.00",
            "acct_curr_cyc_debit": "150.00",
            "acct_open_date": "2019-06-15",
            "acct_expiration_date": "2024-06-15",
            "acct_reissue_date": "2022-06-15",
            "acct_group_id": "GRP01"
        }
    }
    state.cust_db = {
        "CUST001": {
            "cust_id": "CUST001",
            "cust_first_name": "John",
            "cust_middle_name": "M",
            "cust_last_name": "Doe",
            "cust_ssn": "123456789",
            "cust_dob_yyyy_mm_dd": "1985-03-20",
            "cust_fico_credit_score": "750",
            "cust_addr_line_1": "123 Main St",
            "cust_addr_line_2": "",
            "cust_addr_line_3": "",
            "cust_addr_state_cd": "NY",
            "cust_addr_country_cd": "US",
            "cust_addr_zip": "10001",
            "cust_phone_num_1": "555-1234",
            "cust_phone_num_2": "",
            "cust_govt_issued_id": "ABC123",
            "cust_eft_account_id": "EFT001",
            "cust_pri_card_holder_ind": "Y"
        }
    }
    state.card_xref_db = {
        "ACCT001": {"xref_card_num": "4111111111111111"}
    }

    state.ws_card_rid_acct_id = "ACCT001"
    state.ws_card_rid_cust_id = "CUST001"

    store_fetched_data(state)

    assert state.cdemo_acct_id == "ACCT001"
    assert state.cdemo_cust_id == "CUST001"
    assert state.cdemo_card_num == "4111111111111111"
    assert state.acup_old_active_status == "Y"
    assert state.acup_old_open_year == "2019"
    assert state.acup_old_open_mon == "06"
    assert state.acup_old_open_day == "15"
    assert state.acup_old_cust_first_name == "John"
    assert state.acup_old_cust_dob_year == "1985"


def test_store_fetched_data_date_slicing():
    # Standalone date slicing test
    date_str = "2019-06-15"
    assert date_str[0:4] == "2019"
    assert date_str[5:7] == "06"
    assert date_str[8:10] == "15"


def test_store_fetched_data_minimal():
    from translations.state import CarddemoState
    from translations.coactupc_9xxx_stubs import store_fetched_data
    state = CarddemoState()
    state.acct_db = {"ACCT001": {"acct_id": "ACCT001"}}
    state.cust_db = {"CUST001": {"cust_id": "CUST001"}}
    state.card_xref_db = {"ACCT001": {}}
    state.ws_card_rid_acct_id = "ACCT001"
    state.ws_card_rid_cust_id = "CUST001"

    store_fetched_data(state)

    assert state.cdemo_acct_id == "ACCT001"
    assert state.acup_old_acct_id == "ACCT001"



def _make_write_state():
    from translations.state import CarddemoState
    s = CarddemoState()
    s.cc_acct_id = "ACCT001"
    s.cdemo_cust_id = "CUST001"
    s.acct_db = {"ACCT001": {"acct_id": "ACCT001"}}
    s.cust_db = {"CUST001": {"cust_id": "CUST001"}}
    s.ws_return_msg_off = True
    s.data_was_changed_before_update = False
    # Populate required ACUP-NEW-* fields minimally
    s.acup_new_acct_id = "ACCT001"
    s.acup_new_active_status = "Y"
    s.acup_new_curr_bal = "1000.00"
    s.acup_new_credit_limit = "5000.00"
    s.acup_new_cash_credit_limit = "2000.00"
    s.acup_new_curr_cyc_credit = "100.00"
    s.acup_new_curr_cyc_debit = "50.00"
    s.acup_new_open_year = "2020"
    s.acup_new_open_mon = "01"
    s.acup_new_open_day = "15"
    s.acup_new_exp_year = "2025"
    s.acup_new_exp_mon = "12"
    s.acup_new_exp_day = "31"
    s.acup_new_reissue_year = "2022"
    s.acup_new_reissue_mon = "06"
    s.acup_new_reissue_day = "01"
    s.acup_new_group_id = "GRP01"
    s.acup_new_cust_id = "CUST001"
    s.acup_new_cust_first_name = "John"
    s.acup_new_cust_middle_name = "M"
    s.acup_new_cust_last_name = "Doe"
    s.acup_new_cust_addr_line_1 = "123 Main St"
    s.acup_new_cust_addr_line_2 = ""
    s.acup_new_cust_addr_line_3 = ""
    s.acup_new_cust_addr_state_cd = "NY"
    s.acup_new_cust_addr_country_cd = "US"
    s.acup_new_cust_addr_zip = "10001"
    s.acup_new_cust_phone_num_1a = "555"
    s.acup_new_cust_phone_num_1b = "123"
    s.acup_new_cust_phone_num_1c = "4567"
    s.acup_new_cust_phone_num_2a = "555"
    s.acup_new_cust_phone_num_2b = "987"
    s.acup_new_cust_phone_num_2c = "6543"
    s.acup_new_cust_ssn = "123456789"
    s.acup_new_cust_govt_issued_id = "GOV123"
    s.acup_new_cust_dob_year = "1980"
    s.acup_new_cust_dob_mon = "05"
    s.acup_new_cust_dob_day = "20"
    s.acup_new_cust_eft_account_id = "EFT001"
    s.acup_new_cust_pri_holder_ind = "Y"
    s.acup_new_cust_fico_score = "750"
    return s


def test_write_processing_normal():
    from translations.coactupc_9600_write_processing import write_processing
    s = _make_write_state()
    write_processing(s)
    assert s.locked_but_update_failed == False
    assert s.acct_update_id == "ACCT001"
    assert s.cust_update_first_name == "John"
    assert s.acct_update_open_date == "2020-01-15"
    assert s.cust_update_phone_num_1 == "(555)123-4567"
    assert s.cust_update_dob_yyyy_mm_dd == "1980-05-20"
    assert s.acct_db["ACCT001"] == s.acct_update_record
    assert s.cust_db["CUST001"] == s.cust_update_record


def test_write_processing_acct_lock_fail():
    from translations.coactupc_9600_write_processing import write_processing
    s = _make_write_state()
    s.acct_db = {}  # key missing → lock fail
    write_processing(s)
    assert s.input_error == True
    assert s.could_not_lock_acct_for_update == True


def test_write_processing_cust_lock_fail():
    from translations.coactupc_9600_write_processing import write_processing
    s = _make_write_state()
    s.cust_db = {}  # key missing → lock fail
    write_processing(s)
    assert s.input_error == True
    assert s.could_not_lock_cust_for_update == True


def test_write_processing_data_changed():
    from translations.coactupc_9600_write_processing import write_processing
    s = _make_write_state()
    s.data_was_changed_before_update = True
    write_processing(s)
    assert s.locked_but_update_failed == False
    # acct_db and cust_db must be untouched
    assert s.acct_db["ACCT001"] == {"acct_id": "ACCT001"}
    assert s.cust_db["CUST001"] == {"cust_id": "CUST001"}


def test_write_processing_acct_rewrite_fail():
    from translations.coactupc_9600_write_processing import write_processing
    s = _make_write_state()
    class FailOnWrite(dict):
        def __setitem__(self, k, v):
            raise RuntimeError("write fail")
    s.acct_db = FailOnWrite({"ACCT001": {}})
    write_processing(s)
    assert s.locked_but_update_failed == True


def test_write_processing_cust_rewrite_fail_rollback():
    from translations.coactupc_9600_write_processing import write_processing
    original = {"acct_id": "ACCT001", "original": True}
    s = _make_write_state()
    s.acct_db = {"ACCT001": original.copy()}
    class FailOnWrite(dict):
        def __setitem__(self, k, v):
            if k == "CUST001":
                raise RuntimeError("cust write fail")
            super().__setitem__(k, v)
    s.cust_db = FailOnWrite({"CUST001": {}})
    write_processing(s)
    assert s.locked_but_update_failed == True
    assert s.acct_db["ACCT001"] == original


def test_write_processing_date_assembly():
    from translations.coactupc_9600_write_processing import write_processing
    s = _make_write_state()
    write_processing(s)
    assert s.acct_update_open_date == "2020-01-15"
    assert s.acct_update_expiraion_date == "2025-12-31"
    assert s.acct_update_reissue_date == "2022-06-01"
    assert s.cust_update_dob_yyyy_mm_dd == "1980-05-20"

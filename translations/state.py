from dataclasses import dataclass
from typing import Any


@dataclass
class CarddemoState:
    """Shared mutable state for COACTUPC paragraph translations.

    All fields derived strictly from "reads" and "mutates" arrays returned by
    the Honcho API for the three paragraphs. No additional fields invented.
    Only flat leaf fields are kept (group-level Dict containers removed to
    eliminate collisions between parent and child fields).

    Field origin documentation (paragraph that first contributes the field via read or mutate):

    0000-MAIN contributes:
      - ws_literals_lit_thistranid (reads)
      - ws_literals_lit_menupgm (reads)
      - dfhcommarea (reads)
      - carddemo_commarea_cdemo_general_info_cdemo_from_tranid (reads)
      - ws_misc_storage_ws_cics_processng_vars_ws_tranid (mutates)
      - carddemo_commarea_cdemo_general_info_cdemo_to_tranid (mutates)
      - carddemo_commarea_cdemo_general_info_cdemo_to_program (mutates)
      - ws_commarea (mutates)

    1000-PROCESS-INPUTS contributes:
      - ws_misc_storage_ws_return_msg (reads)
      - ws_literals_lit_thispgm (reads)
      - ws_literals_lit_thismapset (reads)
      - ws_literals_lit_thismap (reads)
      - cc_work_areas_cc_work_area_ccard_error_msg (mutates)
      - cc_work_areas_cc_work_area_ccard_next_prog (mutates)
      - cc_work_areas_cc_work_area_ccard_next_mapset (mutates)
      - cc_work_areas_cc_work_area_ccard_next_map (mutates)

    1200-EDIT-MAP-INPUTS contributes:
      - ws_this_progcommarea_acup_new_details_acup_new_acct_data_acup_new_active_status (reads)
      - ws_misc_storage_ws_generic_edits_ws_edit_yes_no (reads + mutates)
      - ws_this_progcommarea_acup_new_details_acup_new_acct_data_acup_new_open_date (reads)
      - ws_misc_storage_alpha_vars_for_data_editing_acup_new_credit_limit_x (reads)
      - ws_misc_storage_ws_generic_edits_ws_flg_signed_number_edit (reads)
      - ws_this_progcommarea_acup_new_details_acup_new_acct_data_acup_new_expiration_date (reads)
      - ws_this_progcommarea_acup_old_details_acup_old_acct_data (mutates)
      - ws_misc_storage_ws_non_key_flags (mutates)
      - ws_misc_storage_ws_generic_edits_ws_edit_variable_name (mutates)
      - ws_misc_storage_ws_non_key_flags_ws_edit_acct_status (mutates)
      - ws_misc_storage_ws_non_key_flags_ws_edit_open_date_flgs (mutates)
      - ws_misc_storage_ws_generic_edits_ws_edit_signed_number_9v2_x (mutates)
      - ws_misc_storage_ws_non_key_flags_ws_edit_credit_limit (mutates)
      - input_ok, acup_details_not_fetched, flg_acctfilter_blank, no_search_criteria_received,
        found_account_data, found_acct_in_master, flg_acctfilter_isvalid, found_cust_in_master,
        flg_custfilter_isvalid, no_changes_found, acup_changes_not_ok (all bool control flags)
    1200-EDIT-MAP-INPUTS contributes:
      - ws_this_progcommarea_acup_new_details_acup_new_acct_data_acup_new_active_status (reads)
      - ws_misc_storage_ws_generic_edits_ws_edit_yes_no (reads + mutates)
      - ws_this_progcommarea_acup_new_details_acup_new_acct_data_acup_new_open_date (reads)
      - ws_misc_storage_alpha_vars_for_data_editing_acup_new_credit_limit_x (reads)
      - ws_misc_storage_ws_generic_edits_ws_flg_signed_number_edit (reads)
      - ws_this_progcommarea_acup_new_details_acup_new_acct_data_acup_new_expiration_date (reads)
      - ws_this_progcommarea_acup_old_details_acup_old_acct_data (mutates)
      - ws_misc_storage_ws_non_key_flags_ws_edit_acct_status (mutates)
      - ws_misc_storage_ws_generic_edits_ws_edit_variable_name (mutates)
      - ws_misc_storage_ws_non_key_flags_ws_edit_open_date_flgs (mutates)
      - ws_misc_storage_ws_generic_edits_ws_edit_signed_number_9v2_x (mutates)
      - ws_misc_storage_ws_non_key_flags_ws_edit_credit_limit (mutates)
    """

    # Pure containers with no leaf children in the source data (kept as Any)
    dfhcommarea: Any = None
    ws_commarea: Any = None

    # 0000-MAIN leaf fields
    ws_literals_lit_thistranid: str = ""
    ws_literals_lit_menupgm: str = ""
    carddemo_commarea_cdemo_general_info_cdemo_from_tranid: str = ""
    ws_misc_storage_ws_cics_processng_vars_ws_tranid: str = ""
    carddemo_commarea_cdemo_general_info_cdemo_to_tranid: str = ""
    carddemo_commarea_cdemo_general_info_cdemo_to_program: str = ""

    # 1000-PROCESS-INPUTS leaf fields
    ws_misc_storage_ws_return_msg: str = ""
    ws_literals_lit_thispgm: str = ""
    ws_literals_lit_thismapset: str = ""
    ws_literals_lit_thismap: str = ""
    cc_work_areas_cc_work_area_ccard_error_msg: str = ""
    cc_work_areas_cc_work_area_ccard_next_prog: str = ""
    cc_work_areas_cc_work_area_ccard_next_mapset: str = ""
    cc_work_areas_cc_work_area_ccard_next_map: str = ""

    # 1200-EDIT-MAP-INPUTS leaf fields
    ws_this_progcommarea_acup_new_details_acup_new_acct_data_acup_new_active_status: str = ""
    ws_misc_storage_ws_generic_edits_ws_edit_yes_no: str = ""
    ws_this_progcommarea_acup_new_details_acup_new_acct_data_acup_new_open_date: str = ""
    ws_misc_storage_alpha_vars_for_data_editing_acup_new_credit_limit_x: str = ""
    ws_misc_storage_ws_generic_edits_ws_flg_signed_number_edit: str = ""
    ws_this_progcommarea_acup_new_details_acup_new_acct_data_acup_new_expiration_date: str = ""
    ws_this_progcommarea_acup_old_details_acup_old_acct_data: str = ""
    ws_misc_storage_ws_non_key_flags_ws_edit_acct_status: str = ""
    ws_misc_storage_ws_generic_edits_ws_edit_variable_name: str = ""
    ws_misc_storage_ws_non_key_flags_ws_edit_open_date_flgs: str = ""
    ws_misc_storage_ws_generic_edits_ws_edit_signed_number_9v2_x: str = ""
    ws_misc_storage_ws_non_key_flags_ws_edit_credit_limit: str = ""

    ws_edit_date_ccyymmdd: str = ""
    ws_edit_date_flgs: str = ""
    ws_expiry_date_flgs: str = ""
    ws_edit_cash_credit_limit: str = ""
    ws_this_progcommarea_acup_new_details_acup_new_acct_data_acup_new_reissue_date: str = ""

    ws_edit_curr_bal: str = ""
    ws_edit_curr_cyc_credit: str = ""
    ws_edit_curr_cyc_debit: str = ""
    ws_edit_dt_of_birth_flgs: str = ""
    ws_edit_alphanum_only: str = ""
    ws_edit_alphanum_length: str = ""
    acup_changes_ok_not_confirmed: bool = False
    flg_fico_score_is_valid: bool = False
    input_error: bool = False

    # 0000-MAIN new fields (duplicates removed)
    eibcalen: int = 0
    ws_return_msg_off: bool = False
    cdemo_pgm_enter: bool = False
    pfk_invalid: bool = False
    pfk_valid: bool = False
    ccard_aid_enter: bool = False
    ccard_aid_pfk03: bool = False
    cdemo_from_tranid: str = ""
    cdemo_to_tranid: str = ""
    ws_literals_lit_menutranid: str = ""
    cdemo_from_program: str = ""
    cdemo_to_program: str = ""
    cdemo_last_map: str = ""
    cdemo_last_mapset: str = ""
    cdemo_pgm_reenter: bool = False
    cdemo_usrtyp_user: str = ""
    common_return: Any = None

    # 1200-EDIT-MAP-INPUTS additional control flags (bool)
    input_ok: bool = False
    acup_details_not_fetched: bool = False
    flg_acctfilter_blank: bool = False
    no_search_criteria_received: bool = False
    found_account_data: bool = False
    found_acct_in_master: bool = False
    flg_acctfilter_isvalid: bool = False
    found_cust_in_master: bool = False
    flg_custfilter_isvalid: bool = False
    no_changes_found: bool = False
    acup_changes_not_ok: bool = False

# 1100-RECEIVE-MAP BMS input fields (CACTUPAI copybook)
    cactupai_acslnami: str = ""
    cactupai_acsadl1i: str = ""
    cactupai_acsadl2i: str = ""
    cactupai_acscityi: str = ""
    cactupai_acssttei: str = ""
    cactupai_acszipci: str = ""
    cactupai_acsctryi: str = ""
    cactupai_acsph1ai: str = ""
    cactupai_acsph1bi: str = ""
    cactupai_acsph1ci: str = ""
    cactupai_acsph2ai: str = ""
    cactupai_acsph2bi: str = ""
    cactupai_acsph2ci: str = ""
    cactupai_acseftci: str = ""
    cactupai_acsgovti: str = ""
    cactupai_acspflgi: str = ""

# 1205-COMPARE-OLD-NEW fields (short canonical names)
    # Account data
    acup_new_acct_id_x: str = ""
    acup_old_acct_id_x: str = ""
    acup_new_active_status: str = ""
    acup_old_active_status: str = ""
    acup_new_curr_bal: float = 0.0
    acup_old_curr_bal: float = 0.0
    acup_new_credit_limit: float = 0.0
    acup_old_credit_limit: float = 0.0
    acup_new_cash_credit_limit: float = 0.0
    acup_old_cash_credit_limit: float = 0.0
    acup_new_open_date: str = ""
    acup_old_open_date: str = ""
    acup_new_expiraion_date: str = ""
    acup_old_expiraion_date: str = ""
    acup_new_reissue_date: str = ""
    acup_old_reissue_date: str = ""
    acup_new_curr_cyc_credit: float = 0.0
    acup_old_curr_cyc_credit: float = 0.0
    acup_new_curr_cyc_debit: float = 0.0
    acup_old_curr_cyc_debit: float = 0.0
    acup_new_group_id: str = ""
    acup_old_group_id: str = ""

    # Customer data
    acup_new_cust_id_x: str = ""
    acup_old_cust_id_x: str = ""
    acup_new_cust_first_name: str = ""
    acup_old_cust_first_name: str = ""
    acup_new_cust_middle_name: str = ""
    acup_old_cust_middle_name: str = ""
    acup_new_cust_last_name: str = ""
    acup_old_cust_last_name: str = ""
    acup_new_cust_addr_line_1: str = ""
    acup_old_cust_addr_line_1: str = ""
    acup_new_cust_addr_line_2: str = ""
    acup_old_cust_addr_line_2: str = ""
    acup_new_cust_addr_line_3: str = ""
    acup_old_cust_addr_line_3: str = ""
    acup_new_cust_addr_state_cd: str = ""
    acup_old_cust_addr_state_cd: str = ""
    acup_new_cust_addr_country_cd: str = ""
    acup_old_cust_addr_country_cd: str = ""
    acup_new_cust_addr_zip: str = ""
    acup_old_cust_addr_zip: str = ""
    acup_new_cust_phone_num_1a: str = ""
    acup_old_cust_phone_num_1a: str = ""
    acup_new_cust_phone_num_1b: str = ""
    acup_old_cust_phone_num_1b: str = ""
    acup_new_cust_phone_num_1c: str = ""
    acup_old_cust_phone_num_1c: str = ""
    acup_new_cust_phone_num_2a: str = ""
    acup_old_cust_phone_num_2a: str = ""
    acup_new_cust_phone_num_2b: str = ""
    acup_old_cust_phone_num_2b: str = ""
    acup_new_cust_phone_num_2c: str = ""
    acup_old_cust_phone_num_2c: str = ""
    acup_new_cust_ssn_x: str = ""
    acup_old_cust_ssn_x: str = ""
    acup_new_cust_govt_issued_id: str = ""
    acup_old_cust_govt_issued_id: str = ""
    acup_new_cust_dob_yyyy_mm_dd: str = ""
    acup_old_cust_dob_yyyy_mm_dd: str = ""
    acup_new_cust_eft_account_id: str = ""
    acup_old_cust_eft_account_id: str = ""
    acup_new_cust_pri_holder_ind: str = ""
    acup_old_cust_pri_holder_ind: str = ""
    acup_new_cust_fico_score_x: str = ""
    acup_old_cust_fico_score_x: str = ""

    # Control flags
    change_has_occurred: bool = False
    no_changes_detected: bool = False

# 1210-EDIT-ACCOUNT fields
    flg_acctfilter_not_ok: bool = False
    cc_acct_id: str = ""
    ws_prompt_for_acct: bool = False
    cdemo_acct_id: int = 0
    acup_new_acct_id: str = ""
    cc_acct_id_n: int = 0
    ws_return_msg: str = ""
# 1215-EDIT-MANDATORY fields
    flg_mandatory_not_ok: bool = False
    ws_edit_alphanum_only: str = ""
    flg_mandatory_blank: bool = False
    flg_mandatory_isvalid: bool = False



# --- 1260 Phone Edit Working Storage ---
ws_edit_us_phone_numa: str = ""      # area code (3 digits)
ws_edit_us_phone_numb: str = ""      # prefix (3 digits)
ws_edit_us_phone_numc: str = ""      # line number (4 digits)
ws_edit_us_phone_is_valid: bool = False
ws_edit_us_phone_is_invalid: bool = False
flg_edit_us_phonea_blank: bool = False
flg_edit_us_phonea_not_ok: bool = False
flg_edit_us_phonea_isvalid: bool = False
flg_edit_us_phoneb_blank: bool = False
flg_edit_us_phoneb_not_ok: bool = False
flg_edit_us_phoneb_isvalid: bool = False
flg_edit_us_phonec_blank: bool = False
flg_edit_us_phonec_not_ok: bool = False
flg_edit_us_phonec_isvalid: bool = False


# --- 1265 SSN Edit Working Storage ---
ws_edit_us_ssn_part1: str = ""
ws_edit_us_ssn_part2: str = ""
ws_edit_us_ssn_part3: str = ""
ws_edit_us_ssn_part1_flgs: str = ""
ws_edit_us_ssn_part2_flgs: str = ""
ws_edit_us_ssn_part3_flgs: str = ""
flg_edit_us_ssn_part1_not_ok: bool = False
flg_edit_us_ssn_part2_not_ok: bool = False
flg_edit_us_ssn_part3_not_ok: bool = False


# --- 1270 State Code Edit Working Storage ---
us_state_code_to_edit: str = ""
flg_state_not_ok: bool = False


# --- 1275 FICO Score Edit Working Storage ---
flg_fico_score_not_ok: bool = False


# --- 1280 State + ZIP Combo Edit Working Storage ---
us_state_and_first_zip2: str = ""
flg_zipcode_not_ok: bool = False


# --- 2000 DECIDE-ACTION Working Storage ---
acup_show_details: bool = False
acup_changes_okayed_and_done: bool = False
acup_changes_okayed_lock_error: bool = False
acup_changes_okayed_but_failed: bool = False
ccard_aid_pfk12: bool = False
ccard_aid_pfk05: bool = False
could_not_lock_acct_for_update: bool = False
locked_but_update_failed: bool = False
data_was_changed_before_update: bool = False
cdemo_card_num: int = 0
cdemo_acct_status: str = ""
abend_culprit: str = ""
abend_code: str = ""
abend_reason: str = ""
abend_msg: str = ""


# --- 3200/3203 Validation Flags ---
flg_cred_limit_isvalid: bool = False
flg_cash_credit_limit_isvalid: bool = False
flg_curr_bal_isvalid: bool = False
flg_curr_cyc_credit_isvalid: bool = False
flg_curr_cyc_debit_isvalid: bool = False
acup_changes_made: bool = False

ws_info_msg: str = ""

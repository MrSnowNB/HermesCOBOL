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

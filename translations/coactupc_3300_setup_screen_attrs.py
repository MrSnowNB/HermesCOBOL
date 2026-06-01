"""
coactupc_3300_setup_screen_attrs.py
Implements 3300-SETUP-SCREEN-ATTRS paragraph.
"""

from constants import DFHBMPRF, DFHBMFSE


def _protect_all(state):
    """3310-PROTECT-ALL-ATTRS"""
    protected_fields = [
        "ACCTSIDA", "ACSTTUSA",
        "ACRDLIMA", "ACSHLIMA", "ACURBALA", "ACRCYCRA", "ACRCYDBA",
        "OPNYEARA", "OPNMONA", "OPNDAYA", "EXPYEARA", "EXPMONA", "EXPDAYA",
        "RISYEARA", "RISMONA", "RISDAYA", "AADDGRPA",
        "ACSTNUMA", "ACTSSN1A", "ACTSSN2A", "ACTSSN3A", "ACSTFCOA",
        "DOBYEARA", "DOBMONA", "DOBDAYA",
        "ACSFNAMA", "ACSMNAMA", "ACSLNAMA",
        "ACSADL1A", "ACSADL2A", "ACSCITYA", "ACSSTTEA", "ACSZIPCA", "ACSCTRYA",
        "ACSPH1AA", "ACSPH1BA", "ACSPH1CA", "ACSPH2AA", "ACSPH2BA", "ACSPH2CA",
        "ACSGOVTA", "ACSEFTCA", "ACSPFLGA", "INFOMSGA",
    ]
    for field in protected_fields:
        state.cactupao[field] = DFHBMPRF


def _unprotect_few(state):
    """3320-UNPROTECT-FEW-ATTRS"""
    unprotected = [
        "ACSTTUSA", "ACRDLIMA", "ACSHLIMA", "ACURBALA", "ACRCYCRA", "ACRCYDBA",
        "OPNYEARA", "OPNMONA", "OPNDAYA",
        "EXPYEARA", "EXPMONA", "EXPDAYA",
        "RISYEARA", "RISMONA", "RISDAYA",
        "DOBYEARA", "DOBMONA", "DOBDAYA", "AADDGRPA",
        "ACTSSN1A", "ACTSSN2A", "ACTSSN3A", "ACSTFCOA",
        "ACSFNAMA", "ACSMNAMA", "ACSLNAMA",
        "ACSADL1A", "ACSADL2A", "ACSCITYA", "ACSSTTEA", "ACSZIPCA",
        "ACSPH1AA", "ACSPH1BA", "ACSPH1CA",
        "ACSPH2AA", "ACSPH2BA", "ACSPH2CA",
        "ACSGOVTA", "ACSEFTCA", "ACSPFLGA",
    ]
    for field in unprotected:
        state.cactupao[field] = DFHBMFSE

    # Explicitly protected in 3320
    state.cactupao["ACSTNUMA"] = DFHBMPRF
    state.cactupao["ACSCTRYA"] = DFHBMPRF
    state.cactupao["INFOMSGA"] = DFHBMPRF


def setup_screen_attrs(state):
    """3300-SETUP-SCREEN-ATTRS"""
    _protect_all(state)

    # Edit mode
    if state.acup_show_details or state.acup_changes_not_ok:
        _unprotect_few(state)

    # Cursor positioning logic (only error/blank conditions)
    if state.flg_acctfilter_blank or state.flg_acctfilter_not_ok:
        state.cactupao["ACCTSIDL"] = -1
    if state.flg_acct_status_blank or state.flg_acct_status_not_ok:
        state.cactupao["ACSTTUSL"] = -1
    if state.flg_open_year_blank or state.flg_open_year_not_ok:
        state.cactupao["OPNYEARL"] = -1
    if state.flg_open_month_blank or state.flg_open_month_not_ok:
        state.cactupao["OPNMONL"] = -1
    if state.flg_open_day_blank or state.flg_open_day_not_ok:
        state.cactupao["OPNDAYL"] = -1
    if state.flg_cred_limit_blank or state.flg_cred_limit_not_ok:
        state.cactupao["ACRDLIML"] = -1
    if state.flg_expiry_year_blank or state.flg_expiry_year_not_ok:
        state.cactupao["EXPYEARL"] = -1
    if state.flg_expiry_month_blank or state.flg_expiry_month_not_ok:
        state.cactupao["EXPMONL"] = -1
    if state.flg_expiry_day_blank or state.flg_expiry_day_not_ok:
        state.cactupao["EXPDAYL"] = -1
    if state.flg_cash_credit_limit_blank or state.flg_cash_credit_limit_not_ok:
        state.cactupao["ACSHLIML"] = -1
    if state.flg_reissue_year_blank or state.flg_reissue_year_not_ok:
        state.cactupao["RISYEARL"] = -1
    if state.flg_reissue_month_blank or state.flg_reissue_month_not_ok:
        state.cactupao["RISMONL"] = -1
    if state.flg_reissue_day_blank or state.flg_reissue_day_not_ok:
        state.cactupao["RISDAYL"] = -1
    if state.flg_curr_bal_blank or state.flg_curr_bal_not_ok:
        state.cactupao["ACURBALL"] = -1
    if state.flg_curr_cyc_credit_blank or state.flg_curr_cyc_credit_not_ok:
        state.cactupao["ACRCYCRL"] = -1
    if state.flg_curr_cyc_debit_blank or state.flg_curr_cyc_debit_not_ok:
        state.cactupao["ACRCYDBL"] = -1
    if state.flg_edit_us_ssn_part1_blank or state.flg_edit_us_ssn_part1_not_ok:
        state.cactupao["ACTSSN1L"] = -1
    if state.flg_edit_us_ssn_part2_blank or state.flg_edit_us_ssn_part2_not_ok:
        state.cactupao["ACTSSN2L"] = -1
    if state.flg_edit_us_ssn_part3_blank or state.flg_edit_us_ssn_part3_not_ok:
        state.cactupao["ACTSSN3L"] = -1
    if state.flg_dt_of_birth_year_blank or state.flg_dt_of_birth_year_not_ok:
        state.cactupao["DOBYEARL"] = -1
    if state.flg_dt_of_birth_month_blank or state.flg_dt_of_birth_month_not_ok:
        state.cactupao["DOBMONL"] = -1
    if state.flg_dt_of_birth_day_blank or state.flg_dt_of_birth_day_not_ok:
        state.cactupao["DOBDAYL"] = -1
    if state.flg_fico_score_blank or state.flg_fico_score_not_ok:
        state.cactupao["ACSTFCOL"] = -1
    if state.flg_first_name_blank or state.flg_first_name_not_ok:
        state.cactupao["ACSFNAML"] = -1
    if state.flg_middle_name_blank or state.flg_middle_name_not_ok:
        state.cactupao["ACSMNAML"] = -1
    if state.flg_last_name_blank or state.flg_last_name_not_ok:
        state.cactupao["ACSLNAML"] = -1
    if state.flg_address_line_1_blank or state.flg_address_line_1_not_ok:
        state.cactupao["ACSADL1L"] = -1
    if state.flg_city_blank or state.flg_city_not_ok:
        state.cactupao["ACSCITYL"] = -1
    if state.flg_state_blank or state.flg_state_not_ok:
        state.cactupao["ACSSTTEL"] = -1
    if state.flg_zipcode_blank or state.flg_zipcode_not_ok:
        state.cactupao["ACSZIPCL"] = -1
    if state.flg_country_blank or state.flg_country_not_ok:
        state.cactupao["ACSCTRYL"] = -1
    if state.flg_phone_num_1a_blank or state.flg_phone_num_1a_not_ok:
        state.cactupao["ACSPH1AL"] = -1
    if state.flg_phone_num_1b_blank or state.flg_phone_num_1b_not_ok:
        state.cactupao["ACSPH1BL"] = -1
    if state.flg_phone_num_1c_blank or state.flg_phone_num_1c_not_ok:
        state.cactupao["ACSPH1CL"] = -1
    if state.flg_phone_num_2a_blank or state.flg_phone_num_2a_not_ok:
        state.cactupao["ACSPH2AL"] = -1
    if state.flg_phone_num_2b_blank or state.flg_phone_num_2b_not_ok:
        state.cactupao["ACSPH2BL"] = -1
    if state.flg_phone_num_2c_blank or state.flg_phone_num_2c_not_ok:
        state.cactupao["ACSPH2CL"] = -1
    if state.flg_eft_account_id_blank or state.flg_eft_account_id_not_ok:
        state.cactupao["ACSEFTCL"] = -1
    if state.flg_pri_cardholder_blank or state.flg_pri_cardholder_not_ok:
        state.cactupao["ACSPFLGL"] = -1

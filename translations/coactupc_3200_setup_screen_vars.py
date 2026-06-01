"""
coactupc_3200_setup_screen_vars.py
Implements 3200-SETUP-SCREEN-VARS and helpers (3201/3202/3203).
"""

from state import state


def _format_currency(value) -> str:
    """Format numeric value as currency string with 2 decimals."""
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return ""


def _show_initial_values():
    """3201-SHOW-INITIAL-VALUES"""
    # Clear account/customer fields
    for field in [
        "ACSTTUSO", "ACRDLIMO", "ACURBALO", "ACSHLIMO",
        "ACRCYCRO", "ACRCYDBO",
        "OPNYEARO", "OPNMONO", "OPNDAYO",
        "EXPYEARO", "EXPMONO", "EXPDAYO",
        "RISYEARO", "RISMONO", "RISDAYO", "AADDGRPO",
        "ACSTNUMO", "ACTSSN1O", "ACTSSN2O", "ACTSSN3O",
        "ACSTFCOO",
        "DOBYEARO", "DOBMONO", "DOBDAYO",
        "ACSFNAMO", "ACSMNAMO",
    ]:
        state.cactupao[field] = ""


def _show_original_values():
    """3202-SHOW-ORIGINAL-VALUES"""
    if state.found_acct_in_master or state.found_cust_in_master:
        state.cactupao["ACSTTUSO"] = state.acup_old_active_status or ""

        state.cactupao["ACURBALO"] = _format_currency(state.acup_old_curr_bal_n)
        state.cactupao["ACRDLIMO"] = _format_currency(state.acup_old_credit_limit_n)
        state.cactupao["ACSHLIMO"] = _format_currency(state.acup_old_cash_credit_limit_n)
        state.cactupao["ACRCYCRO"] = _format_currency(state.acup_old_curr_cyc_credit_n)
        state.cactupao["ACRCYDBO"] = _format_currency(state.acup_old_curr_cyc_debit_n)

        state.cactupao["OPNYEARO"] = state.acup_old_open_year or ""
        state.cactupao["OPNMONO"] = state.acup_old_open_mon or ""
        state.cactupao["OPNDAYO"] = state.acup_old_open_day or ""

        state.cactupao["EXPYEARO"] = state.acup_old_exp_year or ""
        state.cactupao["EXPMONO"] = state.acup_old_exp_mon or ""
        state.cactupao["EXPDAYO"] = state.acup_old_exp_day or ""

        state.cactupao["RISYEARO"] = state.acup_old_reissue_year or ""
        state.cactupao["RISMONO"] = state.acup_old_reissue_mon or ""
        state.cactupao["RISDAYO"] = state.acup_old_reissue_day or ""

        state.cactupao["AADDGRPO"] = state.acup_old_group_id or ""

    if state.found_cust_in_master:
        state.cactupao["ACSTNUMO"] = state.acup_old_cust_id_x or ""

        ssn = state.acup_old_cust_ssn_x or ""
        state.cactupao["ACTSSN1O"] = ssn[0:3] if len(ssn) >= 3 else ""
        state.cactupao["ACTSSN2O"] = ssn[3:5] if len(ssn) >= 5 else ""
        state.cactupao["ACTSSN3O"] = ssn[5:9] if len(ssn) >= 9 else ""

        state.cactupao["ACSTFCOO"] = state.acup_old_cust_fico_score_x or ""

        dob = state.acup_old_cust_dob_yyyy_mm_dd or ""
        if len(dob) >= 10:
            state.cactupao["DOBYEARO"] = dob[0:4]
            state.cactupao["DOBMONO"] = dob[5:7]
            state.cactupao["DOBDAYO"] = dob[8:10]

        state.cactupao["ACSFNAMO"] = state.acup_old_cust_first_name or ""
        state.cactupao["ACSMNAMO"] = state.acup_old_cust_middle_name or ""


def _show_updated_values():
    """3203-SHOW-UPDATED-VALUES"""
    state.cactupao["ACSTTUSO"] = state.acup_new_active_status or ""

    # Credit limit
    if getattr(state, "flg_cred_limit_isvalid", False):
        state.cactupao["ACRDLIMO"] = _format_currency(state.acup_new_credit_limit_n)
    else:
        state.cactupao["ACRDLIMO"] = state.acup_new_credit_limit_x or ""

    # Cash credit limit
    if getattr(state, "flg_cash_credit_limit_isvalid", False):
        state.cactupao["ACSHLIMO"] = _format_currency(state.acup_new_cash_credit_limit_n)
    else:
        state.cactupao["ACSHLIMO"] = state.acup_new_cash_credit_limit_x or ""

    # Current balance
    if getattr(state, "flg_curr_bal_isvalid", False):
        state.cactupao["ACURBALO"] = _format_currency(state.acup_new_curr_bal_n)
    else:
        state.cactupao["ACURBALO"] = state.acup_new_curr_bal_x or ""

    # Current cycle credit
    if getattr(state, "flg_curr_cyc_credit_isvalid", False):
        state.cactupao["ACRCYCRO"] = _format_currency(state.acup_new_curr_cyc_credit_n)
    else:
        state.cactupao["ACRCYCRO"] = state.acup_new_curr_cyc_credit_x or ""

    # Current cycle debit
    if getattr(state, "flg_curr_cyc_debit_isvalid", False):
        state.cactupao["ACRCYDBO"] = _format_currency(state.acup_new_curr_cyc_debit_n)
    else:
        state.cactupao["ACRCYDBO"] = state.acup_new_curr_cyc_debit_x or ""

    state.cactupao["OPNYEARO"] = state.acup_new_open_year or ""
    state.cactupao["OPNMONO"] = state.acup_new_open_mon or ""
    state.cactupao["OPNDAYO"] = state.acup_new_open_day or ""

    state.cactupao["EXPYEARO"] = state.acup_new_exp_year or ""
    state.cactupao["EXPMONO"] = state.acup_new_exp_mon or ""
    state.cactupao["EXPDAYO"] = state.acup_new_exp_day or ""


def setup_screen_vars():
    """3200-SETUP-SCREEN-VARS (public dispatcher)"""
    if state.cdemo_pgm_enter:
        return

    # Account ID
    if state.cc_acct_id_n == 0 and state.flg_acctfilter_isvalid:
        state.cactupao["ACCTSIDO"] = ""
    else:
        state.cactupao["ACCTSIDO"] = state.cc_acct_id or ""

    # Dispatch based on state
    if state.acup_details_not_fetched or state.cc_acct_id_n == 0:
        _show_initial_values()
    elif state.acup_show_details:
        _show_original_values()
    elif state.acup_changes_made:
        _show_updated_values()
    else:
        _show_original_values()

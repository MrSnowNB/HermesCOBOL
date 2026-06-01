from translations.state import CarddemoState


def coactupc_1205_compare_old_new(state: CarddemoState) -> None:
    # seq=1: SET NO-CHANGES-FOUND TO TRUE
    state.no_changes_found = True

    # seq=2: IF ACUP-NEW-ACCT-ID-X = ACUP-OLD-ACCT-ID-X
    #        AND FUNCTION UPPER-CASE(ACUP-NEW-ACTIVE-STATUS) = ...
    #        AND ... (all account field conditions)
    if not (
        state.acup_new_acct_id_x == state.acup_old_acct_id_x
        and state.acup_new_active_status.upper() == state.acup_old_active_status.upper()
        and state.acup_new_curr_bal == state.acup_old_curr_bal
        and state.acup_new_credit_limit == state.acup_old_credit_limit
        and state.acup_new_cash_credit_limit == state.acup_old_cash_credit_limit
        and state.acup_new_open_date == state.acup_old_open_date
        and state.acup_new_expiraion_date == state.acup_old_expiraion_date
        and state.acup_new_reissue_date == state.acup_old_reissue_date
        and state.acup_new_curr_cyc_credit == state.acup_old_curr_cyc_credit
        and state.acup_new_curr_cyc_debit == state.acup_old_curr_cyc_debit
        and state.acup_new_group_id.strip().upper() == state.acup_old_group_id.strip().upper()
    ):
        # seq=3: SET CHANGE-HAS-OCCURRED TO TRUE
        state.change_has_occurred = True
        # seq=4: GO TO 1205-COMPARE-OLD-NEW-EXIT
        return  # GO TO 1205-COMPARE-OLD-NEW-EXIT
    # seq=5: END-IF

    # seq=6: IF FUNCTION UPPER-CASE(FUNCTION TRIM(ACUP-NEW-CUST-ID-X))
    #           = FUNCTION UPPER-CASE(FUNCTION TRIM(ACUP-OLD-CUST-ID-X))
    #        AND ... (all customer field conditions)
    if not (
        state.acup_new_cust_id_x.strip().upper() == state.acup_old_cust_id_x.strip().upper()
        and state.acup_new_cust_first_name.strip().upper() == state.acup_old_cust_first_name.strip().upper()
        and state.acup_new_cust_middle_name.strip().upper() == state.acup_old_cust_middle_name.strip().upper()
        and state.acup_new_cust_last_name.strip().upper() == state.acup_old_cust_last_name.strip().upper()
        and state.acup_new_cust_addr_line_1.strip().upper() == state.acup_old_cust_addr_line_1.strip().upper()
        and state.acup_new_cust_addr_line_2.strip().upper() == state.acup_old_cust_addr_line_2.strip().upper()
        and state.acup_new_cust_addr_line_3.strip().upper() == state.acup_old_cust_addr_line_3.strip().upper()
        and state.acup_new_cust_addr_state_cd.strip().upper() == state.acup_old_cust_addr_state_cd.strip().upper()
        and state.acup_new_cust_addr_country_cd.strip().upper() == state.acup_old_cust_addr_country_cd.strip().upper()
        and state.acup_new_cust_addr_zip.strip().upper() == state.acup_old_cust_addr_zip.strip().upper()
        and state.acup_new_cust_phone_num_1a == state.acup_old_cust_phone_num_1a
        and state.acup_new_cust_phone_num_1b == state.acup_old_cust_phone_num_1b
        and state.acup_new_cust_phone_num_1c == state.acup_old_cust_phone_num_1c
        and state.acup_new_cust_phone_num_2a == state.acup_old_cust_phone_num_2a
        and state.acup_new_cust_phone_num_2b == state.acup_old_cust_phone_num_2b
        and state.acup_new_cust_phone_num_2c == state.acup_old_cust_phone_num_2c
        and state.acup_new_cust_ssn_x == state.acup_old_cust_ssn_x
        and state.acup_new_cust_govt_issued_id.strip().upper() == state.acup_old_cust_govt_issued_id.strip().upper()
        and state.acup_new_cust_dob_yyyy_mm_dd == state.acup_old_cust_dob_yyyy_mm_dd
        and state.acup_new_cust_eft_account_id == state.acup_old_cust_eft_account_id
        and state.acup_new_cust_pri_holder_ind.strip().upper() == state.acup_old_cust_pri_holder_ind.strip().upper()
        and state.acup_new_cust_fico_score_x == state.acup_old_cust_fico_score_x
    ):
        # seq=7: SET CHANGE-HAS-OCCURRED TO TRUE
        state.change_has_occurred = True
        # seq=8: GO TO 1205-COMPARE-OLD-NEW-EXIT
        return  # GO TO 1205-COMPARE-OLD-NEW-EXIT
    # seq=9: END-IF

    # seq=10: SET NO-CHANGES-DETECTED TO TRUE (fall-through)
    state.no_changes_detected = True

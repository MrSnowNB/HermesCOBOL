from translations.state import CarddemoState

# Stub functions for all PERFORM targets (per rule 10)
def coactupc_1210_edit_account(state: CarddemoState) -> None: pass
def coactupc_1205_compare_old_new(state: CarddemoState) -> None: pass
def coactupc_1220_edit_yesno(state: CarddemoState) -> None: pass
def coactupc_1250_edit_signed_9v2(state: CarddemoState) -> None: pass
def coactupc_1265_edit_us_ssn(state: CarddemoState) -> None: pass
def coactupc_1245_edit_num_reqd(state: CarddemoState) -> None: pass
def coactupc_1275_edit_fico_score(state: CarddemoState) -> None: pass
def coactupc_1225_edit_alpha_reqd(state: CarddemoState) -> None: pass
def coactupc_1235_edit_alpha_opt(state: CarddemoState) -> None: pass
def coactupc_1215_edit_mandatory(state: CarddemoState) -> None: pass
def coactupc_1270_edit_us_state_cd(state: CarddemoState) -> None: pass
def coactupc_1260_edit_us_phone_num(state: CarddemoState) -> None: pass
def coactupc_1280_edit_us_state_zip_cd(state: CarddemoState) -> None: pass
def coactupc_edit_date_ccyymmdd(state: CarddemoState) -> None: pass
def coactupc_edit_date_of_birth(state: CarddemoState) -> None: pass


def coactupc_1200_edit_map_inputs(state: CarddemoState) -> None:
    # seq=1: SET INPUT-OK TO TRUE
    state.input_ok = True

    # seq=2: IF ACUP-DETAILS-NOT-FETCHED
    if state.acup_details_not_fetched:
        # seq=3: PERFORM 1210-EDIT-ACCOUNT THRU 1210-EDIT-ACCOUNT-EXIT
        coactupc_1210_edit_account(state)

        # seq=4: MOVE LOW-VALUES TO ACUP-OLD-ACCT-DATA
        # TODO: reset ws_this_progcommarea_acup_old_details_acup_old_acct_data children when modeled
        pass

        # seq=5: IF FLG-ACCTFILTER-BLANK
        if state.flg_acctfilter_blank:
            # seq=6: SET NO-SEARCH-CRITERIA-RECEIVED TO TRUE
            state.no_search_criteria_received = True
        # seq=7: END-IF

        # seq=8: GO TO 1200-EDIT-MAP-INPUTS-EXIT
        return  # GO TO 1200-EDIT-MAP-INPUTS-EXIT
    else:
        # seq=9: CONTINUE
        pass
    # seq=10: END-IF

    # seq=11: SET FOUND-ACCOUNT-DATA TO TRUE
    state.found_account_data = True

    # seq=12: SET FOUND-ACCT-IN-MASTER TO TRUE
    state.found_acct_in_master = True

    # seq=13: SET FLG-ACCTFILTER-ISVALID TO TRUE
    state.flg_acctfilter_isvalid = True

    # seq=14: SET FOUND-CUST-IN-MASTER TO TRUE
    state.found_cust_in_master = True

    # seq=15: SET FLG-CUSTFILTER-ISVALID TO TRUE
    state.flg_custfilter_isvalid = True

    # seq=16: PERFORM 1205-COMPARE-OLD-NEW THRU 1205-COMPARE-OLD-NEW-EXIT
    coactupc_1205_compare_old_new(state)

    # seq=17: IF NO-CHANGES-FOUND
    if getattr(state, 'no_changes_found', False):
        # seq=18: MOVE LOW-VALUES TO WS-NON-KEY-FLAGS
        # TODO: reset ws_misc_storage_ws_non_key_flags children when modeled
        pass
        # seq=19: GO TO 1200-EDIT-MAP-INPUTS-EXIT
        return  # GO TO 1200-EDIT-MAP-INPUTS-EXIT
    # seq=20: END-IF

    # seq=21: SET ACUP-CHANGES-NOT-OK TO TRUE
    state.acup_changes_not_ok = True

    # seq=22: MOVE 'Account Status' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "Account Status"

    # seq=23: MOVE ACUP-NEW-ACTIVE-STATUS TO WS-EDIT-YES-NO
    state.ws_misc_storage_ws_generic_edits_ws_edit_yes_no = state.ws_this_progcommarea_acup_new_details_acup_new_acct_data_acup_new_active_status

    # seq=24: PERFORM 1220-EDIT-YESNO THRU 1220-EDIT-YESNO-EXIT
    coactupc_1220_edit_yesno(state)

    # seq=25: MOVE WS-EDIT-YES-NO TO WS-EDIT-ACCT-STATUS
    state.ws_misc_storage_ws_non_key_flags_ws_edit_acct_status = state.ws_misc_storage_ws_generic_edits_ws_edit_yes_no

    # seq=26: MOVE 'Open Date' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "Open Date"

    # seq=27: MOVE ACUP-NEW-OPEN-DATE TO WS-EDIT-DATE-CCYYMMDD
    state.ws_edit_date_ccyymmdd = state.ws_this_progcommarea_acup_new_details_acup_new_acct_data_acup_new_open_date

    # seq=28: PERFORM EDIT-DATE-CCYYMMDD THRU EDIT-DATE-CCYYMMDD-EXIT
    coactupc_edit_date_ccyymmdd(state)

    # seq=29: MOVE WS-EDIT-DATE-FLGS TO WS-EDIT-OPEN-DATE-FLGS
    state.ws_misc_storage_ws_non_key_flags_ws_edit_open_date_flgs = state.ws_edit_date_flgs

    # seq=30: MOVE 'Credit Limit' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "Credit Limit"

    # seq=31: MOVE ACUP-NEW-CREDIT-LIMIT-X TO WS-EDIT-SIGNED-NUMBER-9V2-X
    state.ws_misc_storage_ws_generic_edits_ws_edit_signed_number_9v2_x = state.ws_misc_storage_alpha_vars_for_data_editing_acup_new_credit_limit_x

    # seq=32: PERFORM 1250-EDIT-SIGNED-9V2 THRU 1250-EDIT-SIGNED-9V2-EXIT
    coactupc_1250_edit_signed_9v2(state)

    # seq=33: MOVE WS-FLG-SIGNED-NUMBER-EDIT TO WS-EDIT-CREDIT-LIMIT
    state.ws_misc_storage_ws_non_key_flags_ws_edit_credit_limit = state.ws_misc_storage_ws_generic_edits_ws_flg_signed_number_edit

    # seq=34: MOVE 'Expiry Date' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "Expiry Date"

    # seq=35: MOVE ACUP-NEW-EXPIRATION-DATE TO WS-EDIT-DATE-CCYYMMDD
    state.ws_edit_date_ccyymmdd = state.ws_this_progcommarea_acup_new_details_acup_new_acct_data_acup_new_expiration_date

    # seq=36: PERFORM EDIT-DATE-CCYYMMDD THRU EDIT-DATE-CCYYMMDD-EXIT
    coactupc_edit_date_ccyymmdd(state)

    # seq=37: MOVE WS-EDIT-DATE-FLGS TO WS-EXPIRY-DATE-FLGS
    # TODO: ws_expiry_date_flgs not in state.py
    pass

    # seq=38: MOVE 'Cash Credit Limit' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "Cash Credit Limit"

    # seq=39: MOVE ACUP-NEW-CASH-CREDIT-LIMIT-X TO WS-EDIT-SIGNED-NUMBER-9V2-X
    # TODO: ACUP-NEW-CASH-CREDIT-LIMIT-X not mapped in state.py
    pass

    # seq=40: PERFORM 1250-EDIT-SIGNED-9V2 THRU 1250-EDIT-SIGNED-9V2-EXIT
    coactupc_1250_edit_signed_9v2(state)

    # seq=41: MOVE WS-FLG-SIGNED-NUMBER-EDIT TO WS-EDIT-CASH-CREDIT-LIMIT
    # TODO: ws_edit_cash_credit_limit not in state.py
    pass

    # seq=42: MOVE 'Reissue Date' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "Reissue Date"

    # seq=43: MOVE ACUP-NEW-REISSUE-DATE TO WS-EDIT-DATE-CCYYMMDD
    # TODO: ACUP-NEW-REISSUE-DATE not mapped
    pass

    # seq=44: PERFORM EDIT-DATE-CCYYMMDD THRU EDIT-DATE-CCYYMMDD-EXIT
    coactupc_edit_date_ccyymmdd(state)

    # seq=45: MOVE WS-EDIT-DATE-FLGS TO WS-EDIT-REISSUE-DATE-FLGS
    # TODO: ws_edit_reissue_date_flgs not in state.py
    pass

    # seq=46: MOVE 'Current Balance' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "Current Balance"

    # seq=47: MOVE ACUP-NEW-CURR-BAL-X TO WS-EDIT-SIGNED-NUMBER-9V2-X
    # TODO: field not in state.py
    pass

    # seq=48: PERFORM 1250-EDIT-SIGNED-9V2 THRU 1250-EDIT-SIGNED-9V2-EXIT
    coactupc_1250_edit_signed_9v2(state)

    # seq=49: MOVE WS-FLG-SIGNED-NUMBER-EDIT TO WS-EDIT-CURR-BAL
    # TODO: ws_edit_curr_bal not in state.py
    pass

    # seq=50: MOVE 'Current Cycle Credit Limit' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "Current Cycle Credit Limit"

    # seq=51: MOVE ACUP-NEW-CURR-CYC-CREDIT-X TO WS-EDIT-SIGNED-NUMBER-9V2-X
    # TODO: field not in state.py
    pass

    # seq=52: PERFORM 1250-EDIT-SIGNED-9V2 THRU 1250-EDIT-SIGNED-9V2-EXIT
    coactupc_1250_edit_signed_9v2(state)

    # seq=53: MOVE WS-FLG-SIGNED-NUMBER-EDIT TO WS-EDIT-CURR-CYC-CREDIT
    # TODO: ws_edit_curr_cyc_credit not in state.py
    pass

    # seq=54: MOVE 'Current Cycle Debit Limit' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "Current Cycle Debit Limit"

    # seq=55: MOVE ACUP-NEW-CURR-CYC-DEBIT-X TO WS-EDIT-SIGNED-NUMBER-9V2-X
    # TODO: field not in state.py
    pass

    # seq=56: PERFORM 1250-EDIT-SIGNED-9V2 THRU 1250-EDIT-SIGNED-9V2-EXIT
    coactupc_1250_edit_signed_9v2(state)

    # seq=57: MOVE WS-FLG-SIGNED-NUMBER-EDIT TO WS-EDIT-CURR-CYC-DEBIT
    # TODO: ws_edit_curr_cyc_debit not in state.py
    pass

    # seq=58: MOVE 'SSN' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "SSN"

    # seq=59: PERFORM 1265-EDIT-US-SSN THRU 1265-EDIT-US-SSN-EXIT
    coactupc_1265_edit_us_ssn(state)

    # seq=60: MOVE 'Date of Birth' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "Date of Birth"

    # seq=61: MOVE ACUP-NEW-CUST-DOB-YYYY-MM-DD TO WS-EDIT-DATE-CCYYMMDD
    # TODO: ACUP-NEW-CUST-DOB-YYYY-MM-DD not mapped
    pass

    # seq=62: PERFORM EDIT-DATE-CCYYMMDD THRU EDIT-DATE-CCYYMMDD-EXIT
    coactupc_edit_date_ccyymmdd(state)

    # seq=63: MOVE WS-EDIT-DATE-FLGS TO WS-EDIT-DT-OF-BIRTH-FLGS
    # TODO: ws_edit_dt_of_birth_flgs not in state.py
    pass

    # seq=64: IF WS-EDIT-DT-OF-BIRTH-ISVALID
    # TODO: flg_fico_score_is_valid used as proxy  ws_edit_dt_of_birth_isvalid not in state.py
    if state.flg_fico_score_is_valid:
        # seq=65: PERFORM EDIT-DATE-OF-BIRTH THRU EDIT-DATE-OF-BIRTH-EXIT
        coactupc_edit_date_of_birth(state)
        # seq=66: MOVE WS-EDIT-DATE-FLGS TO WS-EDIT-DT-OF-BIRTH-FLGS
        # TODO: ws_edit_dt_of_birth_flgs not in state.py
        pass
    # seq=67: END-IF

    # seq=68: MOVE 'FICO Score' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "FICO Score"

    # seq=69: MOVE ACUP-NEW-CUST-FICO-SCORE-X TO WS-EDIT-ALPHANUM-ONLY
    # TODO: ws_edit_alphanum_only not in state.py
    pass

    # seq=70: MOVE 3 TO WS-EDIT-ALPHANUM-LENGTH
    # TODO: ws_edit_alphanum_length not in state.py
    pass

    # seq=71: PERFORM 1245-EDIT-NUM-REQD THRU 1245-EDIT-NUM-REQD-EXIT
    coactupc_1245_edit_num_reqd(state)

    # seq=72: MOVE WS-EDIT-ALPHANUM-ONLY-FLAGS TO WS-EDIT-FICO-SCORE-FLGS
    # TODO: ws_edit_fico_score_flgs not in state.py
    pass

    # seq=73: IF FLG-FICO-SCORE-ISVALID
    # TODO: flg_fico_score_is_valid used as proxy
    if state.flg_fico_score_is_valid:
        coactupc_1275_edit_fico_score(state)
    # seq=75: END-IF

    # seq=76: MOVE 'First Name' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "First Name"

    # seq=77: MOVE ACUP-NEW-CUST-FIRST-NAME TO WS-EDIT-ALPHANUM-ONLY
    # TODO: ws_edit_alphanum_only not in state.py
    pass

    # seq=78: MOVE 25 TO WS-EDIT-ALPHANUM-LENGTH
    # TODO: ws_edit_alphanum_length not in state.py
    pass

    # seq=79: PERFORM 1225-EDIT-ALPHA-REQD THRU 1225-EDIT-ALPHA-REQD-EXIT
    coactupc_1225_edit_alpha_reqd(state)

    # seq=80: MOVE WS-EDIT-ALPHA-ONLY-FLAGS TO WS-EDIT-FIRST-NAME-FLGS
    # TODO: ws_edit_first_name_flgs not in state.py
    pass

    # seq=81: MOVE 'Middle Name' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "Middle Name"

    # seq=82: MOVE ACUP-NEW-CUST-MIDDLE-NAME TO WS-EDIT-ALPHANUM-ONLY
    # TODO: ws_edit_alphanum_only not in state.py
    pass

    # seq=83: MOVE 25 TO WS-EDIT-ALPHANUM-LENGTH
    # TODO: ws_edit_alphanum_length not in state.py
    pass

    # seq=84: PERFORM 1235-EDIT-ALPHA-OPT THRU 1235-EDIT-ALPHA-OPT-EXIT
    coactupc_1235_edit_alpha_opt(state)

    # seq=85: MOVE WS-EDIT-ALPHA-ONLY-FLAGS TO WS-EDIT-MIDDLE-NAME-FLGS
    # TODO: ws_edit_middle_name_flgs not in state.py
    pass

    # seq=86: MOVE 'Last Name' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "Last Name"

    # seq=87: MOVE ACUP-NEW-CUST-LAST-NAME TO WS-EDIT-ALPHANUM-ONLY
    # TODO: ws_edit_alphanum_only not in state.py
    pass

    # seq=88: MOVE 25 TO WS-EDIT-ALPHANUM-LENGTH
    # TODO: ws_edit_alphanum_length not in state.py
    pass

    # seq=89: PERFORM 1225-EDIT-ALPHA-REQD THRU 1225-EDIT-ALPHA-REQD-EXIT
    coactupc_1225_edit_alpha_reqd(state)

    # seq=90: MOVE WS-EDIT-ALPHA-ONLY-FLAGS TO WS-EDIT-LAST-NAME-FLGS
    # TODO: ws_edit_last_name_flgs not in state.py
    pass

    # seq=91: MOVE 'Address Line 1' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "Address Line 1"

    # seq=92: MOVE ACUP-NEW-CUST-ADDR-LINE-1 TO WS-EDIT-ALPHANUM-ONLY
    # TODO: ws_edit_alphanum_only not in state.py
    pass

    # seq=93: MOVE 50 TO WS-EDIT-ALPHANUM-LENGTH
    # TODO: ws_edit_alphanum_length not in state.py
    pass

    # seq=94: PERFORM 1215-EDIT-MANDATORY THRU 1215-EDIT-MANDATORY-EXIT
    coactupc_1215_edit_mandatory(state)

    # seq=95: MOVE WS-EDIT-MANDATORY-FLAGS TO WS-EDIT-ADDRESS-LINE-1-FLGS
    # TODO: ws_edit_address_line_1_flgs not in state.py
    pass

    # seq=96: MOVE 'State' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "State"

    # seq=97: MOVE ACUP-NEW-CUST-ADDR-STATE-CD TO WS-EDIT-ALPHANUM-ONLY
    # TODO: ws_edit_alphanum_only not in state.py
    pass

    # seq=98: MOVE 2 TO WS-EDIT-ALPHANUM-LENGTH
    # TODO: ws_edit_alphanum_length not in state.py
    pass

    # seq=99: PERFORM 1225-EDIT-ALPHA-REQD THRU 1225-EDIT-ALPHA-REQD-EXIT
    coactupc_1225_edit_alpha_reqd(state)

    # seq=100: MOVE WS-EDIT-ALPHA-ONLY-FLAGS TO WS-EDIT-STATE-FLGS
    # TODO: ws_edit_state_flgs not in state.py
    pass

    # seq=101: IF FLG-ALPHA-ISVALID
    # TODO: input_ok used as proxy  flg_alpha_isvalid not in state.py
    if state.input_ok:
        coactupc_1270_edit_us_state_cd(state)
    # seq=103: END-IF

    # seq=104: MOVE 'Zip' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "Zip"

    # seq=105: MOVE ACUP-NEW-CUST-ADDR-ZIP TO WS-EDIT-ALPHANUM-ONLY
    # TODO: ws_edit_alphanum_only not in state.py
    pass

    # seq=106: MOVE 5 TO WS-EDIT-ALPHANUM-LENGTH
    # TODO: ws_edit_alphanum_length not in state.py
    pass

    # seq=107: PERFORM 1245-EDIT-NUM-REQD THRU 1245-EDIT-NUM-REQD-EXIT
    coactupc_1245_edit_num_reqd(state)

    # seq=108: MOVE WS-EDIT-ALPHANUM-ONLY-FLAGS TO WS-EDIT-ZIPCODE-FLGS
    # TODO: ws_edit_zipcode_flgs not in state.py
    pass

    # seq=109: MOVE 'City' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "City"

    # seq=110: MOVE ACUP-NEW-CUST-ADDR-LINE-3 TO WS-EDIT-ALPHANUM-ONLY
    # TODO: ws_edit_alphanum_only not in state.py
    pass

    # seq=111: MOVE 50 TO WS-EDIT-ALPHANUM-LENGTH
    # TODO: ws_edit_alphanum_length not in state.py
    pass

    # seq=112: PERFORM 1225-EDIT-ALPHA-REQD THRU 1225-EDIT-ALPHA-REQD-EXIT
    coactupc_1225_edit_alpha_reqd(state)

    # seq=113: MOVE WS-EDIT-ALPHA-ONLY-FLAGS TO WS-EDIT-CITY-FLGS
    # TODO: ws_edit_city_flgs not in state.py
    pass

    # seq=114: MOVE 'Country' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "Country"

    # seq=115: MOVE ACUP-NEW-CUST-ADDR-COUNTRY-CD TO WS-EDIT-ALPHANUM-ONLY
    # TODO: ws_edit_alphanum_only not in state.py
    pass

    # seq=116: MOVE 3 TO WS-EDIT-ALPHANUM-LENGTH
    # TODO: ws_edit_alphanum_length not in state.py
    pass

    # seq=117: PERFORM 1225-EDIT-ALPHA-REQD THRU 1225-EDIT-ALPHA-REQD-EXIT
    coactupc_1225_edit_alpha_reqd(state)

    # seq=118: MOVE WS-EDIT-ALPHA-ONLY-FLAGS TO WS-EDIT-COUNTRY-FLGS
    # TODO: ws_edit_country_flgs not in state.py
    pass

    # seq=119: MOVE 'Phone Number 1' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "Phone Number 1"

    # seq=120: MOVE ACUP-NEW-CUST-PHONE-NUM-1 TO WS-EDIT-US-PHONE-NUM
    # TODO: ws_edit_us_phone_num not in state.py
    pass

    # seq=121: PERFORM 1260-EDIT-US-PHONE-NUM THRU 1260-EDIT-US-PHONE-NUM-EXIT
    coactupc_1260_edit_us_phone_num(state)

    # seq=122: MOVE WS-EDIT-US-PHONE-NUM-FLGS TO WS-EDIT-PHONE-NUM-1-FLGS
    # TODO: ws_edit_phone_num_1_flgs not in state.py
    pass

    # seq=123: MOVE 'Phone Number 2' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "Phone Number 2"

    # seq=124: MOVE ACUP-NEW-CUST-PHONE-NUM-2 TO WS-EDIT-US-PHONE-NUM
    # TODO: ws_edit_us_phone_num not in state.py
    pass

    # seq=125: PERFORM 1260-EDIT-US-PHONE-NUM THRU 1260-EDIT-US-PHONE-NUM-EXIT
    coactupc_1260_edit_us_phone_num(state)

    # seq=126: MOVE WS-EDIT-US-PHONE-NUM-FLGS TO WS-EDIT-PHONE-NUM-2-FLGS
    # TODO: ws_edit_phone_num_2_flgs not in state.py
    pass

    # seq=127: MOVE 'EFT Account Id' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "EFT Account Id"

    # seq=128: MOVE ACUP-NEW-CUST-EFT-ACCOUNT-ID TO WS-EDIT-ALPHANUM-ONLY
    # TODO: ws_edit_alphanum_only not in state.py
    pass

    # seq=129: MOVE 10 TO WS-EDIT-ALPHANUM-LENGTH
    # TODO: ws_edit_alphanum_length not in state.py
    pass

    # seq=130: PERFORM 1245-EDIT-NUM-REQD THRU 1245-EDIT-NUM-REQD-EXIT
    coactupc_1245_edit_num_reqd(state)

    # seq=131: MOVE WS-EDIT-ALPHANUM-ONLY-FLAGS TO WS-EFT-ACCOUNT-ID-FLGS
    # TODO: ws_eft_account_id_flgs not in state.py
    pass

    # seq=132: MOVE 'Primary Card Holder' TO WS-EDIT-VARIABLE-NAME
    state.ws_misc_storage_ws_generic_edits_ws_edit_variable_name = "Primary Card Holder"

    # seq=133: MOVE ACUP-NEW-CUST-PRI-HOLDER-IND TO WS-EDIT-YES-NO
    # TODO: ws_edit_yes_no not in state.py
    pass

    # seq=134: PERFORM 1220-EDIT-YESNO THRU 1220-EDIT-YESNO-EXIT
    coactupc_1220_edit_yesno(state)

    # seq=135: MOVE WS-EDIT-YES-NO TO WS-EDIT-PRI-CARDHOLDER
    # TODO: ws_edit_pri_cardholder not in state.py
    pass

    # seq=136: IF FLG-STATE-ISVALID AND FLG-ZIPCODE-ISVALID
    # TODO: flg_state_isvalid / flg_zipcode_isvalid not in state.py
    if state.input_ok:
        # seq=137: PERFORM 1280-EDIT-US-STATE-ZIP-CD THRU 1280-EDIT-US-STATE-ZIP-CD-EXIT
        coactupc_1280_edit_us_state_zip_cd(state)
    # seq=138: END-IF

    # seq=139: IF INPUT-ERROR
    # TODO: input_error not in state.py
    if state.input_ok:
        # seq=140: CONTINUE
        pass
    else:
        # seq=141: SET ACUP-CHANGES-OK-NOT-CONFIRMED TO TRUE
        # TODO: acup_changes_ok_not_confirmed not in state.py
        pass
    # seq=142: END-IF

    # seq=143: 1200-EDIT-MAP-INPUTS-EXIT (implicit return)
    return


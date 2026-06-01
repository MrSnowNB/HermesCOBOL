"""
coactupc_3250_setup_infomsg.py
Implements 3250-SETUP-INFOMSG paragraph.
"""

from state import state
from constants import (
    INFO_FOUND_ACCOUNT,
    INFO_PROMPT_SEARCH,
    INFO_PROMPT_CHANGES,
    INFO_PROMPT_CONFIRM,
    INFO_CONFIRM_SUCCESS,
    INFO_INFORM_FAILURE,
)


def setup_infomsg(state):
    """3250-SETUP-INFOMSG"""
    # Default / clear
    state.ws_info_msg = ""

    if state.cdemo_pgm_enter:
        state.ws_info_msg = INFO_PROMPT_SEARCH

    elif state.acup_details_not_fetched:
        state.ws_info_msg = INFO_PROMPT_SEARCH

    elif state.acup_show_details:
        state.ws_info_msg = INFO_PROMPT_CHANGES

    elif state.acup_changes_not_ok:
        state.ws_info_msg = INFO_PROMPT_CHANGES

    elif state.acup_changes_ok_not_confirmed:
        state.ws_info_msg = INFO_PROMPT_CONFIRM

    elif state.acup_changes_okayed_and_done:
        state.ws_info_msg = INFO_CONFIRM_SUCCESS

    elif state.acup_changes_okayed_lock_error:
        state.ws_info_msg = INFO_INFORM_FAILURE

    elif state.acup_changes_okayed_but_failed:
        state.ws_info_msg = INFO_INFORM_FAILURE

    elif not state.ws_info_msg or state.ws_info_msg.strip() == "":
        # WS-NO-INFO-MESSAGE condition
        state.ws_info_msg = INFO_PROMPT_SEARCH

    # Final assignments to output map
    state.cactupao["INFOMSGO"] = state.ws_info_msg
    state.cactupao["ERRMSGO"] = state.ws_return_msg

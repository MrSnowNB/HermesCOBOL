"""
coactupc_3390_setup_infomsg_attrs.py
Implements 3390-SETUP-INFOMSG-ATTRS paragraph.
"""

from state import state
from constants import DFHBMDAR, DFHBMASB, INFO_PROMPT_CONFIRM


def setup_infomsg_attrs(state):
    """3390-SETUP-INFOMSG-ATTRS"""
    if not state.ws_info_msg or not state.ws_info_msg.strip():
        state.cactupai["INFOMSGA"] = DFHBMDAR
    else:
        state.cactupai["INFOMSGA"] = DFHBMASB

    if state.acup_changes_made and not state.acup_changes_okayed_and_done:
        state.cactupai["FKEY12A"] = DFHBMASB

    if state.ws_info_msg == INFO_PROMPT_CONFIRM:
        state.cactupai["FKEY05A"] = DFHBMASB
        state.cactupai["FKEY12A"] = DFHBMASB

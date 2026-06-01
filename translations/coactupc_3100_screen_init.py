"""
coactupc_3100_screen_init.py
Implements 3100-SCREEN-INIT paragraph.
"""

from datetime import datetime
from constants import CCDA_TITLE01, CCDA_TITLE02, LIT_THISTRANID
from state import state


def screen_init():
    """3100-SCREEN-INIT"""
    # Clear the output map
    state.cactupao = {}

    now = datetime.now()

    state.cactupao["CURDATEO"] = now.strftime("%m/%d/%y")
    state.cactupao["CURTIMEO"] = now.strftime("%H:%M:%S")

    state.cactupao["TITLE01O"] = CCDA_TITLE01
    state.cactupao["TITLE02O"] = CCDA_TITLE02
    state.cactupao["TRNNAMEO"] = LIT_THISTRANID
    state.cactupao["PGMNAMEO"] = state.lit_thispgm

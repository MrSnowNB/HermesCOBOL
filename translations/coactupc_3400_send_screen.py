"""3400-SEND-SCREEN translation."""

from typing import Any


def send_screen(state: Any) -> None:
    """3400-SEND-SCREEN.

    MOVE LIT-THISMAPSET TO CCARD-NEXT-MAPSET
    MOVE LIT-THISMAP    TO CCARD-NEXT-MAP

    EXEC CICS SEND MAP(...) MAPSET(...) FROM(CACTUPAO)
                     CURSOR ERASE FREEKB RESP(WS-RESP-CD)
    END-EXEC
    """
    state.ccard_next_mapset = state.ws_literals_lit_thismapset
    state.ccard_next_map = state.ws_literals_lit_thismap

    # EXEC CICS SEND MAP modeled as no-op in Python
    state.ws_resp_cd = 0  # DFHRESP(NORMAL)
    state.cics_send_complete = True

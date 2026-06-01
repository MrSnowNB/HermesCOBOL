"""
coactupc_3000_send_map.py
3000-SEND-MAP orchestrator (stub version).
"""

from coactupc_3xxx_stubs import (
    screen_init,
    setup_screen_vars,
    setup_infomsg,
    setup_screen_attrs,
    setup_infomsg_attrs,
    send_screen,
)


def send_map():
    """3000-SEND-MAP"""
    screen_init()
    setup_screen_vars()
    setup_infomsg()
    setup_screen_attrs()
    setup_infomsg_attrs()
    send_screen()

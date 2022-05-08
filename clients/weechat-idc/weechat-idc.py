import weechat
import socket
import time

weechat.register(
    "weechat-idc",
    "Andrew Yu",
    "0.0.1",
    "UNLICENSE",
    "Internet Delay Chat Protocol for WeeChat",
    "",
    "",
)  # last: shutdown_function and charset


def get_status(data):
    return "this is the result"


def go_idc(data, command, return_code, out, err):
    if return_code == weechat.WEECHAT_HOOK_PROCESS_ERROR:
        weechat.prnt("", "Error with command '%s'" % command)
        return weechat.WEECHAT_RC_OK
    if return_code >= 0:
        weechat.prnt("", "return_code = %d" % return_code)
    if out:
        weechat.prnt("", "stdout: %s" % out)
    if err:
        weechat.prnt("", "stderr: %s" % err)
    return weechat.WEECHAT_RC_OK


hook = weechat.hook_process("func:go_idc", 5000, "go_idc", "")

#!/usr/bin/env python3
#
# Various utility functions for the Internet Delay Chat server written
# in Python Trio.  This library is not intended to be used outside of
# that program.
#
# Written by: Andrew <https://www.andrewyu.org>
#             luk3yx <https://luk3yx.github.io>
#
# This is free and unencumbered software released into the public
# domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

# FIXME 1: We need to make a function that takes in a
#          (bytes, dict[bytes, bytes]) for (cmd, {option: value})
#          and spits out a bytes that's valid and escaped raw IDC
#          Let's call that a "standard tuple".

# FIXME 2: User exceptions should raise (critLevel, errorId, comment)
#          typed (bytes, bytes, bytes), which then gets caught by the
#          main loop, which calls the client's writeErr method with the
#          tuple (let's call it an "error tuple").  The writeErr
#          method needs definition in entities.py, and we need an
#          error tuple to standard tuple converter in utils.py (here).

from __future__ import annotations
from typing import TypeVar

import sys
import re
import time


# Logging


class textStyle:
    reset = "\033[0m"
    fgBlack = "\033[30m"
    fgBrightBlack = "\033[30;1m"
    bgBlack = "\033[40m"
    bgBrightBlack = "\033[40;1m"
    fgRed = "\033[31m"
    fgBrightRed = "\033[31;1m"
    bgRed = "\033[41m"
    bgBrightRed = "\033[41;1m"
    fgGreen = "\033[32m"
    fgBrightGreen = "\033[32;1m"
    bgGreen = "\033[42m"
    bgBrightGreen = "\033[42;1m"
    fgYellow = "\033[33m"
    fgBrightYellow = "\033[33;1m"
    bgYellow = "\033[43m"
    bgBrightYellow = "\033[43;1m"
    fgBlue = "\033[34m"
    fgBrightBlue = "\033[34;1m"
    bgBlue = "\033[44m"
    bgBrightBlue = "\033[44;1m"
    fgMagenta = "\033[35m"
    fgBrightMagenta = "\033[35;1m"
    bgMagenta = "\033[45m"
    bgBrightMagenta = "\033[45;1m"
    fgCyan = "\033[36m"
    fgBrightCyan = "\033[36;1m"
    bgCyan = "\033[46m"
    bgBrightCyan = "\033[46;1m"
    fgWhite = "\033[37m"
    fgBrightWhite = "\033[37;1m"
    bgWhite = "\033[47m"
    bgBrightWhite = "\033[47;1m"


def logDebug(s: str) -> None:
    print(textStyle.reset + "[D] " + s + textStyle.reset, file=sys.stdout)


def logInfo(s: str) -> None:
    print(textStyle.fgGreen + "[I] " + s + textStyle.reset, file=sys.stdout)


def logNote(s: str) -> None:
    print(textStyle.fgBrightBlue + "[N] " + s + textStyle.reset, file=sys.stdout)


def logCaution(s: str) -> None:
    print(textStyle.fgBrightYellow + "[C] " + s + textStyle.reset, file=sys.stdout)


def logWarning(s: str) -> None:
    print(textStyle.fgYellow + "[W] " + s + textStyle.reset, file=sys.stdout)


def logError(s: str) -> None:
    print(textStyle.fgRed + "[E] " + s + textStyle.reset, file=sys.stdout)


# Custom Exceptions


class IDCUserCausedException(Exception):
    pass


class EscapeSequenceError(IDCUserCausedException):
    """
    I don't know this escape sequence
    """

    pass


class MultiCommandError(IDCUserCausedException):
    """
    Multiple commands in one line
    """

    pass


class MessageUndeliverableError(IDCUserCausedException):
    """
    User to deliver message to is offline and doesn't have the
    offline-messages option.
    """

    pass


class UserNotFoundError(IDCUserCausedException):
    """
    Raise this for clients trying to message, modify, or otherwise
    interact with a nonexistant user.
    """

    pass


class StrangeError(IDCUserCausedException):
    """
    Random errors that shouldn't exist and were probably caused by
    either the hardware blowing up or huge bugs.
    """

    pass


# Utility functions


def bytesToArgs(msg: bytes) -> tuple[bytes, dict[bytes, bytes]]:
    """
    Parses a raw IDC message into the command and key/value pairs.
    Example: PRIVMSG TARGET:yay MESSAGE:Hi
    (b'PRIVMSG', {b'TARGET': b'yay', b'MESSAGE': b'Hi'})
    """
    _esc_re = re.compile(rb"\\(.)")
    _idc_escapes = {
        b"\\": b"\\\\",  # Note that Python is escaping backslashes
        # already, this is only one backslash in the
        # bytes sense
        b"r": b"\r",
        b"n": b"\n",
        b"t": b"\t",
    }
    cmd = b""
    args = {}
    for arg in msg.split(b"\t"):
        if b":" in arg:
            key, value = arg.split(b":", 1)

            def s(m: re.Match[bytes]) -> bytes:
                try:
                    return _idc_escapes[m.group(1)]
                except KeyError:
                    raise EscapeSequenceError(
                        "%s is an invalid escape sequence"  # FIXME 1
                        % ("\\" + repr(m.group(1))[2:-1])
                    )

            args[key] = _esc_re.sub(
                s,
                value,
            )
        else:
            if not cmd:
                cmd = arg
            else:
                raise MultiCommandError(b"X")  # FIXME 1
    return cmd, args


def ts() -> bytes:
    """
    Return the current floating-point timestamp as a bytestring.
    """
    return str(time.time()).encode("utf-8")


T = TypeVar("T")
U = TypeVar("U")


def getKeyByValue(d: dict[T, U], s: U) -> list[T]:
    """
    From a dictionary d, retreive all keys that have value s, returned
    as a list.
    """
    # FIXME: Determine if calling getKeyByValue with specific types once
    #        limit the function's future usage to original types.
    r = []
    for k, v in d.items():
        if s == v:
            r.append(k)
    return r


exit = sys.exit

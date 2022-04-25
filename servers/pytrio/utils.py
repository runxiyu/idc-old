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
#
# FIXME 1: We need to make a function that takes in a
#          (bytes, dict[bytes, bytes]) for (cmd, {option: value})
#          and spits out a bytes that's valid and escaped raw IDC
#          Let's call that a "standard tuple".
#
# FIXME 2: User exceptions should raise (critLevel, errorId, comment)
#          typed (bytes, bytes, bytes), which then gets caught by the
#          main loop, which calls the client's writeErr method with the
#          tuple (let's call it an "error tuple").  The writeErr
#          method needs definition in entities.py, and we need an
#          error tuple to standard tuple converter in utils.py (here).

from __future__ import annotations
from typing import TypeVar, Iterator, Optional

import sys
import re
import time

# Custom Exceptions

class IDCUserCausedException(Exception):
    """
    Should be subclassed by all of the 'user did something wrong' errors
    """
    pass


class NonAlphaKeyError(IDCUserCausedException):
    """
    Putting non-letters into keywords
    """

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

_esc_re = re.compile(rb"\\(.)")
_idc_escapes = {
    b"\\": b"\\\\",
    b"r": b"\r",
    b"n": b"\n",
    b"t": b"\t",
}


def _get_idc_args(
    command: bytes, kwdict: dict[str, Optional[bytes]]
) -> Iterator[bytes]:
    yield command.upper()
    for key, value in kwdict.items():
        if value is not None:
            for escape_char, char in _idc_escapes.items():
                value = value.replace(char, b"\\" + escape_char)
            yield key.upper().encode("ascii") + b":" + value
            # FIXME 4: Possible key collision:
            #          {"a": b"t1", "A": b"t2"} -> {"A": b"undefined"}


def stdToBytes(command: bytes, **kwargs: Optional[bytes]) -> bytes:
    """
    Turns a standard tuple into a raw IDC message, adding the final
    CR-LF
    """
    # TODO: Why are we even using a _get_idc_args function here?  Why
    # do we need to use that iterator (yield)?  Eating Test_User is a
    # very bad idea, too!
    return b"\t".join(_get_idc_args(command, kwargs)) + b"\r\n"


def bytesToStd(msg: bytes) -> tuple[bytes, dict[str, bytes]]:
    """
    Parses a raw IDC message into the command and key/value pairs.
    The message MUST contain the CR-LF.
    Example: PRIVMSG TARGET:yay MESSAGE:Hi
    (b'PRIVMSG', {b'TARGET': b'yay', b'MESSAGE': b'Hi'})
    """
    cmd = b""
    args = {}
    for arg in msg.split(b"\t"):
        if b":" in arg:
            key, value = arg.split(b":", 1)

            try:
                _ = key.decode("ascii")
            except UnicodeDecodeError:
                raise NonAlphaKeyError()
            else:
                if not _.isalpha():
                    raise NonAlphaKeyError("")  # FIXME 2

            def s(m: re.Match[bytes]) -> bytes:
                try:
                    return _idc_escapes[m.group(1)]
                except KeyError:
                    raise EscapeSequenceError(
                        "%s is an invalid escape sequence"  # FIXME 2
                        % ("\\" + repr(m.group(1))[2:-1])
                    )

            args[_] = _esc_re.sub(
                s,
                value,
            )
        else:
            if not cmd:
                cmd = arg
            else:
                raise MultiCommandError()  # FIXME 2
    return cmd, args


SUCCESS = b"SUCCESS"
FAIL = b"FAIL"
EXTRA = b"EXTRA"
ERROR = b"ERROR"


def replyToStd(
    r: tuple[bytes, bytes, bytes, bytes, dict[str, bytes]],
    #        level, cookie, reply, comment, additional
) -> tuple[bytes, dict[str, bytes]]:
    """
    Convert a reply tuple to a standard tuple.
    """
    try:
        a = r[4]
        a["COOKIE"] = r[1]
        a["REPLY"] = r[2]
        a["COMMENT"] = r[3]
        return (
            r[0].upper(),
            a,
        )
    except KeyError as e:
        raise e


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

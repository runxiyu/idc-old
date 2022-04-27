#!/usr/bin/env python3
#
# This program is made by the World Sus Foundation by Andrew.
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
#
# FIXME 2: Exceptions due to bad user input are defined in
#          exceptions.py.  Each of those exceptions MUST have these
#          attributes, and MUST be caught by the client main loop.
#
#          Necessary attributes:
#          (1) severity
#          (2) errorType
#          (3) yay
#

from __future__ import annotations
from typing import TypeVar, Iterator, Optional

import sys
import re
import time

import exceptions

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
    # Working with errors
    yield command.upper()
    seen = set()
    for key, value in kwdict.items():
        key = key.upper()
        assert key not in seen
        seen.add(key)
        if value is not None:
            for escape_char, char in _idc_escapes.items():
                value = value.replace(char, b"\\" + escape_char)
            yield key.encode("ascii") + b":" + value
            # FIXED 4: Possible key collision:
            #          Assigned to: luk3yx
            #          {"a": b"t1", "A": b"t2"} -> {"A": b"undefined"}
            # Will now raise AssertionError


def stdToBytes(command: bytes, **kwargs: Optional[bytes]) -> bytes:
    """
    Turns a standard tuple into a raw IDC message, adding the final
    CR-LF
    """
    # Good
    return b"\t".join(_get_idc_args(command, kwargs)) + b"\r\n"


def bytesToStd(msg: bytes) -> tuple[bytes, dict[str, bytes]]:
    """
    Parses a raw IDC message into the command and key/value pairs.
    The message MUST contain the CR-LF.
    Example: PRIVMSG TARGET:yay MESSAGE:Hi
    (b'PRIVMSG', {b'TARGET': b'yay', b'MESSAGE': b'Hi'})
    """
    # Working with errors
    cmd = b""
    args = {}
    for arg in msg.split(b"\t"):
        if b":" in arg:
            key, value = arg.split(b":", 1)

            try:
                key_str = key.decode("ascii")
            except UnicodeDecodeError:
                raise exceptions.NonAlphaKeyError(
                    "The key of every argument must be an ASCII letter-only sequence."
                )
            else:
                if not key_str.isalpha():
                    raise exceptions.NonAlphaKeyError(
                        "The key of every argument must be an ASCII letter-only sequence."
                    )

            def s(m: re.Match[bytes]) -> bytes:
                try:
                    return _idc_escapes[m.group(1)]
                except KeyError:
                    raise exceptions.EscapeSequenceError(
                        "%s is an invalid escape sequence"  # FIXME 2
                        % ("\\" + repr(m.group(1))[2:-1])
                    )

            args[key_str] = _esc_re.sub(
                s,
                value,
            )
        elif cmd is not None:
            raise exceptions.MultiCommandError()  # FIXME 2
        else:
            cmd = arg
    return cmd, args


SUCCESS = b"SUCCESS"
FAIL = b"FAIL"
EXTRA = b"EXTRA"
ERROR = b"ERROR"


# Bugged, FIXME!
# What is broken?
# What if the dict contains COOKIE and REPLY and COMMENT? We're
# overriding them
# Also why are you using a tuple and not arguments
# not sure
# anyways, I've made up my mind to not use methods
# they suck
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


# Good
def ts() -> bytes:
    """
    Return the current floating-point timestamp as a bytestring.
    """
    return str(time.time()).encode("utf-8")


T = TypeVar("T")
U = TypeVar("U")


# Good
def getKeyByValue(d: dict[T, U], s: U) -> list[T]:
    """
    From a dictionary d, retreive all keys that have value s, returned
    as a list.
    """
    r = []
    for k, v in d.items():
        if s == v:
            r.append(k)
    return r


exit = sys.exit

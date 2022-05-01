#!/usr/bin/env python3
#
# This program is made by the World Sus Foundation by luky3x.  No rights
# reserved.
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

from __future__ import annotations
from typing import TypeVar, Iterator, Optional, Union

import sys
import re
import time

import minilog
import exceptions
import entities

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
    seen = set()
    for key, value in kwdict.items():
        key = key.upper()
        if key in seen:
            raise exceptions.KeyCollisionError(
                key.encode("ascii")
                + b" was already seen in the arguments."
            )
        seen.add(key)
        if value is not None:
            for escape_char, char in _idc_escapes.items():
                value = value.replace(char, b"\\" + escape_char)
            yield key.encode("ascii") + b":" + value


def stdToBytes(command: bytes, **kwargs: Optional[bytes]) -> bytes:
    """
    Turns a standard tuple into a raw IDC message, adding the final
    CR-LF.
        "Hey!  Saw that underscore?  Why are you even looking at this?"
    """
    r = b"\t".join(_get_idc_args(command, kwargs)) + b"\r\n"
    return r


def bytesToStd(msg: bytes) -> tuple[bytes, dict[str, bytes]]:
    """
    Parses a raw IDC message into the command and key/value pairs.
    The message MUST contain the CR-LF.
    Example: PRIVMSG TARGET:yay MESSAGE:Hi
    (b'PRIVMSG', {b'TARGET': b'yay', b'MESSAGE': b'Hi'})
    """
    if msg.endswith(b"\n"):
        msg = msg[:-1]
    if msg.endswith(b"\r"):
        msg = msg[:-1]
    cmd = b""
    args = {}
    for arg in msg.split(b"\t"):
        if b":" in arg:
            key, value = arg.split(b":", 1)
            key = key.upper()

            try:
                key_str = key.decode("ascii")
            except UnicodeDecodeError:
                raise exceptions.NonAlphaKeyError(
                    b"Argument keys must be ASCII aplphabet sequences.  (decode error)"
                )
            else:
                if not key_str.isalpha():
                    raise exceptions.NonAlphaKeyError(
                        b"Argument keys must be ASCII aplphabet sequences. (not isalpha)"
                    )

            def s(m: re.Match[bytes]) -> bytes:
                try:
                    return _idc_escapes[m.group(1)]
                except KeyError:
                    raise exceptions.EscapeSequenceError(
                        b"\\"
                        + m.group(1)
                        + b"is an invalid escape sequence."
                    )

            args[key_str] = _esc_re.sub(
                s,
                value,
            )
        elif cmd != b"":
            raise exceptions.MultiCommandError(
                b"You can't use multiple commands inside one line!"
            )
        else:
            cmd = arg
    return cmd, args


def ts() -> bytes:
    """
    Return the current floating-point timestamp as a bytestring.
    """
    return str(time.time()).encode("ascii")


T = TypeVar("T")
U = TypeVar("U")


def carg(
    adict: dict[str, bytes], key: str, cmd: bytes = b"This command"
) -> bytes:
    try:
        return adict[key]
    except KeyError:
        raise exceptions.MissingArgumentError(
            cmd
            + b" requires an argument with the key "
            + key.encode("utf-8")
            + b" but was not provided."
        )


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


V = Union[entities.Client, entities.User]


async def send(
    thing: V, command: bytes, **kwargs: Optional[bytes]
) -> None:
    if isinstance(thing, entities.Client):
        await thing.stream.send_all(stdToBytes(command, **kwargs))
    elif isinstance(thing, entities.User):
        pass  # TODO


def exit(i: int) -> None:
    sys.exit(i)


def add_client_to_user(c: entities.Client, u: entities.User) -> None:
    u.connected_clients.append(c)
    c.user = u

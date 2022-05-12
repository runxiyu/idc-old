#!/usr/bin/env python3
#
# Entities library for Internet Delay Chat server written in Python
# Trio.  Don't run this.
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
from typing import Optional, Union, List, Sequence
from dataclasses import dataclass, field
import trio.abc


@dataclass
class Server:
    # stub, we're not using it just yet
    rvalue: bytes
    domain: bytes
    users: dict[bytes, User]


@dataclass
class User:
    username: bytes
    password: bytes
    options: list[str]
    connected_clients: list[Client] = field(default_factory=list)
    in_channels: list[Channel] = field(default_factory=list)
    queue: list[bytes] = field(default_factory=list)


@dataclass
class Client:
    cid: bytes
    stream: trio.abc.Stream
    user: Optional[User] = None


@dataclass
class Guild:
    guildname: bytes
    users: list[User]
    channels: list[Channel]


@dataclass
class Channel:
    channelname: bytes
    guild: Optional[Guild]
    broadcast_to: list[User]



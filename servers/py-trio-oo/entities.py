#!/usr/bin/env python3
#
# Entities for use in the Internet Delay Chat server written in Python
# Trio.  Not intended to be used anywhere else or ran independently.
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

from __future__ import annotations
from dataclasses import dataclass

# from dataclasses import field
# from typing import TypeVar
from typing import Optional

import trio

import utils


@dataclass
class Server:
    """
    This Server class represents both the local ("this") server, and
    remote servers.
    """

    name: bytes
    users: dict[bytes, User]
    clients: Optional(dict[bytes, User])
    guilds: dict[bytes, Guild]

    def topologyLink(self, srv: Server):
        pass

    def topologyDelink(self, srv: Server):
        pass


@dataclass
class User:
    """
    This User class handles both local and remote users.
    """

    name: bytes


@dataclass
class Client:
    clientId: bytes
    # The clientId is now specified by the main loop.  Therefore the
    # class itself doesn't care about  what ID it gets and about putting
    # itself into the global clients dictionary.

    belongsToUser: User  # This should be None by default?
    stream: trio.SocketStream

    async def writeRaw(self, toWrite: bytes) -> None:  # None?
        return await self.stream.send_all(toWrite)

    async def writeStd(
        self, std: tuple[bytes, dict[bytes, bytes]]
    ) -> None:
        await self.writeRaw(utils.stdToBytes(std[0], **std[1]))

    async def send(
        self, command: bytes, **kwargs: Optional[bytes]
    ) -> None:
        await self.writeRaw(utils.stdToBytes(command, **kwargs))

    async def destroy(self):
        """
        Note that this function only stops the stream, it doesn't remove
        itself from its user's client list or anything; the User should
        have a method to do that.

        OO is yay!
        Also why do you need a method in User to do that? What's wrong
        with removing it from here?

        Beause our current way of doing this is, the thing that contains
        the more minor thing removes it; i mean the client doesn't
        assign its own client id, it's assigned by the mainloop, we need
        some consistency otherwise this OO gets into a big mess
        """
        pass


@dataclass
class Guild:
    pass

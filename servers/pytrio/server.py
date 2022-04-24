#!/usr/bin/env python3
#
# Internet Delay Chat server written in Python Trio.
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

from itertools import count
import trio
import secrets

import entities
import utils
import config

CONNECTION_COUNTER = count()
clients = dict[bytes, entities.Client]


async def clientLoop(serverStream: trio.SocketStream) -> None:
    clientId = str(int(next(CONNECTION_COUNTER)))
    utils.logInfo(f"{clientId}: started")
    try:
        async for data in serverStream:
            try:
                utils.logDebug(f"{clientId} >> {data!r}")
                await serverStream.send_all(data)
                utils.logDebug(f"{clientId} << {data!r}")
            except utils.IDCUserCausedException as exc:
                utils.logNote(f"{clientId}: {exc!r}")
        utils.logInfo(f"{clientId} EOF")
    except Exception as exc:
        utils.logWarning(f"{clientId}: {exc!r}")


async def main() -> None:
    await trio.serve_tcp(clientLoop, config.listen.port)


if __name__ == "__main__":
    try:
        trio.run(main)
    except KeyboardInterrupt:
        utils.logError("KeyboardInterrupt")
        utils.exit(0)

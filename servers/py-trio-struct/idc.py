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
#
# This program requires Python 3.9 or later due to its extensive use of
# type annotations.  Usage with an older version would likely cause
# SyntaxErrors.  If mypy has problems detecting types on the Trio
# library, install trio-typing.  Please mypy after every runnable edit.
#

from __future__ import annotations
from itertools import count
import trio
import minilog

import exceptions
import entities
import utils
import config

PORT = 6835

client_id_counter = count()
local_users: dict[bytes, entities.User] = {}

for username in config.users:
    local_users[username] = entities.User(
        username=username,
        password=config.users[username]["password"],
        options=config.users[username]["options"],
    )


async def connection_loop(stream: trio.SocketStream) -> None:
    ident = bytes(next(client_id_counter))
    minilog.note(f"Connection {str(ident)} has started.")
    client = entities.Client(cid=ident, stream=stream)
    try:
        async for data in stream:
            minilog.debug(f"I got {data!r} from {ident!r}")
            try:
                cmd, args = utils.bytesToStd(data)
                cmd = cmd.upper()
                # Begin main actions
                if cmd == b"LOGIN":
                    if client.user:
                        raise exceptions.AlreadyLoggedIn(b"You are already logged in as " + client.user.username + b".")
                    else:
                        attempting_username = utils.carg(
                            args, "USERNAME", b"LOGIN"
                        )
                        attempting_password = utils.carg(
                            args, "PASSWORD", b"LOGIN"
                        )
                        try:
                            if (
                                local_users[attempting_username].password
                                == attempting_password
                            ):
                                utils.add_client_to_user(
                                    client, local_users[attempting_username]
                                )
                                await utils.send(
                                    client,
                                    b"LOGIN_GOOD",
                                    USERNAME=attempting_username,
                                    COMMENT=b"Login is good.",
                                )
                            else:
                                raise exceptions.LoginFailed(
                                    b"Invalid password for "
                                    + attempting_username
                                    + b"."
                                )
                        except KeyError:
                            raise exceptions.LoginFailed(
                                attempting_username
                                + b" is not a registered username."
                            )
                else:
                    raise exceptions.UnknownCommand(cmd + b" is an unknown command.")
                # End main actions
            except exceptions.IDCUserCausedException as e:
                await utils.send(
                    client,
                    e.severity,
                    E=e.error_type,
                    COMMENT=e.args[0],
                )
    except Exception as exc:
        minilog.warning(f"{ident!r}: crashed: {exc!r}")


async def main() -> None:
    await trio.serve_tcp(connection_loop, PORT)


if __name__ == "__main__":
    try:
        minilog.note("Definitions complete.  Establishing listener.")
        trio.run(main)
    except KeyboardInterrupt:
        minilog.error("KeyboardInterrupt!")

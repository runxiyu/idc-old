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
from typing import Awaitable, Callable
import trio
import minilog
import traceback

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


_CMD_HANDLER = Callable[
    [entities.Client, "dict[str, bytes]"], Awaitable[None]
]
_registered_commands: dict[bytes, _CMD_HANDLER] = {}


def register_command(
    command: str,
) -> Callable[[_CMD_HANDLER], _CMD_HANDLER]:
    def register_inner(func: _CMD_HANDLER) -> _CMD_HANDLER:
        _registered_commands[command.encode("ascii")] = func
        return func

    return register_inner


@register_command("HELP")
async def _help_cmd(
    client: entities.Client, args: dict[str, bytes]
) -> None:
    await utils.send(
        client,
        b"HELP",
        available_commands=b",".join(_registered_commands),
    )


@register_command("LOGIN")
async def _login_cmd(
    client: entities.Client, args: dict[str, bytes]
) -> None:
    if client.user:
        raise exceptions.AlreadyLoggedIn(
            b"You are already logged in as "
            + client.user.username
            + b"."
        )

    attempting_username = utils.carg(args, "USERNAME", b"LOGIN")
    attempting_password = utils.carg(args, "PASSWORD", b"LOGIN")
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
            assert client.user is not None
            if client.user.queue:
                for q in client.user.queue[-1::-1]:
                    await utils.quote(client, q)
                client.user.queue = []
        else:
            raise exceptions.LoginFailed(
                b"Invalid password for " + attempting_username + b"."
            )
    except KeyError:
        raise exceptions.LoginFailed(
            attempting_username + b" is not a registered username."
        )


@register_command("PING")
async def _ping_cmd(
    client: entities.Client, args: dict[str, bytes]
) -> None:
    await utils.send(client, b"PONG", cookie=utils.carg(args, "COOKIE"))


@register_command("EGG")
async def _egg_cmd(
    client: entities.Client, args: dict[str, bytes]
) -> None:
    await utils.send(
        client,
        b"EASTER_EGG",
        moocow=b"MOOCOWS ARE OFTC",
        cat=b"LIBERACHAT LOL",
    )


@register_command("PRIVMSG")
async def _privmsg_cmd(
    client: entities.Client, args: dict[str, bytes]
) -> None:  # in the future this should return the raw line sent to the target client
    if not client.user:
        raise exceptions.NotLoggedIn(
            b"You can't use PRIVMSG before logging in!"
        )
    else:
        target_name = utils.carg(args, "TARGET")
        try:
            target_user = local_users[target_name]
        except KeyError:
            raise exceptions.NonexistantTargetError(
                b"The target " + target_name + b" is nonexistant."
            )
        else:
            await utils.send(
                local_users[utils.carg(args, "TARGET")],
                b"PRIVMSG",
                source=client.user.username,
                target=utils.carg(args, "TARGET"),
                message=utils.carg(args, "MESSAGE"),
            )
            await utils.send(
                client.user,
                b"PRIVMSG",
                source=client.user.username,
                target=utils.carg(args, "TARGET"),
                message=utils.carg(args, "MESSAGE"),
            )
        # Do you think that we should put echo-message here, or in utils.send()?


async def connection_loop(stream: trio.SocketStream) -> None:
    ident = bytes(next(client_id_counter))
    minilog.note(f"Connection {str(ident)} has started.")
    client = entities.Client(cid=ident, stream=stream)
    try:
        async for data in stream:
            if data == b"\r\n":
                continue
            minilog.debug(f"I got {data!r} from {ident!r}")
            try:
                cmd, args = utils.bytesToStd(data)
                cmd = cmd.upper()
                if cmd in _registered_commands:
                    await _registered_commands[cmd](client, args)
                else:
                    raise exceptions.UnknownCommand(
                        cmd + b" is an unknown command."
                    )
            except exceptions.IDCUserCausedException as e:
                await utils.send(
                    client,
                    e.severity,
                    PROBLEM=e.error_type,
                    COMMENT=e.args[0],
                )
    except Exception as exc:
        traceback.print_exc()
        minilog.warning(f"{ident!r}: crashed: {exc!r}")
    finally:
        if client.user:
            client.user.connected_clients.remove(client)
        del client.stream
        del client
        minilog.note(f"Connection {str(ident)} has ended.")


async def main() -> None:
    await trio.serve_tcp(connection_loop, PORT)


if __name__ == "__main__":
    try:
        minilog.note("Definitions complete.  Establishing listener.")
        trio.run(main)
    except KeyboardInterrupt:
        minilog.error("KeyboardInterrupt!")

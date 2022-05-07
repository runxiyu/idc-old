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
import time

from typing import Awaitable, Callable
import trio
import minilog
import traceback

import exceptions
import entities
import utils
import config

starttime = time.time()

PORT = 6835

client_id_counter = -1
local_users: dict[bytes, entities.User] = {}
local_channels: dict[bytes, entities.Channel] = {}

for username in config.users:
    local_users[username] = entities.User(
        username=username,
        password=config.users[username]["password"],
        options=config.users[username]["options"],
    )

for channelname in config.channels:
    local_channels[channelname] = entities.Channel(
        channelname=channelname,
        broadcast_to=[
            local_users[username]
            for username in config.channels[channelname]["broadcast_to"]
        ],
        guild=None,
    )
    for u in local_channels[channelname].broadcast_to:
        u.in_channels.append(local_channels[channelname])


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
        AVAILABLE_COMMANDS=b" ".join(_registered_commands),
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
            client.user = local_users[attempting_username]
            local_users[attempting_username].connected_clients.append(
                client
            )
            await utils.send(
                client,
                b"LOGIN_GOOD",
                USERNAME=attempting_username,
                COMMENT=b"Login is good.",
            )
            assert client.user is not None
            for c in client.user.in_channels:
                await utils.send(
                    client,
                    b"JOIN",
                    CHANNEL=c.channelname,
                    USERS=b" ".join(
                        [u.username for u in c.broadcast_to]
                    ),
                )
            await utils.send(
                client,
                b"END_BURST",
                COMMENT=b"I'm finished telling you the state you're in.",
            )
            if client.user.queue:
                for q in client.user.queue:
                    await utils.quote(client, q)
                    client.user.queue.remove(q)
            for channel in client.user.in_channels:
                if channel.queue:
                    minilog.debug(f"{client.user.username!r} is looking for its offline queue of {channel.channelname!r}")
                    for mqm in channel.queue:
                        minilog.debug(f"{client.user.username!r} found a mqm for {channel.channelname!r}: {mqm.data!r} for {b', '.join([u.username for u in mqm.targets])!r}")
                        if client.user in mqm.targets:
                            minilog.debug(f"{client.user.username!r} sees that the mqm is for them!!")
                            await utils.quote(client, mqm.data)
                            mqm.targets.remove(client.user)
                            minilog.debug(f"{client.user.username!r} removes itself from the {channel.channelname!r} mqm: {mqm.data!r} for {b', '.join([u.username for u in mqm.targets])!r}")
                            if len(mqm.targets) == 1:
                                channel.queue.remove(mqm)
            await utils.send(
                client,
                b"END_OFFLINE_MESSAGES",
                COMMENT=b"I'm finished telling you your offline messages.",
            )
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
    await utils.send(client, b"PONG", COOKIE=utils.carg(args, "COOKIE"))


@register_command("EGG")
async def _egg_cmd(
    client: entities.Client, args: dict[str, bytes]
) -> None:
    await utils.send(
        client,
        b"EASTER_EGG",
        YAY=b"luk3yx: Never gonna give you up\nnever gonna let you down\nnever gonna run around and desert you\nnever gonna make you cry\nnever gonna say goodbye\nnever gonna tell a lie and hurt you",
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
                target_user,
                b"PRIVMSG",
                SOURCE=client.user.username,
                TYPE=args.get("TYPE", b"NORMAL"),
                TARGET=utils.carg(args, "TARGET"),
                MESSAGE=utils.carg(args, "MESSAGE"),
            )
            if target_user is not client.user:
                await utils.send(
                    client.user,
                    b"PRIVMSG",
                    SOURCE=client.user.username,
                    TYPE=args.get("TYPE", b"NORMAL"),
                    TARGET=utils.carg(args, "TARGET"),
                    MESSAGE=utils.carg(args, "MESSAGE"),
                )
        # Do you think that we should put echo-message here, or in utils.send()?


@register_command("CHANMSG")
async def _chanmsg_cmd(
    client: entities.Client, args: dict[str, bytes]
) -> None:
    if not client.user:
        raise exceptions.NotLoggedIn(
            b"You can't use CHANMSG before logging in!"
        )
    else:
        target_channel_name = utils.carg(args, "TARGET")
        try:
            target_channel = local_channels[target_channel_name]
        except KeyError:
            raise exceptions.NonexistantTargetError(
                b"The target channel "
                + target_channel_name
                + b"is nonexistant."
            )
        else:

            await utils.send(
                target_channel,
                b"CHANMSG",
                SOURCE=client.user.username,
                TYPE=args.get("TYPE", b"NORMAL"),
                TARGET=target_channel_name,
                MESSAGE=utils.carg(args, "MESSAGE"),
            )


#             await utils.send(
#                 client.user,
#                 b"CHANMSG",
#                 source=client.user.username,
#                 target=target_channel_name,
#                 message=utils.carg(args, "MESSAGE"),
#             )


async def connection_loop(stream: trio.SocketStream) -> None:
    global client_id_counter
    client_id_counter += 1
    ident = str(client_id_counter).encode("ascii")
    minilog.note(f"Connection {str(ident)} has started.")
    client = entities.Client(cid=ident, stream=stream)
    await utils.send(client, b"MOTD", MESSAGE=config.motd)
    try:
        msg = b""
        async for newmsg in stream:
            msg += newmsg
            split_msg = msg.split(b"\r\n")
            if len(split_msg) < 2:
                continue
            data = split_msg[0:-1]
            msg = split_msg[-1]
            minilog.debug(f"I got {data!r} from {ident!r}")
            for cmdline in data:
                try:
                    cmd, args = utils.bytesToStd(cmdline)
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
    finally:
        minilog.note(f"I've ran for {str(time.time() - starttime)} seconds!")

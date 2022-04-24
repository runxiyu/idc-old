#!/bin/sh
# Internet Delay Chat Server
# Example implementation in Python asyncio
#
# The Internet Delay Chat specifications and implementations are all under
# heavy development.  No stability may be expected.
#
# This software likely contains critical bugs.
#
# By: luk3yx <https://luk3yx.github.io>
#     Andrew Yu <https://www.andrewyu.org>
#     Test_User <https://users.andrewyu.org/~hax>
#
# This is free and unencumbered software released into the public domain.
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
# Todo list:
# - Guilds and channels
# - Use sources correctly, i.e. :andrew@andrewyu.org
# - Presence list
# - Federation, and usernames should contain the server name somehow
# - TLS
# - VOIP
# - Moderation
# - haxlurking
# - MAKE A CLIENT!

from __future__ import annotations

import time
import asyncio
import logging
import secrets

import config

from dataclasses import (
    dataclass,
    field,
)

logging.basicConfig(level=logging.DEBUG)


class UserNotFoundError(Exception):
    pass


class StrangeError(Exception):
    pass


@dataclass
class Client:
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter


@dataclass
class User:
    username: bytes
    password: bytes
    bio: bytes
    permissions: set[bytes]
    options: set[bytes]
    clients: list[Client] = field(default_factory=list)
    queue: list[bytes] = field(default_factory=list)


@dataclass
class _PermissionSet:
    permissions: set[bytes]
    anti_permissions: set[bytes]
    management_permissions: set[bytes]


@dataclass
class Role(_PermissionSet):
    name: bytes
    channel_overrides: dict[bytes, PermissionSet]


@dataclass
class Channel:
    name: bytes
    users: list[bytes]


@dataclass
class Guild:
    name: bytes
    description: bytes
    users: list[bytes]
    userRoles: dict[bytes, set[bytes]]
    roles: dict[bytes, Role]
    channels: dict[bytes, Channel]


clients: dict[bytes, Client] = {}
client_id_count = 0
users = {name: User(username=name, **user) for name, user in config.users.items()}
guilds = {name: Guild(name=name, **guild) for name, guild in config.guilds.items()}


def broadcastToGuild(
    guildname,
):
    pass


def getKeyByValue(d, s):
    r = []
    for k, v in d.items():
        if s == v:
            r.append(k)
    return r


def getCidByWriter(writer):
    r = getKeyByValue(clients, writer)
    if len(r) > 1:
        raise StrangeError("Two CIDs have the same writer?")
    elif len(r) == 1:
        return r[0]
    else:
        raise StrangeError("Writer exists but doesn't have a CID?")


async def argWrite(writer, *args):
    line = (
        b"\t".join(arg.replace(b"\\", b"\\\\").replace(b"\t", b"\\\t") for arg in args)
        + b"\r\n"
    )
    logging.info(getCidByWriter(writer) + " <<< " + repr(line))
    writer.write(line)
    del line
    await writer.drain()


async def sendToAllClientsOfUser(username, *args):
    if users[username].clients:
        i = 0
        for cid in users[username].clients:
            writer = clients[cid]
            await argWrite(writer, *args)
            i += 1
        return i
    elif "offline-messages" in users[username].options:
        line = (
            b"\t".join(
                arg.replace(b"\\", b"\\\\").replace(b"\t", b"\\\t") for arg in args
            )
            + b"\r\n"
        )
        users[username].queue.append(line)
        return False
    return None


async def checkedTimedOriginedMessageToUser(
    originUsername, targetUsername, command, text
):
    if targetUsername in users.keys():
        return await sendToAllClientsOfUser(
            targetUsername,
            command,
            str(time.time()).encode("utf-8"),
            originUsername,
            text,
        )
    else:
        return UserNotFoundError("User nonexistant")


async def clientLoop(reader, writer):
    addr = writer.get_extra_info("peername")
    global client_id_count
    cid = str(client_id_count)
    client_id_count += 1
    clients[cid] = writer
    loggedIn = False
    loggedInAs = None
    ln = b""
    while True:
        newln = await reader.read(512)
        if newln == b"":
            break
        ln += newln
        lnSplt = ln.split(b"\r\n")
        if len(lnSplt) < 2:
            continue
        msg = lnSplt[0]
        ln = b""

        escaped = False
        args = []
        current = b""
        for b in [msg[i : i + 1] for i in range(len(msg))]:
            if escaped:
                if b == b"\\":
                    current += b"\\"
                elif b == b"\t":
                    current += b"\t"
                else:
                    current += b""
                escaped = False
            elif b == b"\\":
                escaped = True
            elif b == b"\t":
                args.append(current)
                current = b""
            else:
                current += b
        del escaped
        args.append(current)
        del current

        if not args[0]:
            continue

        logging.debug(cid + " >>> " + repr(args))
        cmd = args[0].upper()

        if cmd == b"SERVER":
            await argWrite(
                writer, b"ERR_NOT_IMPLEMENTED", b"Server linkage is unimplemented."
            )
        elif cmd == b"HELP":
            await argWrite(
                writer,
                b"RPL_READ_THE_FREAKING_SOURCE_CODE",
                b"Read the freaking source code!  It's at git://git.andrewyu.org/internet-delay-chat.git.",
            )
        elif cmd == b"USER":
            if len(args) != 3:
                await argWrite(
                    writer,
                    b"ERR_ARGUMEHT_NUMBER",
                    b"The USER command takes two positional arguments: Username and password.",
                )
            elif loggedIn:
                await argWrite(
                    writer,
                    b"ERR_ALREADY_LOGGED_IN",
                    b"You've already logged in, therefore your USER command is invalid.",
                )
            else:
                try:
                    goodPassword = users[args[1]].password
                    # u to undo, dd is "delete line", 4dd is "delete this line and the next three", "cw" is change this word, "5cw" is "change this word and the next four"
                    # redo: ^r
                except KeyError:
                    await argWrite(
                        writer,
                        b"ERR_LOGIN_INVALID",
                        b"The username provided is invalid.",
                    )
                else:
                    if secrets.compare_digest(args[2], goodPassword):
                        await argWrite(
                            writer,
                            b"RPL_LOGIN_GOOD",
                            b"You have logged in as " + args[1] + b".",
                        )
                        loggedInAs = args[1]
                        loggedIn = True
                        users[loggedInAs].clients.append(cid)
                        queue = users[loggedInAs].queue
                        if queue:
                            await argWrite(writer, b"OFFLINE_MESSAGES")
                            for m in queue:
                                writer.write(m)
                            del m
                            users[loggedInAs].queue = []
                            await argWrite(writer, b"END_OFFLINE_MESSAGES")
                        del queue
                    else:
                        await argWrite(
                            writer,
                            b"ERR_PASS_INVALID",
                            b"Incorrect password for " + args[1] + b".",
                        )
        elif cmd == b"DUMP":  # TODO: This is for debugging purposes, obviously
            writer.write(repr(clients).encode("utf-8"))
            writer.write(repr(users).encode("utf-8"))
            await writer.drain()
        elif not loggedIn:
            await argWrite(writer, b"ERR_UNREGISTERED", b"You haven't logged in.")
        elif cmd == b"PRIVMSG":
            if len(args) != 3:
                await argWrite(
                    writer,
                    b"ERR_ARGUMEHT_NUMBER",
                    b"The PRIVMSG command takes two positional arguments: Username and text.",
                )
            else:
                r = await checkedTimedOriginedMessageToUser(
                    loggedInAs, args[1], b"PRIVMSG", args[2]
                )
                if isinstance(r, UserNotFoundError):
                    await argWrite(
                        writer,
                        b"ERR_DESTINATION_NONEXISTANT",
                        b"The destination user " + args[1] + b" does not exist.",
                    )
                elif r is None:
                    await argWrite(
                        writer,
                        b"ERR_NO_OFFLINE_MSGS",
                        b""
                        + args[1]
                        + b" is offline and does not have offline-messages.",
                    )
                del r
        elif cmd == b"KILL":
            if not "kill" in users[loggedInAs].permissions:
                await argWrite(
                    writer,
                    b"ERR_SERVER_PERMS",
                    b"You do not have the permission to use KILL.",
                )
            elif 3 <= len(args) <= 4:
                await argWrite(
                    writer,
                    b"ERR_NOT_IMPLEMENTED",
                    b"The KILL command hasn't been implemented yet.",
                )
            else:
                await argWrite(
                    writer,
                    b"ERR_ARGUMEHT_NUMBER",
                    b"The KILL command takes two positional arguments: Target client and optional reason.",
                )
        elif cmd == b"JOIN":
            if 3 <= len(args) <= 4:
                await argWrite(
                    writer,
                    b"ERR_NOT_IMPLEMENTED",
                    b"The KILL command hasn't been implemented yet.",
                )
            else:
                await argWrite(
                    writer,
                    b"ERR_ARGUMEHT_NUMBER",
                    b"The KILL command takes two positional arguments: Target client and optional reason.",
                )
        else:
            await argWrite(
                writer, b"ERR_UNKNOWN_COMMAND", cmd + b" is an unknown command."
            )

    writer.close()
    try:
        users[loggedInAs].clients.remove(cid)
    except KeyError:
        pass
    del clients[cid]


async def main():
    server = await asyncio.start_server(clientLoop, "", 1025)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())

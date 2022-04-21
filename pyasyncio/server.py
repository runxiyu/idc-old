# Internet Delay Chat Server
# Example implementation in Python asyncio
#
# Copyright (C) 2022  Andrew Yu <https://www.andrewyu.org>
# Copyright (C) 2022  Test_User <https://users.andrewyu.org/~hax>
# Copyright (C) 2022  luk3yx <https://luk3yx.github.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Todo list:
# - Use sources correctly, i.e. :andrew@andrewyu.org
# - Federation, and usernames should contain the server name somehow
# - Guilds and channels
# - TLS
# - VOIP
# - Yay

from __future__ import annotations

import time
import asyncio
import logging
import secrets

import config

from dataclasses import (
    dataclass,
    field,
)  # do it for existing stuff (i.e. fusers and clientsa) first

logging.basicConfig(level=logging.DEBUG)


class UserNotFoundError(Exception):
    pass


class WeirdError(Exception):
    pass  # lol


@dataclass
class Client:
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter


@dataclass
class User:
    username: bytes  # Can names please be bytesings
    password: bytes
    bio: bytes
    permissions: set[bytes]
    options: set[bytes]
    clients: list[Client] = field(default_factory=list)
    queue: list[bytes] = field(default_factory=list)


@dataclass
class PermissionSet:
    permissions: set[bytes]
    anti_permissions: set[bytes]
    management_permissions: set[bytes]


@dataclass
class Role(PermissionSet):
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
    userRoles: dict[
        bytes, set[bytes]
    ]  # camel case because it looks more like haskell lol
    roles: dict[bytes, Role]
    channels: dict[bytes, Channel]


#    ... str? most of those should be bytes
# anything that will possibly get transmitted in the socket should be a bytes()

# time to rewrite everything below


users = {name: User(username=name, **user) for name, user in config.users.items()}
guilds = {name: Guild(name=name, **guild) for name, guild in config.guilds.items()}

clients: dict[
    bytes, Client
] = {}  # because server ops might want to transmit and receive CIDs
# your controls, semi-afk
# anyways, rewriting the below sounds slightly painful
client_id_count = 0

# put this in config.py
# guilds = {
#     "Hackers": {
#                    "users": ["luk3yx", "andrew", "hax"],
#                }
# }`
# name: {"users": [username],
#        "userRoles": {userName: set(roles)},
#        "rolePermissions": {roleName: [set(permissions), set(antiPermission), set(managementPermissions), {channelName: [...]}]},
#        "channels" : {channelName: {}},
#       }


def getKeyByValue(d, s):
    r = []
    for k, v in d.items():
        if s == v:
            r.append(k)
    return r


def getCidByWriter(writer):
    r = getKeyByValue(clients, writer)
    if len(r) > 1:
        raise WeirdError("Two CIDs have the same writer?")
    elif len(r) == 1:
        return r[0]
    else:
        raise WeirdError("Writer exists but doesn't have a CID?")


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
        users[username].queue.append(toWrite)
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
        newln = await reader.read(9)
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
                            await argWrite(writer, b"OFFLINE_MESSAGES\r\n")
                            for m in queue:
                                writer.write(m)
                            del m
                            users[loggedInAs].queue = []
                            await argWrite(writer, b"END_OFFLINE_MESSAGES\r\n")
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

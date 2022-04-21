#!/bin/sh
# Internet Delay Chat Server
# Example implementation in Python asyncio
#
# This implementation uses some parts of object-oriented Python, while trying
# to be uninstrusive such as not having two layers of subclassing.  When I
# learn how to actually write practical (as opposed to plainly theoretical and
# purely functional programs), this implementation won't be maintained by me
# anymore. -- Andrew
#
# The Internet Delay Chat specifications and implementations are all under
# heavy development.  No stability may be expected.
#
# This software likely contains critical bugs.
#
# Copyright (C) 2022  luk3yx <https://luk3yx.github.io>
# Copyright (C) 2022  Andrew Yu <https://www.andrewyu.org>
# Copyright (C) 2022  Test_User <https://users.andrewyu.org/~hax>
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

logging.basicConfig(level=logging.DEBUG)


class UserNotFoundError(Exception):
    pass


class StrangeError(Exception):
    pass


class Client:
    client_accumulation = 0

    def __init__(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        Client.client_accumulation += 1
        self.reader: asyncio.StreamReader = reader
        self.writer: asyncio.StreamWriter = writer
        self.clientId: bytes = str(Client.client_accumulation).encode("utf-8")
        # self.user won't be defined here, unless we decide to make a nullUser of some sort

    async def writeRaw(self, toWrite: bytes) -> None:
        self.writer.write(toWrite)
        await self.writer.drain()

    async def writeArgs(self, *toWrite: list[bytes]) -> None:
        line: bytes = (
            b"\t".join(
                arg.replace(b"\\", b"\\\\").replace(b"\t", b"\\\t") for arg in args
            )
            + b"\r\n"
        )
        await self.writeRaw(line)


class User:
    def __init__(self, username: bytes, userConfiguration):
        self.username: bytes = username
        self.password: bytes = userConfiguration.password
        self.bio: bytes = userConfiguration.bio
        self.permissions: set[bytes] = userConfiguration.serverPermissions
        self.options: set[bytes] = userConfiguration.serverOptions
        # I'm unclear what would happen if the below lists are empty.  Having
        # an empty clientlist and queue is pretty normal.
        self.clients: list[Client] = []
        self.queue: list[bytes] = []
    def addClient(self, client: Client):
        self.clients.append(client)
    def delClient(self, client: Client):
        self.clients.remove(client)
    async def writeArgsToAllClients(self, delayable: bool, *toWrite: bytes) -> int:
        if self.clients:
            i: int = 0
            for client in self.clients:
                await client.writeArgs(*toWrite)
                i += 1
            return i
        elif "offline-messages" in self.options:
            self.queue.append(toWrite)
            return 0
        else:
            raise MessageUndeliverableError("User offline and does not accept offline messages")


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
        for clientId in users[username].clients:
            writer = clients[clientId]
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
    clientId = str(client_id_count)
    client_id_count += 1
    clients[clientId] = writer
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

        logging.debug(clientId + " >>> " + repr(args))
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
                        users[loggedInAs].clients.append(clientId)
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
        users[loggedInAs].clients.remove(clientId)
    except KeyError:
        pass
    del clients[clientId]


async def main():
    server = await asyncio.start_server(clientLoop, "", 1025)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())

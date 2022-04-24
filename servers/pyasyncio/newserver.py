#!/usr/bin/env python3
#
# Internet Delay Chat Server
# Example implementation in Python asyncio
#
# This implementation uses some parts of object-oriented Python, while
# trying # to be uninstrusive such as not having two layers of
# subclassing.  When I # learn how to actually write practical (as
# opposed to plainly theoretical and # purely functional programs),
# this implementation won't be maintained by me anymore. -- Andrew
#
# The Internet Delay Chat specifications and implementations are all
# under heavy development.  No stability may be expected.
#
# This program uses new Python type annotations.  After making an edit,
# you should use MyPy to check if the types are good.
#
# This software likely contains critical bugs.  Do not use it for
# production as with any other experimental software.
#
# By: luk3yx <https://luk3yx.github.io>
#     Andrew Yu <https://www.andrewyu.org>
#     Test_User <https://users.andrewyu.org/~hax>
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
# Todo list:
# - Guilds and channels
# - Use sources correctly, i.e. :andrew@andrewyu.org
# - Presence list
# - Federation, and usernames should contain the server name somehow
# - TLS
# - VOIP
# - Moderation
# - MAKE A CLIENT!
#
# Note that this program only runs properly on Python 3.9 and later.
# This program heavily utilizes dataclasses so that the object-oriented
# nature of Python may be utilized in a less harmful way; annotations
# are used for static typechecking and will cause SyntaxErrors and
# IndexErrors on older version that do not understand annotations.

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TypeVar

import time  # for timestamps in messages
import asyncio
import logging
import secrets  # handles password-elated stuff

import config

# config.py, which should be where you put this program
# an example configuration may be created soon

logging.basicConfig(level=logging.DEBUG)

# Some global dictionaries to store state

users: dict[bytes, User] = {}

clients: dict[bytes, Client] = {}
client_id_count = 0  # replace with len(clients.keys())

guilds: dict[bytes, Guild] = {}


# Custom exceptions


class StrangeError(Exception):
    """
    Random errors that shouldn't exist and were probably caused by
    either the hardware blowing up or huge bugs.
    """

    pass


class MessageUndeliverableError(Exception):
    """
    User to deliver message to is offline and doesn't have the
    offline-messages option.
    """

    pass


class UserNotFoundError(MessageUndeliverableError):
    """
    Trying to message, modify, or otherwise interact with a nonexistant
    user.
    """

    pass


class RickRollError(BaseException):
    """
    Raise this when luk3yx rickrolls.
    """

    def __str__(self) -> str:
        return """Never gonna give you up,
never gonna let you down,
never gonna run around and desert you!
"""


def timestamp() -> bytes:
    return str(time.time()).encode("utf-8")


def argsToBytes(*args: bytes) -> bytes:  # *args: bytes, or *args: list[bytes]
    """
    From the arguments given, escape each argument (mainly the
    backslashes and tabs), then join them with tabs.
    """
    return (
        b"\t".join(
            [arg.replace(b"\\", b"\\\\").replace(b"\t", b"\\\t") for arg in args]
        )
        + b"\r\n"
    )


def bytesToArgs(msg: bytes) -> list[bytes]:
    """
    Turns bytes, usually received from the socket, into arguments with
    a parser.  This code is very inefficent!
    """
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
    args.append(current)
    return args

    # args = re.sub(r"\\(.)|\t", lambda m: m.group(1) or "\udeff",\
    #    msg).split(
    #    "\udeff"
    # )
    # Bad because: (1) This is a hack, it looks dirty;
    #              (2) It wants things to be decoded.


class Server:
    """
    Stub class for server linkage.
    """

    pass


class Client:
    client_accumulation = 0  # We might replace this with len(clients)

    def __init__(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        Client.client_accumulation += 1
        self.reader: asyncio.StreamReader = reader
        self.writer: asyncio.StreamWriter = writer
        self.clientId: bytes = str(Client.client_accumulation).encode("utf-8")
        # self.user won't be defined here, unless we decide to make a
        # nullUser of some sort; setting it to None would cause type
        # problems with annotations and MyPy.
        # Do note that a client MUST belong to a user for actual usage,
        # otherwise there's not much that the client can do.

    async def writeRaw(self, toWrite: bytes) -> None:
        self.writer.write(toWrite)
        await self.writer.drain()

    async def writeArgs(self, *toWrite: bytes) -> None:
        await self.writeRaw(argsToBytes(*toWrite))


@dataclass
class User:
    username: bytes
    password: bytes
    bio: bytes
    permissions: set[bytes]
    options: set[bytes]
    clients: list[Client] = field(default_factory=list)
    queue: list[bytes] = field(default_factory=list)

    # It might be possible to rewrite this as a property()

    def addClient(self, client: Client) -> list[Client]:
        self.clients.append(client)
        return self.clients

    def delClient(self, client: Client) -> list[Client]:
        self.clients.remove(client)
        return self.clients

    async def writeArgsToAllClients(self, delayable: bool, *toWrite: bytes) -> int:
        if self.clients:
            i: int = 0
            for client in self.clients:
                await client.writeArgs(*toWrite)
                i += 1
            return i
        elif not delayable:
            raise MessageUndeliverableError("User offline and message is not delayable")
        elif b"offline-messages" in self.options:
            self.queue.append(argsToBytes(*toWrite))
            return 0
        else:
            raise MessageUndeliverableError(
                "User offline and does not accept offline messages"
            )


@dataclass
class _PermissionSet:
    permissions: set[bytes]
    anti_permissions: set[bytes]
    management_permissions: set[bytes]


@dataclass
class Role(_PermissionSet):
    name: bytes
    channel_overrides: dict[bytes, _PermissionSet]


@dataclass
class Channel:
    name: bytes
    users: list[User]


@dataclass
class Guild:
    name: bytes
    description: bytes
    users: list[User]
    userRoles: dict[User, set[Role]]
    roles: dict[bytes, Role]
    channels: dict[bytes, Channel]
    # The guild MUST be added to the guilds dictionary on creation, but
    # should we do it here?
    # this is a question for you :)
    # How often do you create guilds? 
    #  I 'm not sure how this matters, but probably not very often; we
    # definitely do want a way to create guilds during runtime, because
    # not al!l users have ac!ces to the configuration file and using realod()
    # is bad practice 


# this is quite generic...
# this is haskell syntax, is this possible?
T = TypeVar('T')  # from typing import TypeVar
U = TypeVar('U')
def getKeyByValue(d: dict[T, U], s: U) -> list[T]:
    r = []
    for k, v in d.items():
        if s == v:
            r.append(k)
    return r


# Don't delete this yet, we haven't put it in User/Client yet
# async def checkedTimedOriginedMessageToUser(
#     originUsername, targetUsername, command, text
# ):
#     if targetUsername in users:
#         return await users[targetUsername].writeArgsToAllClients(
#             b":" + originUsername,
#             command,
#             str(time.time()).encode("utf-8"),
#             text,
#         )
#     else:
#         return UserNotFoundError("User nonexistant")


# what are the classes for this again
async def clientLoop(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    # addr = writer.get_extra_info("peername")
    # maybe use this for login allowmask checking?
    global client_id_count
    clientId = str(client_id_count).encode("utf-8")
    client_id_count += 1
    clients[clientId] = writer
    loggedIn = False
    loggedInAs = None
    ln = b""
    while True:
        newln = await reader.read(4096)
        if newln == b"":
            break
        ln += newln
        lnSplt = ln.split(b"\r\n")
        if len(lnSplt) < 2:
            continue
        msg = lnSplt[0]
        ln = b""

        args = bytesToArgs(msg)

        if not args[0]:
            continue

        logging.debug(clientId.decode("utf-8") + " >>> " + repr(args))
        cmd = args[0].upper()

        if cmd == b"SERVER":
            await argWrite(
                writer,
                b"ERR_NOT_IMPLEMENTED",
                b"Server linkage is unimplemented.  Please submit a patch to idc@andrewyu.org; this is a crucial feature.",
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
                    b"ERR_ARGUMENT_NUMBER",
                    b"The USER command takes two positional arguments: Username and password.",
                )
            else:
                try:
                    goodPassword = users[args[1]].password
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
                        # users[loggedInAs].clients.append(Client())
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
        elif cmd == b"PING":
            await argWrite(writer, b"PONG", *args[1:])
        elif cmd == b"PRIVMSG":
            if len(args) != 3:
                await argWrite(
                    writer,
                    b"ERR_ARGUMENT_NUMBER",
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
            if "kill" not in users[loggedInAs].permissions:
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


async def main() -> None:
    server = await asyncio.start_server(clientLoop, "", 1025)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    import subprocess

    if subprocess.call(("mypy", __file__)) == 0:
        asyncio.run(main())

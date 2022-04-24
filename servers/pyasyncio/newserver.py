#!/usr/bin/env python3
#
# Internet Delay Chat Server
# Example implementation in Python asyncio
#
# This implementation uses some parts of object-oriented Python, while
# trying # to be uninstrusive such as not having two layers of
# subclassing.  When I # learn how to actually write practical (as
# opposed to plainly theoretical and purely functional programs),
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
# Please please report problems to <idc@andrewyu.org>.

# By: luk3yx <https://luk3yx.github.io>
#     Andrew Yu <https://www.andrewyu.org>
#     Test_User <https://users.andrewyu.org/~hax>

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

# Todo list:
# - New message format
# - Guilds and channels
# - Use sources correctly, i.e. :andrew@andrewyu.org
# - Presence list
# - Federation, and usernames should contain the server name somehow
# - TLS
# - VOIP
# - Moderation
# - MAKE A CLIENT!

# Variables whose values are transmitted in sockets and connections
# should usually be a bytes object, rather than a string.  If we decode
# and re-encode everything, users wouldn't be able to do stuff like
# send binary files, which is a unwanted limitation.

# -------------------------------------------------------------------- #
#                              Typing                                  #
# -------------------------------------------------------------------- #

# Note that this program only runs properly on Python 3.9 and later.
# This program heavily utilizes dataclasses so that the object-oriented
# nature of Python may be utilized in a less harmful way; annotations
# are used for static typechecking and will cause SyntaxErrors and
# IndexErrors on older version that do not understand annotations.
# It is recommended to pass the --strict option to mypy while doing
# typechecks.  The following are the imports for typechecking.
# Whenever you see things of form variable: type = something or
# variable: containerType[type ...] = something, those are type
# signatures.
from __future__ import annotations
from dataclasses import dataclass, field
from typing import TypeVar

# -------------------------------------------------------------------- #
#                             Imports                                  #
# -------------------------------------------------------------------- #


# These are general imports...
import time  # Most messages have timestamps
import re  # Regular expressions might be used for parsing
import asyncio  # Handles the most basic things
import logging  # Need to dig into more fancy logging options (colors?)
import secrets  # handles password-elated stuff

# The configuration file for this program is written in Python itself,
# and is imported as a library.  This allows for extreme flexibility.
# However, as a complication, I haven't figured out a good way to
# "rehash" the configuration file when it is updated.  Reload from
# importlib might work, but it is unclear how importlib affects
# scopes and coroutines that are already using the configuration.
# Currently, just use the public configuration; a better-documented
# reference configuration may be created, but that's a low priority for
# now.  Another problem is, we don't know how to write configuration
# from within the program.  I recall seeing dynamic Python configs
# somewhere, but I don't remember where that is, please tell me if you
# find one.
import config

# General rules for logging:
# Raw I/O lines go into DEBUG
# Things like joinquits should go to INFO
# Not sure if we need WARN/ERROR/etc, but maybe do so on unexpected
# exceptions (such as StrangeError, as opposed to errors that arise
# in normal usage such as UserNotFoundError).
logging.basicConfig(level=logging.DEBUG)

# -------------------------------------------------------------------- #
#                           Global State                               #
# -------------------------------------------------------------------- #

# Global dictionaries to store state.
# The bytes objects below all have their respective names as keys.
clients: dict[bytes, Client] = {}
users: dict[bytes, User] = {}
guilds: dict[bytes, Guild] = {}

# client_id_count = 0  # replace with len(clients.keys())

# -------------------------------------------------------------------- #
#                            Exceptions                                #
# -------------------------------------------------------------------- #

# The following are exceptions specific to our server.  Many of them
# should be caught---we don't want the server to crash just because
# a user tried to send a message to a nonexistant user.
# We still raise exceptions, because many of those problems are detected
# in more "internal" stages in the program, such as internal command-
# handling functions.  Checking them before calling seems like putting
# the checks in the wrong place.


class ParserError(Exception):
    """
    Something happened during parsing!
    """

    pass


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
    Raise this for clients trying to message, modify, or otherwise
    interact with a nonexistant user.
    """

    pass


# -------------------------------------------------------------------- #
#                            Utilities                                 #
# -------------------------------------------------------------------- #

T = TypeVar("T")
U = TypeVar("U")

# I'm a little afraid here that the first time this function is called
# T and U will be fixed types for the rest of the program.  Hopefully
# not.


def getKeyByValue(d: dict[T, U], s: U) -> list[T]:
    """
    Simple dictioary keys, knowing its value.
    """
    r = []
    for k, v in d.items():
        if s == v:
            r.append(k)
    return r


def timestamp() -> bytes:
    """
    This simply returns a floating-point timestamp in bytes.
    """
    return str(time.time()).encode("utf-8")


_esc_re = re.compile(rb"\\(.)")
_idc_escapes = {b"\\": b"\\\\", b"r": b"\r", b"n": b"\n", b"t": b"\t"}


def bytesToArgs(msg: bytes) -> tuple[bytes, dict[bytes, bytes]]:
    """
    Parses a raw IDC message into the command and arguments.
    Example: PRIVMSG TARGET:yay MESSAGE:Hi
    (b'PRIVMSG', {b'TARGET': b'yay', b'MESSAGE': b'Hi'})
    """
    # I'm pretty sure that this is one of luk3yx's hacks as it contains
    # some byte sequences that I just can't understand.
    cmd = b""
    args = {}
    for arg in msg.split(b"\t"):
        if b":" in arg:
            key, value = arg.split(b":", 1)
            args[key] = _esc_re.sub(
                lambda m: _idc_escapes.get(m.group(1), b"\xef\xbf\xbd"), value
            )
        else:
            if not cmd:
                cmd = arg
            else:
                raise ParserError("Two commands in one message")
    return cmd, args


def argsToBytes(cmd: bytes, **args: dict[bytes:bytes]) -> bytes:
    """
    From the arguments given, escape each argument (mainly the
    backslashes and tabs), then join them with tabs.
    """
    # TODO: This was written for the old positional protocol; the new
    # key and value protocol needs a rewrite of this function.
    return b"stub TODO TODO TODO at def argsToBytes"


# -------------------------------------------------------------------- #
#                            Classes                                   #
# -------------------------------------------------------------------- #


class Server:
    """
    Stub class for server linkage.
    """

    pass


@dataclass
class Client:
    """
    The Client class is an object related to each connection, or called
    client.
    """

    clientId: bytes = str(len(clients) + 1).encode("utf-8")
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    user: User

    def __init__(self) -> None:
        """
        Nothing fancy, just puts itself into the global state.
        """
        clients[self.clientId] = self
        # WARNING!  Importatn!  TODO!
        # Should we be adding the client to the clients dictionary right
        # here, or should we do that in clientLoop?
        # If we put it in clientLoop, make sure that it does so quick
        # enough, because if new clients are spawned before the old one
        # adds itself to the clients dictionary, you would have client
        # ID collisions, which can cause undefined behavior!

    def __del__(self) -> None:
        # TODO
        """
        Stub function, what do we do when a client disconnects?
        (1) Remove it from the clients list
        (2) Remove it from its user's client list (TODO)
        """
        del clients[self.clientId]
        del self.user.clients[self.clientId]

    async def writeRaw(self, toWrite: bytes) -> None:
        """
        Write some stuff to the client.
        """
        self.writer.write(toWrite)
        await self.writer.drain()

    async def writeArgs(self, *toWrite: bytes) -> None:
        # This is one of the writeArgs things that needs to use
        # keywords insteade of argpos.  <<TODO>>
        """
        Write arguments to the client.
        """
        await self.writeRaw(argsToBytes(*toWrite))

    # I don't think we should put the client's mainloop into this class
    # as it's not strictly an attribute of the client.


@dataclass
class User:
    """
    There exists a User() object for each entity using this IDC server,
    and possibly the same class for federated servers with some
    if statements.
    Users differ from clients because users usually represent people or
    bots, while clients refer to specific connections.
    """

    username: bytes
    password: bytes
    bio: bytes
    permissions: set[bytes]
    options: set[bytes]
    clients: list[Client] = field(default_factory=list)
    queue: list[bytes] = field(default_factory=list)

    # It might be possible to rewrite this as a property(), but that's
    # not strictly necessary.  I'm also unsure if property() works like
    # that for remotely appending things into lists?

    # The addClient and delClient methods should be called by the
    # respective client's mainloop.  These two functions only register
    # the client on a user; it doesn't modify the client connection
    # itself.  Particularly, it doesn't destroy connections when
    # delClient is called.

    def addClient(self, client: Client) -> list[Client]:
        """
        Adds a client to the user
        """
        self.clients.append(client)
        return self.clients

    def delClient(self, client: Client) -> list[Client]:
        """
        Removes a client from the user
        """
        self.clients.remove(client)
        return self.clients

    async def writeArgsToAllClients(self, delayable: bool, *toWrite: bytes) -> int:
        # This is one of the writeArgs things that needs to use
        # keywords insteade of argpos.  <<TODO>>
        if self.clients:
            i: int = 0
            for client in self.clients:
                await client.writeArgs(*toWrite)
                # This is one of the writeArgs things that needs to use
                # keywords insteade of argpos.  <<TODO>>
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
    """
    A permission set is just a set of three types of permissions,
    read the whitepaper for details on how this should work.  Of course
    this is really complicated and is unimplemented.
    """

    permissions: set[bytes]
    antiPermissions: set[bytes]
    managementPermissions: set[bytes]


@dataclass
class Role(_PermissionSet):
    """
    A role is used in a Guild and designates a user's permission set
    there.  Each channel may have override permissions.
    """

    name: bytes
    channelOverrides: dict[Channel, _PermissionSet]


@dataclass
class Channel:
    """
    Channels belong to Guilds and are specific ... well ... channels.
    """

    name: bytes
    users: list[User]

    async def writeArgsToAllUsers(self, delayable: bool, **args: []) -> None:
        # This is one of the writeArgs things that needs to use
        # keywords insteade of argpos.  <<TODO>>
        pass


@dataclass
class Guild:
    """
    Treat Guilds as namespaces on Libera (but it's actually integrated),
    or communities/spaces on Matrix, or "Servers" on Discord (it's their
    terminology of using Guilds in the API).
    """

    name: bytes
    description: bytes
    users: list[User]
    userRoles: dict[User, set[Role]]
    roles: dict[bytes, Role]
    channels: dict[bytes, Channel]
    # The guild MUST be added to the guilds dictionary on creation, but
    # should we do it here?
    # This is similar to "when do we put a Client() into clients{}?"
    # How often do you create guilds?
    # I'm not sure how this matters, but probably not very often; we
    # definitely do want a way to create guilds during runtime, because
    # not all users have access to the configuration file and using
    # reload crazily is bad and buggy
    # Also, a guild object should be created when the first user of that
    # guild comes online or something?  But that gets messey as we need
    # to track which Guilds a user is in in two places... also the bane
    # of object-oriented programming again.


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


# -------------------------------------------------------------------- #
#                         Client Main Loop                             #
# -------------------------------------------------------------------- #
async def clientLoop(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter
) -> None:
    """
    This coroutine witnesses clients from their connection to their
    death.
    """
    addr = writer.get_extra_info("peername")
    global client_id_count
    clientId = str(client_id_count).encode("utf-8")
    client_id_count += 1
    client = Client
    clients[clientId] = client
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

        cmd, args = bytesToArgs(msg)

        if not cmd:
            continue

        logging.debug("%s >>> %r %r", clientId.decode("utf-8"), cmd, args)

        # Now that argWrite doesn't exist...

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
            if "USERNAME" not in args or "PASSWORD" not in args:
                await argWrite(
                    writer,
                    b"ERR_ARGUMENT_NUMBER",
                    b"The USER command takes two positional arguments: Username and password.",
                )
            else:
                try:
                    goodPassword = users[args["USERNAME"]].password
                except KeyError:
                    await argWrite(
                        writer,
                        b"ERR_LOGIN_INVALID",
                        b"The username provided is invalid.",
                    )
                else:
                    if secrets.compare_digest(args["PASSWORD"], goodPassword):
                        await argWrite(
                            writer,
                            b"RPL_LOGIN_GOOD",
                            b"You have logged in as " + args[1] + b".",
                        )
                        loggedInAs = args["USERNAME"]
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
        elif loggedInAs is None:
            await argWrite(writer, b"ERR_UNREGISTERED", b"You haven't logged in.")
        elif cmd == b"PING":
            await argWrite(writer, b"PONG", b"COOKIE:" + args["COOKIE"])
        elif cmd == b"PRIVMSG":
            if "TARGET" not in args or "MESSAGE" not in args:
                await argWrite(
                    writer,
                    b"ERR_ARGUMENT_NUMBER",
                    b"The PRIVMSG command takes two arguments: Target and MESSAGE.",
                )
            else:
                r = await checkedTimedOriginedMessageToUser(
                    loggedInAs, args["TARGET"], b"PRIVMSG", args["MESSAGE"]
                )
                if isinstance(r, UserNotFoundError):
                    await argWrite(
                        writer,
                        b"ERR_DESTINATION_NONEXISTANT",
                        b"The destination user " + args["TARGET"] + b" does not exist.",
                    )
                elif r is None:
                    await argWrite(
                        writer,
                        b"ERR_NO_OFFLINE_MSGS",
                        b""
                        + args["TARGET"]
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
            elif "VICTIM" not in args:
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
            if "GUILD" not in args:
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
    if loggedInAs is not None:
        try:
            # loggedInAs could be None at this point
            # Which won't make any actual difference but it upsets mypy
            # true, we need a nullUser
            # but wait, is loggedInAs a bytes or a User
            # bad, we should use User, and define a nullUser if mypy wants that
            # or use stuff from the typing module to make mypy happy
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

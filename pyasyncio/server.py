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

import time
import asyncio
import logging
import config

# from dataclasses import dataclass # nah not doing this for now

logging.basicConfig(level=logging.DEBUG)


class UserNotFoundError(Exception):
    pass


class WeirdError(Exception):
    pass


users = config.users
for username in users:
    users[username]["clients"] = []
    users[username]["queue"] = []
clients = {}  # cid: (reader, writer)
client_id_count = 0


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
    if users[username]["clients"]:
        i = 0
        for cid in users[username]["clients"]:
            writer = clients[cid]
            await argWrite(writer, *args)
            i += 1
        return i
    elif "offline-messages" in users[username]["options"]:
        users[username]["queue"].append(toWrite)
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
                    goodPassword = users[args[1]]["password"]
                except KeyError:
                    await argWrite(
                        writer,
                        b"ERR_LOGIN_INVALID",
                        b"The username provided is invalid.",
                    )
                else:
                    if args[2] == goodPassword:
                        await argWrite(
                            writer,
                            b"RPL_LOGIN_GOOD",
                            b"You have logged in as " + args[1] + b".",
                        )
                        loggedInAs = args[1]
                        loggedIn = True
                        users[loggedInAs]["clients"].append(cid)
                        queue = users[loggedInAs]["queue"]
                        if queue:
                            await argWrite(writer, b"OFFLINE_MESSAGES\r\n")
                            for m in queue:
                                writer.write(m)
                            del m
                            users[loggedInAs]["queue"] = []
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
        else:
            await argWrite(
                writer, b"ERR_UNKNOWN_COMMAND", cmd + b" is an unknown command."
            )

    writer.close()
    try:
        users[loggedInAs]["clients"].remove(cid)
    except KeyError:
        pass
    del clients[cid]


async def main():
    server = await asyncio.start_server(clientLoop, "", 1025)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())

import time
import asyncio
import config
from pprint import pprint

users = config.users
for username in users:
    users[username]["clients"] = []
    users[username]["queue"] = []
clients = {}  # cid: (reader, writer)
client_id_count = 0


async def sendToAllClientsOfUser(username, toWrite):
    if users[username]["clients"]:
        i = 0
        for pair in users[username]["clients"]:
            pair[1].write(toWrite)
            await pair[1].drain()
            i += 1
        return i
    else:
        if "offline-messages" in users[username]["options"]:
            users[username]["queue"].append(toWrite)
            return False
        return None

class UserNotFoundError(Exception): pass


async def checkedTimedOriginedMessageToUser(
    originUsername, targetUsername, command, text
):
    if targetUsername in users.keys() and originUsername in users.keys():
        return await sendToAllClientsOfUser(
            targetUsername,
            command
            + b"\t"
            + (str(time.time()).encode("utf-8"))
            + b"\t"
            + originUsername
            + b"\t"
            + text
            + b"\r\n",
        )
    else:
        return UserNotFoundError("User nonexistant")


async def clientLoop(reader, writer):
    addr = writer.get_extra_info("peername")
    global client_id_count
    cid = str(client_id_count)
    client_id_count += 1
    clients[cid] = (reader, writer)
    loggedIn = False
    loggedInAs = Exception
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

        print(args)

        if not args[0]:
            return
        cmd = args[0].upper()

        if cmd == b"SERVER":
            writer.write(b"ERR_NOT_IMPLEMENTED\tServer linkage is unimplemented.\r\n")
        elif cmd == b"HELP":
            writer.write(
                b"RTFS\tRead the freaking source code!  It's at git://git.andrewyu.org/internet-delay-chat.git.\r\n"
            )
        elif cmd == b"USER":
            if len(args) != 3:
                writer.write(
                    b"ERR_ARGUMEHT_NUMBER\tThe USER command takes two positional arguments: Username and password.\r\n"
                )
            else:
                try:
                    goodPassword = users[args[1]]["password"]
                except KeyError:
                    writer.write(
                        b"ERR_LOGIN_INVALID\tThe username provided is invalid.\r\n"
                    )
                else:
                    if args[2] == goodPassword:
                        writer.write(
                            b"RPL_LOGIN_GOOD\tYou have logged in as "
                            + args[1]
                            + b".\r\n"
                        )
                        loggedInAs = args[1]
                        loggedIn = True
                        users[loggedInAs]["clients"].append(cid)
                        queue = users[loggedInAs]["queue"]
                        if queue:
                            writer.write(b"BURST\r\n")
                            for m in queue:
                                writer.write(m)
                            del m
                            users[loggedInAs]["queue"] = []
                            writer.write(b"END_BURST\r\n")
                        del queue
                    else:
                        writer.write(
                            b"ERR_PASS_INVALID\tIncorrect password for "
                            + args[1]
                            + b".\r\n"
                        )
        elif cmd == b"DUMP":  # TODO: This is for debugging purposes, obviously
            writer.write(repr(clients).encode("utf-8"))
            writer.write(repr(users).encode("utf-8"))
        elif not loggedIn:
            writer.write(b"ERR_UNREGISTERED\tYou haven't logged in.\r\n")
        elif cmd == b"PRIVMSG":
            if len(args) != 3:
                writer.write(
                    b"ERR_ARGUMEHT_NUMBER\tThe PRIVMSG command takes two positional arguments: Username and text.\r\n"
                )
            else:
                r = await checkedTimedOriginedMessageToUser(loggedInAs, args[1], b"PRIVMSG", args[2])
                if isinstance(r, UserNotFoundError):
                    writer.write(
                        b"ERR_DESTINATION_NONEXISTANT\tThe destination user "
                        + args[1]
                        + b" does not exist.\r\n"
                    )
                elif r is None:
                    writer.write(b"ERR_NO_OFFLINE_MSGS\t" + args[1] + b"is offline and does not have offline-messages.\r\n")
                del r
        else:
            writer.write(
                b'ERR_UNKNOWN_COMMAND\t"' + cmd + b'" is an unknown command.\r\n'
            )

        await writer.drain()

    writer.close()
    try:
        users[loggedInAs]["clients"].remove(cid)
    except UnboundLocalError:
        pass
    del clients[cid]


async def main():
    server = await asyncio.start_server(clientLoop, "", 1025)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())

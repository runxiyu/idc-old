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
    for (reader, writer) in users[username]["clients"]:
        writer.write(toWrite)
        await writer.drain()

async def privateMessage(originUsername, targetUsername, text):
    sendToAllClientsOfUser(b"PRIVATE_MESSAGE\t" + originUsername + b"\t" + targetUsername + b"\t" + text)


async def clientLoop(reader, writer):
    addr = writer.get_extra_info("peername")
    global client_id_count
    cid = str(client_id_count)
    client_id_count += 1
    clients[cid] = (reader, writer)
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
                        users[loggedInAs]["clients"].append(cid)
                    else:
                        writer.write(
                            b"ERR_PASS_INVALID\tIncorrect password for "
                            + args[1]
                            + b".\r\n"
                        )
        elif cmd == b"DUMP":
            writer.write(repr(clients).encode("utf-8"))
            writer.write(repr(users).encode("utf-8"))
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
    server = await asyncio.start_server(clientLoop, "", 1026)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())

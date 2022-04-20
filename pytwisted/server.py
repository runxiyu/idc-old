"""
Example IDC server written in Python with Twisted (because we wanted this to be
quick and dirty)

run me with twistd -y chatserver.py, and then connect with multiple
clients to port 1025
"""

from twisted.protocols import basic
import random

with open("config.py", "r") as c:
    exec(c.read())


class User:
    def __init__(self, username):
        self.clients = []  # Client()
        self.in_channels = []  # Channel()

    def add_client(self, client):
        self.clients.append(client)

    def del_client(self, client):
        self.clients.remove(client)

    def send(self, *args):
        for client in self.clients:
            client.send(*args)

    def join(self, channel):
        channel.broadcast_join(self)
        self.channels.append(channel)

    def part(self, channel, reason=""):
        channel.broadcast_part(self, reason)
        self.channels.remove(channel)

    def message(self, target, message):
        pass


class Channel:
    def __init__(self, name):
        self.name = name
        self.users = []  # User()
        self.modes = []  # ("ban", "hax@andrewyu.org")

    def broadcast_join(self, user):  # must be called with User().join
        self.users.append(user)
        for u in self.users:
            u.send("JOIN", user.get_id(), seld.name)

    def broadcast_part(self, user, reason=""):  # must be called with User().part
        self.users.append(user)
        for u in self.users:
            u.send("PART", user.get_id(), seld.name, reason)


class Client(basic.LineReceiver):
    delimiter = b"\n"

    def connectionMade(self):
        r = lambda: random.choice(list("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
        while True:
            _ = r() + r() + r() + r() + r() + r()
            if _ not in self.factory.clients.keys():
                self.cid = _
                del _
                del r
                break
        self.factory.clients[self.cid] = self
        self.ready = False
        self.username = None

    def connectionLost(self, reason):
        del self.factory.clients[self.cid]
        del self  # del self? Won't this just do nothing?

    def lineReceived(self, line):
        print(repr(self.cid), repr(line))
        escaped = False
        args = []
        current = b""
        for b in [line[i : i + 1] for i in range(len(line))]:
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

        if not args[0]:
            return
        cmd = args[0].upper()

        print(cmd)

        if not self.ready:
            if cmd == b"PASSWORD":
                if len(args) < 2:
                    pass
                self.trying_password = args[1]
            elif cmd == b"USER":
                trying_user = config.users[args[1]]
                try:
                    if self.trying_password == trying_user["password"]:
                        self.username = args[1]
                        self.ready = True
                        self.send(
                            b"REPLY_LOGGED_IN",
                            b"You are now logged in as " + args[1] + b".",
                        )
                        if args[1] not in self.factory.users.keys():
                            self.factory.users[args[1]] = [self]
                        else:
                            self.factory.users[args[1]].append(self)
                    else:
                        self.send(
                            b"ERR_INVALID_CREDENTIALS",
                            b"The credentials you've entered are invalid.",
                        )
                except AttributeError:
                    self.send(b"ERR_NO_PASSWORD", b"You haven't provided a password.")
                    pass
            else:
                self.send(
                    b"ERR_NOT_LOGGED_IN",
                    b"You may not use this command before logging in.",
                )
        else:
            if cmd == b"MESSAGE" and len(args) == 3:
                self.send_msg(args[1], args[2])
                # why is it invaliding rather than passing
            elif cmd == b"PING":
                # miniirc_idc expects replies to PINGs
                self.send(b"PONG", args[-1])
            else:
                self.send(
                    b"ERR_INVALID_COMMAND",
                    b"The command you sent, " + cmd + b", is invalid.",
                )

    def quote(self, bytestring):
        try:
            self.transport.write(bytestring + b"\r\n")
        except:
            raise

    def send(self, *args):
        #buf = b""
        #for i in args:
        #    i = i.replace(b"\\", b"\\\\")
        #    i = i.replace(b"\t", b"\\\t")
        #    buf += i
        #    buf += b"\t"
        #self.quote(buf[:-1])
        self.quote(b'\t'.join(
            arg.replace(b'\\', b'\\\\').replace(b'\t', b'\\\t')
            for arg in args
        ))

    def send_msg(self, recipient, msg):
        if recipient not in config.users:
            self.send(
                b'ERR_I_AM_TOO_LAZY_TO_FIGURE_OUT_WHAT_CODE_TO_USE_HERE',
                b'User does not exist!',
            )
            return
        target_clients = self.factory.users.get(recipient)
        if not target_clients:
            # not [] == True
            self.send(b'ERR_USER_NOT_ONLINE', b'User is not online!')
            return
        for client in target_clients:
            # I have no idea what message format you want but this looks like
            # IRC so I'll do that
            client.send(b':' + self.username, b'MESSAGE', msg)


from twisted.internet import protocol
from twisted.application import service, internet

factory = protocol.ServerFactory()
factory.protocol = Client
factory.clients = {}  # cid: Client()
factory.channels = {}  # name: Channel()
factory.users = {}  # username: [Client()]

application = service.Application("chatserver")
internet.TCPServer(1025, factory).setServiceParent(application)

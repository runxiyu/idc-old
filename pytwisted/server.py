"""The most basic chat protocol possible.

run me with twistd -y chatserver.py, and then connect with multiple
clients to port 1025
"""

from twisted.protocols import basic
import random

with open("config.py", "r") as c:
    exec(c.read())


class MyChat(basic.LineReceiver):
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
        del self

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
                trying_user = config.users(args[1])
                try:
                    if self.trying_password == trying_user[password]:
                        self.username = args[1]
                        self.ready = True
                        self.send(
                            b"REPLY_LOGGED_IN", b"You are now logged in as " + args[1]
                        )
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

    def quote(self, bytestring):
        try:
            self.transport.write(bytestring + b"\r\n")
        except:
            raise

    def send(self, *args):
        buf = b""
        for i in args:
            i = i.replace(b"\\", b"\\\\")
            i = i.replace(b"\t", b"\\\t")
            buf += i
            buf += b"\t"
        self.quote(buf[:-1])


from twisted.internet import protocol
from twisted.application import service, internet

factory = protocol.ServerFactory()
factory.protocol = MyChat
factory.clients = {}
factory.channels = {}

application = service.Application("chatserver")
internet.TCPServer(1025, factory).setServiceParent(application)

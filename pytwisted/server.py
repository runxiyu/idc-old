"""The most basic chat protocol possible.

run me with twistd -y chatserver.py, and then connect with multiple
clients to port 1025
"""

from twisted.protocols import basic
import random
import config


class MyChat(basic.LineReceiver):
    delimiter = b"\n"
    def connectionMade(self):
        r = lambda: random.randchoice(list("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
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
        for b in line:
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
        self.send(bytes(repr(args)))

    def send(self, bytestring):
        try:
            self.transport.write(bytestring + b"\r\n")


from twisted.internet import protocol
from twisted.application import service, internet

factory = protocol.ServerFactory()
factory.protocol = MyChat
factory.clients = {}
factory.channels = {}

application = service.Application("chatserver")
internet.TCPServer(1025, factory).setServiceParent(application)

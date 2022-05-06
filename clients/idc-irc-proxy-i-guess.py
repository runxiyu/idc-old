#!/usr/bin/env python3
#
# miniirc bouncer thing
#
# © 2022 by luk3yx
#

import miniirc, socket, threading, miniirc_idc
from miniirc_extras.utils import ircv2_message_unparser, ircv3_message_parser

# A single network
class Network:
    _buffer  = b''
    IRC      = miniirc_idc.IDC
    encoding = 'utf-8'
    _001     = False

    _main_lock     = False
    block_incoming = frozenset(('PING', 'CAP', 'AUTHENTICATE'))
    block_outgoing = frozenset(('CAP',))

    # :( what socket is this even

    # Send messages
    def send(self, cmd, hostmask, tags, args):
        raw = ircv2_message_unparser(cmd, hostmask or (cmd, cmd, cmd), tags,
            args, colon=False, encoding=self.encoding)
        self.sock.sendall(raw[:510] + b'\r\n')

    # Receive messages
    def recv(self):
        while True:
            while b'\n' not in self._buffer:
                buf = self.sock.recv(4096)
                assert buf, 'The socket has been closed!'
                self._buffer += buf.replace(b'\r', b'\n')

            msg, self._buffer = self._buffer.split(b'\n', 1)
            msg = msg.decode(self.encoding, 'replace')
            if msg:
                cmd, _, tags, args = ircv3_message_parser(msg, colon=False)
                return tags, cmd.upper(), args

    # Handle everything
    def _miniirc_handler(self, irc, cmd, hostmask, tags, args):
        if cmd.startswith('IRCV3 ') or cmd in self.block_incoming:
            return
        elif cmd == '001':
            if self._001:
                return

            self._001 = True

            # Clear the SendQ
            if self._sendq:
                while len(self._sendq) > 0:
                    self._sendcmd(*self._sendq.pop(0))

            # Start the main loop
            self._main()
        elif cmd == 'ERROR':
            self.send('PING', None, {}, [':ERROR'])
        elif cmd == 'PONG' and args and args[-1] == 'miniirc-ping':
            return

        # Send the command to the client
        try:
            self.send(cmd, hostmask, tags, args)
        except Exception as e:
            print(repr(e))
            self.irc.disconnect('Connection closed.', auto_reconnect=False)

    # The initial main loop
    def _init_thread(self):
        self._sendq = []
        nick  = None
        user  = None

        # Wait for NICK and USER to be sent
        while not nick or not user:
            tags, cmd, args = self.recv()
            if cmd == 'NICK' and len(args) == 1:
                nick = args[0]
            elif cmd == 'USER' and len(args) > 1:
                user = args
            else:
                self._sendq.append((tags, cmd, args))

        # Set values
        self.irc.nick = nick
        self.irc.ident = user[0]
        self.irc.realname = user[-1]

        # Connect
        self.irc.connect()

    # Send a command
    def _sendcmd(self, tags, cmd, args):
        if cmd not in self.block_outgoing:
            raw = ircv2_message_unparser(cmd, (cmd, cmd, cmd), {}, args,
                colon=False, encoding=None)
            self.irc.quote(raw, tags=tags)

    # The more permanent main loop
    def _main(self, single_thread=False):
        if not single_thread:
            if self._main_lock and self._main_lock.is_alive():
                return self._main_lock

            t = threading.Thread(target=self._main, args=(True,))
            t.start()
            return t

        # Clear the RecvQ
        if self._recvq:
            while len(self._recvq) > 0:
                self.send(*self._recvq.pop(0))
            self._recvq = None

        # Send everything to IRC
        while True:
            try:
                tags, cmd, args = self.recv()
            except Exception as e:
                print(repr(e))
                return self.irc.disconnect()

            self._sendcmd(tags, cmd, args)

    # Generic init function
    def _init(self, conn, irc):
        # self.sock is the socket returned by sock.accept()
        # It's the socket it uses to talk to WeeChat
        # This bouncer was made for IRC-to-IRC so there isn't
        # anything IDC-specific here (except for changing it to use IDC()
        # instead of IRC())
        self.sock, self.ip = conn
        self.irc = irc

        # Add the IRC handler
        self._recvq = []
        self.irc.CmdHandler(ircv3=True, colon=False)(self._miniirc_handler)

        # Start the main loop
        threading.Thread(target=self._init_thread).start()

    # Create the IRC object
    def __init__(self, conn, *args, bad_cmds=None, **kwargs):
        if bad_cmds is not None:
            self.bad_cmds = bad_cmds
        self._init(conn, self.IRC(*args, auto_connect=False, **kwargs))

# The bouncer class
class Bouncer:
    addr = ('127.0.0.1', 1025)
    Network = Network

    # Main loop
    def main(self):
        # Create a socket object
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(self.addr)
            sock.listen(1)
            self.Network(sock.accept(), *self.args, **self.kwargs)

    # The main init
    def __init__(self, *args, **kwargs):
        self.args, self.kwargs = args, kwargs
        self.main()

# Debugging
def main():
    return Bouncer('127.0.0.1', 6835, 'luk3yx', debug=True, ns_identity='luk3yx billy')

if __name__ == '__main__':
    main()

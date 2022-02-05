#!/usr/bin/env python3

"""
Very simple reference implementation of an IDC server in Python.
Written in an object-oriented style because that's the best way to
do it in Python, imperative and functional implementations welcome.

Copyright (C) 2022  Andrew Yu <andrew@andrewyu.org>
Copyright (C) 2022  Test_User <hax@andrewyu.org>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from __future__ import annotations
import threading
import socket
import time
import ssl
import sys
import pickle
from misc import *

servers = []
clients = []

listen_port = int(sys.argv[1])


class Connection:
    def __init__(self, c, ca):
        self.c = c
        self.ca = ca
        self.user_modes = list[str]
        self.in_channels = list[str]

    def send(self, m):
        self.c.send(t_b(m + "\r\n"))

    def recv(self):
        return t_s(self.c.recv(1024))

    def close(self):
        self.c.close()

    def handle(self, m):
        if m[-1] == "\n": m = m[0:-1]
        p = parse2(m)
        cmd = p[0]
        nuh = p[1]
        arg = p[2]
        if cmd == "USER":
            
        self.send(str(p))

    def wait(self):
        if not d:
            o.close()


def connectionHandler(c, ca):
    o = Connection(c, ca)
    while True:
        d = o.recv()
        if not d:
            break
        o.handle(d)


def main():
    with socket.socket() as listening_sock:
        listening_sock.bind(("", listen_port))
        listening_sock.listen()
        while True:
            cs, ca = listening_sock.accept()
            threading.Thread(
                target=connectionHandler,
                args=(
                    cs,
                    ca,
                ),
                daemon=True,
            ).start()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

"""
Simple utilities for IDC
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

import re


def t_b(s):
    return s.encode("utf-8")


def t_s(b):
    return b.decode()


# Adapted from miniirc by luk3yx (MIT License)
def parse(msg):
    n = msg.split(" ")

    if n[0].startswith(":"):
        while len(n) < 2:
            n.append("")
        hostmask = n[0][1:].split("!", 1)
        if len(hostmask) < 2:
            hostmask.append("")
        i = hostmask[1].split("@", 1)
        if len(i) < 2:
            i.append("")
        hostmask = (hostmask[0], i[0], i[1])
        cmd = n[1]
    else:
        cmd = n[0]
        hostmask = ("","","")
        n.insert(0, "")

    args = []
    c = 1
    for i in n[2:]:
        c += 1
        if i.startswith(":"):
            args.append((" ".join(n[c:]))[1:])
            break
        else:
            args.append(i)

    return cmd, hostmask, args

IRCMessage = collections.namedtuple('IRCMessage', 'command hostmask tags args')
_msg_re = re.compile(
    r'^'
    r'(?:@([^ ]+) )?'
    r'(?::([^!@ ]*)(?:!([^@ ]*))?(?:@([^ ]*))? )?'
    r'([^ ]+)(?: (.*?)(?: :(.*))?)?'
    r'$'
)

def parse2(msg):
    match = _msg_re.match(msg)
    if not match:
        return

    raw_tags = match.group(1)
    tags = _tag_list_to_dict(raw_tags.split(';')) if raw_tags else {}

    hostmask = (match.group(2) or '', match.group(3) or '',
                match.group(4) or '')
    cmd = match.group(5)

    raw_args = match.group(6)
    args = [] if raw_args is None else raw_args.split(' ')

    trailing = match.group(7)
    if trailing:
        args.append(trailing)

    return IRCMessage(cmd.upper(), hostmask, tags, args)

#!/usr/bin/env python3
#
# This is very horrible and quickly written
# But it works
# You need to specify that this program is covered under the LICENSE file in this exact file
#
# Copyright © 2022 by luk3yx
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from __future__ import annotations
from collections.abc import Iterator, Mapping, Sequence
from typing import Optional
import datetime, miniirc, re  # type: ignore
assert miniirc.ver >= (1,8,1)


_LEADING_COLON = '' if miniirc.ver[0] > 2 else ':'
_esc_re = re.compile(r'\\(.)')

# Backslash must be first
_idc_escapes = {'\\': '\\', 'r': '\r', 'n': '\n', 't': '\t'}


def _get_idc_args(command: str, kwargs: Mapping[str, Optional[str | float]]
                  ) -> Iterator[str]:
    yield command
    for key, value in kwargs.items():
        if value is not None:
            value = str(value)
            for escape_char, char in _idc_escapes.items():
                value = value.replace(char, '\\' + escape_char)
            yield f'{key.upper()}={value}'


class IDC(miniirc.IRC):
    def idc_message_parser(
        self, msg: str
    ) -> Optional[tuple[str, tuple[str, str, str], dict[str, str], list[str]]]:
        idc_cmd = None
        idc_args = {}
        for arg in msg.split('\t'):
            if '=' in arg:
                key, value = arg.split('=', 1)
                idc_args[key] = _esc_re.sub(
                    lambda m: _idc_escapes.get(m.group(1), '\ufffd'),
                    value
                )
            else:
                idc_cmd = arg

        # Translate IDC keyword arguments into IRC positional ones
        if idc_cmd == 'PRIVMSG':
            msg = idc_args['MESSAGE']
            command = 'PRIVMSG'
            msg_type = idc_args.get('TYPE')
            if msg_type == 'NOTICE':
                command = 'NOTICE'
            elif msg_type == 'ACTION':
                msg = f'\x01ACTION {msg}\x01'
            args = [self.current_nick, msg]
        elif idc_cmd == 'CHANMSG':
            command = 'PRIVMSG'
            args = [idc_args['CHAN'], idc_args['MESSAGE']]
        elif idc_cmd == 'LOGIN_GOOD':
            command = '001'
            args = [self.current_nick, f'Welcome to IDC {self.current_nick}']
        elif idc_cmd == 'PONG':
            command = 'PONG'
            args = [idc_args.get('COOKIE', '')]
        else:
            return None

        # Add generic parameters
        tags = {}
        if 'SOURCE' in idc_args:
            user = idc_args['SOURCE']
            hostmask = (user, user, user)
            tags['account'] = user
        else:
            hostmask = ('', '', '')

        # If echo-message wasn't requested then don't send self messages
        if (command == 'PRIVMSG' and hostmask[0] == self.current_nick and
                'echo-message' not in self.active_caps):
            return None

        if 'TS' in idc_args:
            dt = datetime.datetime.utcfromtimestamp(float(idc_args['TS']))
            tags['time'] = dt.isoformat() + 'Z'

        if 'LABEL' in idc_args:
            tags['label'] = idc_args['LABEL']

        if args and _LEADING_COLON:
            args[-1] = _LEADING_COLON + args[-1]
        return command, hostmask, tags, args

    # Send raw messages
    def idc_send(self, command: str, **kwargs: Optional[str | float]):
        super().quote('\t'.join(_get_idc_args(command, kwargs)), force=True)

    def quote(self, *msg: str, force: Optional[bool] = None,
              tags: Optional[Mapping[str, str | bool]] = None) -> None:
        cmd, _, tags2, args = miniirc.ircv3_message_parser(' '.join(msg))
        if miniirc.ver[0] < 2 and args and args[-1].startswith(':'):
            args[-1] = args[-1][1:]
        self.send(cmd, *args, force=force, tags=tags or tags2)

    def _get_idc_account(self) -> Sequence[str]:
        if isinstance(self.ns_identity, tuple):
            return self.ns_identity
        else:
            return self.ns_identity.split(' ', 1)

    @property
    def current_nick(self) -> str:
        return self._get_idc_account()[0]

    def send(self, cmd: str, *args: str, force: Optional[bool] = None,
             tags: Optional[Mapping[str, str | bool]] = None) -> None:
        cmd = cmd.upper()
        label = tags.get('label') if tags else None
        if cmd in ('PRIVMSG', 'NOTICE'):
            target = args[0]
            # TODO: Make miniirc think that SASL worked PMs to NickServ don't
            # have to be blocked.
            if target == 'NickServ':
                return

            msg = args[1]
            msg_type: Optional[str]
            if cmd == 'NOTICE':
                msg_type = 'NOTICE'
            elif msg.startswith('\x01ACTION'):
                msg = msg[8:].rstrip('\x01')
                msg_type = 'ACTION'
            else:
                msg_type = None

            self.idc_send('CHANMSG' if target.startswith('#') else 'PRIVMSG',
                          target=target, type=msg_type, message=msg,
                          label=label)
        elif cmd == 'PING':
            self.idc_send('PING', cookie=args[0], label=label)
        elif cmd == 'USER':
            user, password = self._get_idc_account()
            self.idc_send('LOGIN', username=user, password=password,
                          label=label)
            self.active_caps = self.ircv3_caps & {
                'account-tag', 'echo-message', 'labeled-response',
            }

    # Override the message parser to change the default parser.
    def change_parser(self, parser=None):
        super().change_parser(parser or self.idc_message_parser)

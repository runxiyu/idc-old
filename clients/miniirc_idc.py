#!/usr/bin/env python3
#
# This is very horrible and quickly written
# But it works
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
import datetime, miniirc, re, traceback  # type: ignore

assert miniirc.ver >= (1, 8, 1)


_LEADING_COLON = "" if miniirc.ver[0] > 2 else ":"
_esc_re = re.compile(r"\\(.)")

# Backslash must be first
_idc_escapes = {"\\": "\\", "r": "\r", "n": "\n", "t": "\t"}


def _get_idc_args(
    command: str, kwargs: Mapping[str, Optional[str | float]]
) -> Iterator[str]:
    yield command
    for key, value in kwargs.items():
        if value is not None:
            value = str(value)
            for escape_char, char in _idc_escapes.items():
                value = value.replace(char, "\\" + escape_char)
            yield f"{key.upper()}={value}"


def _parse_join(
    irc: IDC,
    hostmask: tuple[str, str, str],
    tags: Mapping[str, str],
    args: list[str],
) -> None:
    users = tags.get("=idc-join-users")
    if isinstance(users, str):
        irc._dispatch(
            "353", "", [irc.current_nick, "=", args[0], users]
        )
        irc._dispatch(
            "366", "", [irc.current_nick, args[0], "End of /NAMES list"]
        )


class IDC(miniirc.IRC):
    if miniirc.ver[0] >= 2:

        def _dispatch(
            self, command: str, user: str, args: list[str]
        ) -> None:
            self.handle_msg(
                miniirc.IRCMessage(
                    command,
                    (user, "~u", f"idc/{user}")
                    if user
                    else ("", "", ""),
                    {},
                    args,
                )
            )

    else:

        def _dispatch(
            self, command: str, user: str, args: list[str]
        ) -> None:
            if args:
                args[-1] = _LEADING_COLON + args[-1]
            self._handle(
                command,
                (user, "~u", f"idc/{user}") if user else ("", "", ""),
                {},
                args,
            )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.Handler("JOIN", colon=False, ircv3=True)(_parse_join)

    def _idc_message_parser_no_exc(
        self, msg: str
    ) -> Optional[
        tuple[str, tuple[str, str, str], dict[str, str], list[str]]
    ]:
        try:
            return self.idc_message_parser(msg)
        except Exception:
            traceback.print_exc()
            return None

    def idc_message_parser(
        self, msg: str
    ) -> Optional[
        tuple[str, tuple[str, str, str], dict[str, str], list[str]]
    ]:
        idc_cmd = None
        idc_args = {}
        for arg in msg.split("\t"):
            if "=" in arg:
                key, value = arg.split("=", 1)
                idc_args[key] = _esc_re.sub(
                    lambda m: _idc_escapes.get(m.group(1), "\ufffd"),
                    value,
                )
            else:
                idc_cmd = arg

        # Translate IDC keyword arguments into IRC positional ones
        tags = {}
        if idc_cmd == "PRIVMSG":
            command = "PRIVMSG"
            args = [self.current_nick, idc_args["MESSAGE"]]
        elif idc_cmd == "CHANMSG":
            command = "PRIVMSG"
            args = ["#" + idc_args["TARGET"], idc_args["MESSAGE"]]
        elif idc_cmd == "LOGIN_GOOD":
            command = "001"
            args = [
                self.current_nick,
                f"Welcome to IDC {self.current_nick}",
            ]
        elif idc_cmd == "PONG":
            command = "PONG"
            args = [self.ip, idc_args.get("COOKIE", "")]
        elif idc_cmd == "JOIN":
            command = "JOIN"
            idc_args["SOURCE"] = self.current_nick
            args = ["#" + idc_args["CHANNEL"]]

            # HACK: Add a message tag and fire other events later rather than
            # firing events from the parser function which feels worse.
            # The tag name starts with = so that it doesn't conflict with any
            # actual IRC tags.
            tags["=idc-join-users"] = idc_args["USERS"]
        else:
            return None

        # Add generic parameters
        if "SOURCE" in idc_args:
            user = idc_args["SOURCE"]
            hostmask = (user, "~u", f"idc/{user}")
            tags["account"] = user
        else:
            hostmask = ("", "", "")

        if command == "PRIVMSG":
            # If echo-message wasn't requested then don't send self messages
            if (
                hostmask[0] == self.current_nick
                and "echo-message" not in self.active_caps
            ):
                return None

            # Parse the message type
            msg_type = idc_args.get("TYPE", "").upper()
            if msg_type == "NOTICE":
                command = "NOTICE"
            elif msg_type == "ACTION":
                args[1] = f"\x01ACTION {args[1]}\x01"

        if "TS" in idc_args:
            dt = datetime.datetime.utcfromtimestamp(
                float(idc_args["TS"])
            )
            tags["time"] = dt.isoformat() + "Z"

        if "LABEL" in idc_args:
            tags["label"] = idc_args["LABEL"]

        if miniirc.ver[0] >= 2:
            return miniirc.IRCMessage(command, hostmask, tags, args)
        else:
            if args:
                args[-1] = _LEADING_COLON + args[-1]
            return command, hostmask, tags, args

    # Send raw messages
    def idc_send(self, command: str, **kwargs: Optional[str | float]):
        super().quote(
            "\t".join(_get_idc_args(command, kwargs)), force=True
        )

    def quote(
        self,
        *msg: str,
        force: Optional[bool] = None,
        tags: Optional[Mapping[str, str | bool]] = None,
    ) -> None:
        cmd, _, tags2, args = miniirc.ircv3_message_parser(
            " ".join(msg)
        )
        if miniirc.ver[0] < 2 and args and args[-1].startswith(":"):
            args[-1] = args[-1][1:]
        self.send(cmd, *args, force=force, tags=tags or tags2)

    def _get_idc_account(self) -> Sequence[str]:
        if isinstance(self.ns_identity, tuple):
            return self.ns_identity
        else:
            return self.ns_identity.split(" ", 1)

    @property
    def current_nick(self) -> str:
        return self._get_idc_account()[0]

    def send(
        self,
        cmd: str,
        *args: str,
        force: Optional[bool] = None,
        tags: Optional[Mapping[str, str | bool]] = None,
    ) -> None:
        cmd = cmd.upper()
        label = tags.get("label") if tags else None
        if cmd in ("PRIVMSG", "NOTICE"):
            target = args[0]
            # TODO: Make miniirc think that SASL worked PMs to NickServ don't
            # have to be blocked.
            if target == "NickServ":
                return

            msg = args[1]
            msg_type: Optional[str]
            if cmd == "NOTICE":
                msg_type = "NOTICE"
            elif msg.startswith("\x01ACTION"):
                msg = msg[8:].rstrip("\x01")
                msg_type = "ACTION"
            else:
                msg_type = None

            if target.startswith("#"):
                idc_cmd = "CHANMSG"
                target = target[1:]
            else:
                idc_cmd = "PRIVMSG"

            self.idc_send(
                idc_cmd,
                target=target,
                type=msg_type,
                message=msg,
                label=label,
            )
        elif cmd == "PING":
            self.idc_send("PING", cookie=args[0], label=label)
        elif cmd == "USER":
            user, password = self._get_idc_account()
            self.idc_send(
                "LOGIN", username=user, password=password, label=label
            )
            self.active_caps = self.ircv3_caps & {
                "account-tag",
                "echo-message",
                "labeled-response",
            }

    # Override the message parser to change the default parser.
    def change_parser(self, parser=None):
        super().change_parser(parser or self._idc_message_parser_no_exc)

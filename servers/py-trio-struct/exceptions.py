#!/usr/bin/env python3
#
# This program is made by the World Sus Foundation by Andrew.
#
# Various utility functions for the Internet Delay Chat server written
# in Python Trio.  This library is not intended to be used outside of
# that program.
#
# Written by: Andrew <https://www.andrewyu.org>
#             luk3yx <https://luk3yx.github.io>
#
# This is free and unencumbered software released into the public
# domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.


class Severity:
    UNKNOWN = b"UNKNOWN"
    YAY = b"YAY"
    NORM = b"NORM"
    FAIL = b"FAIL"
    WARN = b"WARN"
    ERROR = b"ERROR"
    SECURITY = b"SECURITY"
    FATAL = b"FATAL"
    THE_PROGRAMMER_IS_DUMB = b"THE_PROGRAMMER_IS_DUMB"


class IDCException(Exception):
    severity = Severity.UNKNOWN
    error_type = b"UNKNOWN"


class IdiotError(IDCException):
    severity = Severity.THE_PROGRAMMER_IS_DUMB
    error_type = b"YOU_DUMB_DEVELOPER"


class IDCUserCausedException(IDCException):
    """
    Should be subclassed by all of the 'user did something wrong' errors
    """

    severity = Severity.ERROR
    error_type = b"USER_ERROR"
    pass


class UnknownCommand(IDCUserCausedException):
    error_type = b"UNKNOWN_COMMAND"


class MissingArgumentError(IDCUserCausedException):
    error_type = b"MISSING_ARGUMENT"


class NotLoggedIn(IDCUserCausedException):
    error_type = b"NOT_LOGGED_IN"


class AlreadyLoggedIn(IDCUserCausedException):
    error_type = b"REDUNDENT_LOGIN"


class LoginFailed(IDCUserCausedException):
    severity = Severity.FAIL
    error_type = b"LOGIN_FAILED"


class NonAlphaKeyError(IDCUserCausedException):
    """
    Putting non-letters into keywords
    """

    error_type = b"INVALID_KEYWORD"


class EscapeSequenceError(IDCUserCausedException):
    """
    I don't know this escape sequence
    """

    error_type = b"DONT_KNOW"


class MultiCommandError(IDCUserCausedException):
    """
    Multiple commands in one line
    """

    error_type = b"MULTIPLE_CMDS"


class MessageUndeliverableError(IDCUserCausedException):
    """
    User to deliver message to is offline and doesn't have the
    offline-messages option.
    """

    error_type = b"MSG_UNDELIVERABLE"


class UserNotFoundError(IDCUserCausedException):
    """
    Raise this for clients trying to message, modify, or otherwise
    interact with a nonexistant user.
    """

    error_type = b"USER_NOT_FOUND"


class StrangeError(IDCException):
    """
    Random errors that shouldn't exist and were probably caused by
    either the hardware blowing up or huge bugs.
    """

    error_type = b"DONT_KNOW"


class KeyCollisionError(IDCUserCausedException):
    """
    Raise when there are redundent keys in a line.
    """

    error_type = b"REDUNDENT_KEYS"


class NonexistantTargetError(IDCUserCausedException):
    """
    target doesnt exist
    """

    error_type = b"NONEXISTANT_TARGET"


class NoExternalMessagesError(IDCUserCausedException):
    """
    sender not in chan
    """

    error_type = b"NO_EXTERNAL_MESSAGES"


class TargetOfflineError(IDCUserCausedException):
    """
    Target offline
    """

    error_type = b"TARGET_OFFLINE"

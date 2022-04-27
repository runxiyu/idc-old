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

import enum
import abc


class Severity(enum.Enum):
    # nah
    NORM = enum.auto()
    FAIL = enum.auto()
    WARN = enum.auto()
    ERROR = enum.auto()
    SECURITY = enum.auto()
    FATAL = enum.auto()


class IDCException(Exception):
    severity = Severity.UNKNOWN
    errorType = "ERR_UNKNOWN"


class IDCUserCausedException(IDCException):
    """
    Should be subclassed by all of the 'user did something wrong' errors
    """

    severity = Severity.ERROR
    errorType = "ERR_USER_ERROR"
    pass


class NonAlphaKeyError(IDCUserCausedException):
    """
    Putting non-letters into keywords
    """

    errorType = "ERR_INVALID_KEYWORD"


class EscapeSequenceError(IDCUserCausedException):
    """
    I don't know this escape sequence
    """

    errorType = "ERR_DONT_KNOW"


class MultiCommandError(IDCUserCausedException):
    """
    Multiple commands in one line
    """

    errorType = "ERR_MULTIPLE_CMDS"


class MessageUndeliverableError(IDCUserCausedException):
    """
    User to deliver message to is offline and doesn't have the
    offline-messages option.
    """

    errorType = "ERR_MSG_UNDELIVERABLE"


class UserNotFoundError(IDCUserCausedException):
    """
    Raise this for clients trying to message, modify, or otherwise
    interact with a nonexistant user.
    """

    errorType = "ERR_USER_NOT_FOUND"


class StrangeError(IDCUserCausedException):
    """
    Random errors that shouldn't exist and were probably caused by
    either the hardware blowing up or huge bugs.
    """

    errorType = "ERR_DONT_KNOW"

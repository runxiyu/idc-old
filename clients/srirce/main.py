# srIRCeBot, a Simple IRC RElay Bot

import miniirc
from miniirc_idc import miniirc_idc
from miniirc_extras import *
from time import sleep

# Configuration

server = [["irc.andrewyu.org", "IRC"], ["andrewyu.org", "IDC"]]
relayedChannels = ["#IDC", "hackers"]
nick = "idcbot"
debug = True

# IRC
irc = miniirc.IRC(
    server[0][0],
    6697,
    nick,
    relayedChannels[0],
    ns_identity=None,
    debug=False,
)
# IDC
idc = miniirc_idc.IDC(
    server[1][0],
    6835,
    nick,
    relayedChannels[1],
    ns_identity=["idcbot", ""],
    debug=debug,
)

# Relay functions


def relay_msgs(chat, hostmask, args, which):
    sleep(0.5)  # Sleep for 0.5 seconds
    whichchan = 0 if which == 1 else 1
    # Send in the irc side what the user sent in the idc side and vice-versa
    print("NEW MESSAGE")
    chat.send(
        "CHANMSG",
        relayedChannels[whichchan],
        "(%s) <%s> %s" % (server[which][1], hostmask[0], args[-1]),
    )
    # chat.send('PRIVMSG', relayedChannels[whichchan],
    #            "(%s) <%s> %s"
    #            % (server[which][1], hostmask[0], args[-1]))


def relay_nick(chat, hostmask, args, which):
    sleep(0.5)
    whichchan = 0 if which == 1 else 1
    # Send in the idc side the nick change in the irc side
    chat.send(
        "PRIVMSG",
        relayedChannels[whichchan],
        "(%s) %s is now known as %s"
        % (server[which][1], hostmask[0], args[0]),
    )


def relay_joins(chat, hostmask, args, which):
    sleep(0.5)
    whichchan = 0 if which == 0 else 1
    # Send in the idc side joins in the irc side and vice-versa
    chat.send(
        "PRIVMSG",
        relayedChannels[whichchan],
        "(%s) %s has joined %s"
        % (server[which][1], hostmask[0], args[0]),
    )


def relay_mode(chat, hostmask, args, which):
    # sleep(0.5)
    # whichchan = 0 if which == 1 else 1
    # chat.send('PRIVMSG', relayedChannels[whichchan],
    #         "(%s) %s: [%s] by %s"
    #         % (server[which][1], args[0], args[1], hostmask[0]))
    # Doesn't work for some reason
    pass


def relay_quits(chat, hostmask, args, which):
    sleep(0.5)
    whichchan = 0 if which == 1 else 1
    # Send in the idc side quits in the irc side and vice-versa
    chat.send(
        "PRIVMSG",
        relayedChannels[whichchan],
        "(%s) %s has quit %s"
        % (server[which][1], hostmask[0], args[0]),
    )


def relay_kicks(chat, hostmask, args, which):
    sleep(0.5)
    whichchan = 0 if which == 1 else 1
    # Send in the idc side kicks in the irc side and vice-versa
    chat.send(
        "PRIVMSG",
        relayedChannels[whichchan],
        "(%s) %s was kicked from %s by %s"
        % (server[which][1], args[1], args[0], hostmask[0]),
    )


# Functions that run the relay functions, depending on the server where the message has been sent
@miniirc.Handler("NICK", colon=False)
def handle_nicks(chat, hostmask, args):
    if chat == idc:
        relay_nick(irc, hostmask, args, 0)
    elif chat == irc:
        relay_nick(idc, hostmask, args, 1)


@miniirc.Handler("KICK", colon=False)
def handle_kicks(chat, hostmask, args):
    if chat == irc:
        relay_kicks(irc, hostmask, args, 0)
    elif chat == idc:
        relay_kicks(idc, hostmask, args, 1)


@miniirc.Handler("JOIN", colon=False)
def handle_joins(chat, hostmask, args):
    if chat == irc:
        relay_joins(irc, hostmask, args, 0)
    elif chat == idc:
        relay_joins(idc, hostmask, args, 1)


@miniirc.Handler("PART", colon=False)
def handle_quits(chat, hostmask, args):
    if chat == irc:
        relay_quits(irc, hostmask, args, 0)
    elif chat == idc:
        relay_quits(idc, hostmask, args, 1)


@miniirc.Handler("PRIVMSG", colon=False)
def handle_privmsgs(chat, hostmask, args):
    words = args[-1].split(" ")
    w = [x.lower() for x in words]
    channel = args[0]
    command = words[0].lower()
    if chat == irc:
        if command.startswith(":sendmessage"):
            sleep(0.5)
            irc.send(
                "PRIVMSG",
                relayedChannels[1],
                "[\x02\x0308%s\x02\x0300] <\x02%s\x02>"
                % (server[0][1], hostmask[0]),
            )
            irc.send(
                "PRIVMSG",
                channel,
                "%s"
                % args[-1]
                .split("//////")[0]
                .replace(":sendmessage ", ""),
            )
            return
        elif command.startswith(":chat"):
            sleep(0.5)
            irc.send(
                words[1],
                relayedChannels[1],
                words[2],
                "%s (requested by %s)" % (words[-1], hostmask[0]),
            )
            return
        relay_msgs(idc, hostmask, args, 0)
    elif chat == idc:
        if command.startswith(":sendmessage"):
            sleep(0.5)
            idc.send(
                "PRIVMSG",
                relayedChannels[0],
                "[\x02\x0308%s\x02\x0300] <\x02%s\x02>"
                % (server[1][1], hostmask[0]),
            )
            idc.send(
                "PRIVMSG",
                channel,
                "%s"
                % args[-1]
                .split("//////")[0]
                .replace(":sendmessage ", ""),
            )
            return
        elif command.startswith(":chat"):
            sleep(0.5)
            idc.send(
                words[1],
                relayedChannels[0],
                words[2],
                "%s (requested by %s)" % (words[-1], hostmask[0]),
            )
            return
        relay_msgs(irc, hostmask, args, 1)


@miniirc.Handler("CHANMSG", colon=False)
def handle_chanmsgs(chat, hostmask, args):
    words = args[-1].split(" ")
    w = [x.lower() for x in words]
    channel = args[0]
    command = words[0].lower()
    if chat == irc:
        if command.startswith(":sendmessage"):
            sleep(0.5)
            irc.send(
                "PRIVMSG",
                relayedChannels[1],
                "[\x02\x0308%s\x02\x0300] <\x02%s\x02>"
                % (server[0][1], hostmask[0]),
            )
            irc.send(
                "PRIVMSG",
                channel,
                "%s"
                % args[-1]
                .split("//////")[0]
                .replace(":sendmessage ", ""),
            )
            return
        elif command.startswith(":chat"):
            sleep(0.5)
            irc.send(
                words[1],
                relayedChannels[1],
                words[2],
                "%s (requested by %s)" % (words[-1], hostmask[0]),
            )
            return
        relay_msgs(idc, hostmask, args, 0)
    elif chat == idc:
        if command.startswith(":sendmessage"):
            sleep(0.5)
            idc.send(
                "PRIVMSG",
                relayedChannels[0],
                "[\x02\x0308%s\x02\x0300] <\x02%s\x02>"
                % (server[1][1], hostmask[0]),
            )
            idc.send(
                "PRIVMSG",
                channel,
                "%s"
                % args[-1]
                .split("//////")[0]
                .replace(":sendmessage ", ""),
            )
            return
        elif command.startswith(":chat"):
            sleep(0.5)
            idc.send(
                words[1],
                relayedChannels[0],
                words[2],
                "%s (requested by %s)" % (words[-1], hostmask[0]),
            )
            return
        relay_msgs(irc, hostmask, args, 1)


@miniirc.Handler("MODE", colon=False)
def handle_mode(chat, hostmask, args):
    if chat == irc:
        relay_mode(irc, hostmask, args, 0)
    elif chat == idc:
        relay_mode(idc, hostmask, args, 1)

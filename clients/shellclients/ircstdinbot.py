#!/usr/bin/python3
#
# stdinbot - Read text from stdin and send it to an IRC channel
#
# © 2018 by luk3yx
#

import sys, time
from miniirc import IRC

# Variables
nick       = 'idc'
ident      = nick
realname   = 'Internet Delay Chat Relay'
identity   = None
# identity = '<username> <password>'
print_cmds = False
interval   = 0.25

channels = ['#idc']
debug    = False

ip = 'irc.andrewyu.org'
port = 6697

print("Welcome to stdinbot!", file=sys.stderr)
irc = IRC(ip, port, nick, channels, ident=ident, realname=realname,
    ns_identity=identity, debug=debug, auto_connect=False)

# Read stdin
@irc.Handler('001', colon=False)
def handle_stdin(irc, hostmask, args):
    qmsg = 'I reached the end of my file, therefore my life™.'
    while True:
        try:
            line = + input().replace('\r', '').replace('\n', '  ')
        except:
            line = '\x04'
        if line == '\x04':
            return irc.disconnect(qmsg)
        irc.msg(channels[0], line)
        time.sleep(interval)

@irc.Handler('PRIVMSG', colon=False)
def handle_privmsg(irc, hostmask, args):
    #if args[0] in channels:
    if True:
        print("<" + hostmask[0] + "> " + args[1])

if __name__ == '__main__':
    irc.connect()

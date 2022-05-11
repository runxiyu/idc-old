%%%
title = "Internet Delay Chat Protocol"
abbrev = "Internet Delay Chat Protocol"
ipr= "none"
area = "Internet"
workgroup = "IDC Working Group"
#submissiontype = "IETF"
submissiontype = "independent"
keyword = ["messaging", "protocol"]
#date = 2022-04-04T00:00:00Z

[seriesInfo]
name = "Internet-Draft"
value = "internet-delay-chat"
stream = "independent"
status = "informational"

[[author]]
initials="A."
surname="Yu"
fullname="Andrew Yu"
 [author.address]
 email = "andrew@andrewyu.org"
[[author]]
initials="T."
surname="User"
fullname="Test_User"
 [author.address]
 email = "hax@andrewyu.org"
[[author]]
initials="F."
surname="EL HAFIDI"
fullname="Ferass EL HAFIDI"
 [author.address]
 email = "vitali64pmemail@protonmail.com"
%%%

.# Abstract

Documentation is usually out of date.  It is updated every few weeks.
Please reference the Python Trio server implementation.

This document specifies a new Internet Protocol for messaging over the Internet.

{mainmatter}

#  Introduction

The IDC (Internet Delay Chat) protocol has been designed over a number of months for federated multimedia conferencing.  This document describes the current IDC protocol.

IDC itself is a messaging system, which (through the use of the client-server and server-to-server model) is well-suited to running on many machines in a distributed fashion.  A typical setup involves multiple servers each with multiple clients, that connect to each other in order to exchange messages, in a multi-centered fashion.

## Limitations of Existing Protocols

Existing protocols are limited.  The Internet Relay Chat Protocol as described in RFC 1459 is a very simple protocol for teleconferencing system.  Later updates such as RFC 2812 have been badly accepted.

When a client disconnects, the IRC network no longer recognizes the client, and messages during the client's downtime are not saved.  This renders IRC unfit for instant messaging, where clients are forced to disconnect but messages are to be read later.

IRC is also not federated, causing most people to be on the few large networks which may lead to privacy and stability issues (for example, the freenode takeover [citation needed]).  Though IRC is technically multi-centered, it is not politically, as servers fully trust other servers, and thus are typically run by the same organization.

Most modern IRC networks use dedicated "services" servers for user, channel, and group management and dedicated client bots for extensible channel management.  Compared with these features built into the server, this is ineffective.  Features such as timed mutes should be handled server-side rather than by a clientbot.

The Extensible Messaging and Presence Protocol, also known as XMPP or Jabber, was designed for presense, instant messaging, and conferences.  However, it is based on XML, and implementations are large and buggy.  XML is inherently bloated and causes unnecessary spam in the network.  XMPP is not multicast either, messages are slow and especially inefficent with multi user chats.  IRC, on the other hand, is a simple text-oriented protocol, where implementing is more straightforward and is harder to write bugs into.

The Discord messaging platform is a proprietary platform for team, community and personal communications.  It is very popular and widely used among gamers, but it's controlled by a single entity with bad privacy records, making it unfit for many communications.  Unlike other Free protocols (such as Matrix and XMPP), messages aren't encrypted, which means that the people behind Discord are able to see every message that you type.  They also actively block Tor users, which have to give Discord their phone number in order to use the platform.  Their client is also proprietary and they disallow alternative clients made with the bot API.  This is a platform that is very bad for privacy and security.  You also cannot host your own server (unlike Matrix, XMPP, and IRC).  You have to rely on centralised servers controlled by Discord themselves.

The Matrix protocol is a Free protocol that has encrypted messages, spaces (like Discord's "guilds"), and some more features.  The people behind Matrix also maintain the Element.io client which looks a lot like Discord.  However, that client is quite big and most other clients either lack features or are unstable.  The Matrix server software, Synapse, is also very big and uses lots of resources.  Matrix is federated however, but most people prefer using the Matrix.org homeserver, due to the instability and inefficency of its server-to-server protocol, with only a handful of people self-hosting their own.  While it is very user-friendly, Synapse is so slow that most people prefer using Matrix.org.  So one of the many issues of IRC is also there: most people join big instances, which is bad for privacy as this is one point of failure.  Matrix also uses a so-called "identity" server.  Most people use the vector.im identity server, which is also bad for privacy.

IDC aims to solve these problems progressively.  The current version of IDC is a text-based non-federated protocol where users may have multiple connections and are not destroyed when all connections are destroyed, and servers save messages when the user is offline.  Future versions will be federated, and may be distributed in the far future.  This document describes the first version of IDC.


# General Concepts

## Servers

The server forms the backbone of IDC, providing a point to which clients may connect to to talk to each other, and a point for other servers to connect to, forming the global IDC network.  The network is a mesh where each server connects to other servers directly.

## Clients

A client is anything connecting to a server that is not another server.

## Users

Each client is associated with a user when it logs in.  Users are identified by a UID, in the form of user@host, where host is either (1) the FQDN of the server the user resides on or (2) a domain with a SRV record to the actual server.  The UID is unique in the Internet.  Messages are directed at users, which are then sent to all connected clients of the said user.  If the user has no connected clients, i.e. the user is offline, the message SHOULD be kept until the user reconnects.


### Administrators

To allow a reasonable amount of order to be kept within a server, a special class of users (administrators) is allowed to perform general maintenance functions on the server.  Although the powers granted to an administrator can be considered as 'dangerous', they are nonetheless required.  Administrators should be able to perform basic network tasks such as disconnecting and reconnecting servers as needed to prevent long-term use of bad network routing.  In recognition of this need, the protocol discussed herein provides for operators only to be able to perform such functions.

A system where independent users vote to decide on server actions MAY be implemented.

## Spaces

A space is a identified group of one of more users.  The space is created explicitly by a user on a server, and ceases to exist when the last user leaves it.  While the space exists, any user can reference the space using the identifier of the space.

Space identifiers are strings with the form "&name@server", where *name* is an alphanumeric string of length up to 128 characters and *server* is the server name of which the founder of the space resides on.

To create a new space or become part of an existing space, a user is required to JOIN the space.  If the space doesn't exist prior to joining, the space is created under the server the user is on and the creating user becomes the space operator.  If the space already exists, whether or not the request to JOIN that space is honoured depends on the current options of the space. For example, if the space is invite-only, (`+INVITE_ONLY`), then the user may only join if invited.  As part of the protocol, a user may be a part of several spaces at once.

A user may have a nickname for use within the space, independent of their nickname when used outside of spaces, which is an alphanumeric of length up to 128 characters.  A space may not have two users with the same nickname.  In these cases, the user joined later (according to packet receiving order by the space's hosting server) will have a underscore appended to per nickname until it no longer collides with any other nickname in the space.  If during this process the nickname exceeds 128 characters, the user is required to choose another nickname.

  Note: We'd need to define what "packet" is, since they're not lines in TCP, or datagrams in UDP, but something custom.

## Channels

Channels are a group of users in a space who have permissions for reading the channel.  Channel identifiers are strings, appending a '#' character and a name, where the name is an alphanumeric string of up to 128 characters, to the space that the channel is in.

# Permission System

## Permissions

Permissions allow users to perform actions that do not interfere with
the permissions other users.

- talk :: allow the user to talk
- read :: allow the user to read the chat

## Anti-permissions

Anti-permissions cause the user to be unable to exercise a matching
permission, even if their role contains the said permission.  There
exists an anti-permission for each permission, with the name of the
permission preceeded by a "-" (ASCII 0x2D HYPHEN-MINUS) character.

- -talk :: causes the user to be unable to talk
- -read :: causes the user to be deafened

## Roles

Roles are sets of permissions, anti-permissions and management permissions (as defined in section 4).  Users may have multiple roles and must at least have one role.  All permissions, anti-permissions, and management permissions are granted via roles; users who have a role with a given permission have the permission, and users who don't have any roles containing a permission don't have the permission.  Roles are ranked linearly, and may be set to self-deroleable.

Note that the examples below note an example setup.  Those with the "roles" management permission may customize these, as noted in section 4.

- 1 administrator :: talk, read, mute, deafen, kick, ban, react
- 2 teacher :: talk, read, mute, deafen, ban, react
- 3 student :: talk, read, react
- 0 default :: talk, read
- -1 spammer :: -talk, read, -react

## Management Permissions

Management permissions allow managing roles.

There exists a management permission for each permission, and thus, each anti-permission.

A user may give a user of a role, if all of the following conditions are met:
- The user affected has a lower role than the actor;
- The role given is lower or equal to the actor's role;
- The actor has all corresponding management permissions for the permissions and anti-permissions of the role given.

(how does granting management permissions work again)

# The IDC Specification

## Overview

The protocol as described herein is for use both with server to server and client to server connections.  There are similiar restrictions on server connections as for client connections as this is a federated protocol.

## Character codes

The character encoding for IDC is UTF-8.

## Messages

Servers and clients send eachother messages which may or may not generate a reply.  If the message contains a valid command, as described in later sections, the client should expect a reply as specified but it is not advised to wait forever for the reply; client to server and server to server communication is essentially asynchronous in nature.

Each IDC message may consist of up to three main parts: the prefix (optional), the command, and the command parameters (of which there may be up to 30).  The prefix, command, and all parameters are separated by one (or more) ASCII space character(s) (0x20).

The presence of a prefix is indicated with a single leading ASCII colon character (':', 0x3b), which must be the first character of the message itself.  There must be no gap (whitespace) between the colon and the prefix.  The prefix is used by servers to indicate the true origin of the message.  If the prefix is missing from the message, it is assumed to have originated from the connection from which it was received.  Clients should not use prefix when sending a message from themselves; if they use a prefix, the only valid prefix is the registered nickname associated with the client.  If the source identified by the prefix cannot be found from the server's internal database, or if the source is registered from a different link than from which the message arrived, the server must ignore the message with an error message.

The command must be a valid IDC command.

IDC messages are always lines of characters terminated with a CR-LF (Carriage Return - Line Feed) pair, and these messages shall not exceed 65536 characters in length, counting all characters including the trailing CR-LF. Thus, there are 65534 characters maximum allowed for the command and its parameters.  There is no provision for continuation message lines.  See section <++> for more details about current implementations.

The protocol messages must be extracted from the contiguous stream of data.  The current solution is to designate two characters, CR and LF, as message separators.   Empty  messages  are  silently  ignored, which permits  use  of  the  sequence  CR-LF  between  messages without extra problems.

The extracted message is parsed into the components <prefix>,
<command> and list of parameters matched either by <middle> or
<trailing> components.

The BNF representation for this is:

```
<message>  ::= [':' <prefix> <SPACE> ] <command> <params> <crlf>
<prefix>   ::= <servername> | <nick> [ '!' <user> ] [ '@' <host> ]
<command>  ::= <letter> { <letter> } | <number> <number> <number>
<SPACE>    ::= ' ' { ' ' }
<params>   ::= <SPACE> [ ':' <trailing> | <middle> <params> ]

<middle>   ::= <Any *non-empty* sequence of octets not including SPACE
               or NUL or CR or LF, the first of which may not be ':'>
<trailing> ::= <Any, possibly *empty*, sequence of octets not including
                 NUL or CR or LF>

<crlf>     ::= CR LF
```

NOTES:

1. <SPACE> is consists only of SPACE character(s) (0x20).  Specially notice that TABULATION, and all other control characters are considered NON-WHITE-SPACE.
2. After extracting the parameter list, all parameters are equal, whether matched by <middle> or <trailing>. <Trailing> is just a syntactic trick to allow SPACE within parameter.
3. The fact that CR and LF cannot appear in parameter strings is just artifact of the message framing.
4. The NUL character is not special in message framing, and basically could end up inside a parameter, but as it would cause extra complexities in normal C string handling. Therefore NUL is not allowed within messages.
5. The last parameter may be an empty string.
6. Use of the extended prefix (['!' <user> ] ['@' <host> ]) must not be used in server to server communications and is only intended for server to client messages in order to provide clients with more useful information about who a message is from without the need for additional queries.

Most protocol messages specify additional semantics and syntax for
the extracted parameter strings dictated by their position in the
list.  For example, many server commands will assume that the first
parameter after the command is the list of targets, which can be
described with:

```
<target>     ::= <to> [ "," <target> ]
<to>         ::= <channel> | <user> '@' <server> | <mask>
<channel>    ::= ('#') <chstring>
<servername> ::= <host>
<host>       ::= see RFC 952 [DNS:4] for details on allowed hostnames
<uid>       ::= <letter> { <letter> | <number> }
<mask>       ::= ('#' | '$') <chstring>
<chstring>   ::= <any 8bit code except SPACE, BELL, NUL, CR, LF and
                  comma (',')>
```

Other parameter syntaxes are:

```
<user>       ::= <nonwhite> { <nonwhite> }
<letter>     ::= 'a' ... 'z' | 'A' ... 'Z'
<number>     ::= '0' ... '9'
<special>    ::= '-' | '[' | ']' | '\' | '`' | '^' | '{' | '}'
```

```
<nonwhite>   ::= <any 8bit code except SPACE (0x20), NUL (0x0), CR
                  (0xd), and LF (0xa)>
```

# IDC Concepts.

This section is devoted to describing the actual concepts behind  the organization of  the IDC protocol and how the current implementations deliver different classes of messages.

## One-to-one communication

Communication on a one-to-one basis is usually only performed by clients, since most server-server traffic is not a result of servers talking only to each other.  To provide a secure means for clients to talk to each other, it is required that all servers be able to send a message to any other server.

## One-to-many

The main goal of IRC is to provide a  forum  which  allows  easy  and
efficient  conferencing (one to many conversations).  IRC offers
several means to achieve this, each serving its own purpose.

### To a list

The least efficient style of one-to-many conversation is through clients talking to a 'list' of users.  How this is done is almost self explanatory: the client gives a list of destinations to which the message is to be delivered and the server breaks it up and dispatches a separate copy of the message to each given destination.  This isn't as efficient as using a group since the destination list is broken up and the dispatch sent without checking to make sure duplicates aren't sent down each path.

### To a channel

In IRC the channel has a role equivalent to that of the multicast group; their existence is dynamic (coming and going as people join and leave channels) and the actual conversation carried out on a channel is only sent to servers which are supporting users on a given channel.  If there are multiple users on a server in the same channel, the message text is sent only once to that server and then sent to each client on the channel.  This action is then repeated for each client-server combination until the original message has fanned out and reached each member of the channel.

# Message details

On the following pages are descriptions of each message recognized by the IRC server and client.  All commands described in this section must be implemented by any server for this protocol.

Where the reply ERR_NOSUCHSERVER is listed, it means that the <server> parameter could not be found.  The server must not send any other replies after this for that command.

The server to which a client is connected is required to parse the complete message, returning any appropriate errors.  If the server encounters a fatal error while parsing a message, an error must be sent back to the client and the parsing terminated.  A fatal error may be considered to be incorrect command, a destination which is otherwise unknown (server, user or channel names fit this category), not enough parameters or incorrect privileges.

If a full set of parameters is presented, then each must be checked for validity and appropriate responses sent back to the client.  In the case of messages which use parameter lists using the comma as an item separator, a reply must be sent for each item.

In the examples below, some messages appear using the full format:

```
:Name COMMAND parameter list
```

Such examples represent a message from "Name" in transit between servers, where it is essential to include the name of the original sender of the message so remote servers may send back a reply along the correct path.

## Connection Registration

The commands described here are used to register a connection with an IRC server as either a user or a server as well as correctly disconnect.

A "PASS" command is not required for either client or server connection to be registered, but it must precede the server message or the latter of the NICK/USER combination.  It is strongly recommended that all server connections have a password in order to give some level of security to the actual connections.  The recommended order for a client to register is as follows:

1. Pass message
2. Nick message
3. User message

### Password message

      Command: PASS
   Parameters: <password>

The PASS command is used to set a 'connection password'.  The password can and must be set before any attempt to register the connection is made.  Currently this requires that clients send a PASS command before sending the NICK/USER combination and servers *must* send a PASS command before any SERVER command.  The password supplied must match the one contained in the C/N lines (for servers) or I lines (for clients).  It is possible to send multiple PASS commands before registering but only the last one sent is used for verification and it may not be changed once registered.

   Replies:

           ERR_NEEDMOREPARAMS              ERR_ALREADYREGISTRED

   Example:

           PASS secretpasswordhere

### Nick message

      Command: NICK
   Parameters: <nickname>

NICK message is used to give user a nickname or change the previous one.

Numeric Replies:

         ERR_NONICKNAMEGIVEN             ERR_ERRONEUSNICKNAME

### User message

      Command: USER
   Parameters: <UID> <realname>

The USER message is used at the beginning of connection to specify the username, hostname, servername and realname of s new user.  It is also used in communication between servers to indicate new user arriving on IDC, since only after both USER and NICK have been received from a client does a user become registered.

Between servers USER must to be prefixed with client's UID.  Note that hostname and servername are normally ignored by the IRC server when the USER command comes from a directly connected client for security reasons, but they are used in server to server communication.

It must be noted that realname parameter must be the last parameter, because it may contain space characters and must be prefixed with a colon (':') to make sure this is recognised as such.

Replies:

        ERR_NEEDMOREPARAMS              ERR_ALREADYREGISTRED

Examples:

```
USER andrew@andrewyu.org :Andrew Yu
```

### Server message

      Command: SERVER
   Parameters: <servername> <server description>

The SERVER message must only be accepted from a connection which is yet to be registered and is attempting to register as a server.

Most errors that occur with the receipt of a SERVER command result in the connection being terminated by the destination host (target SERVER).  Error replies are usually sent using the "ERROR" command rather than the numeric since the ERROR command has several useful properties which make it useful here.

### Quit

      Command: QUIT
   Parameters: [<Quit message>]

A client session is ended with a quit message.  The server must close the connection to a client which sends a QUIT message. If a "Quit Message" is given, this will be sent instead of the default message, the nickname.

If, for some other reason, a client connection is closed without  the client  issuing  a  QUIT  command  (e.g.  client  dies and EOF occurs on socket), the server is required to fill in the quit  message  with some sort  of  message  reflecting the nature of the event which caused it to happen.

### Server quit message

      Command: SQUIT
   Parameters: <server> <comment>

The SQUIT message is needed to tell about quitting servers.  If a server wishes to break the connection to another server it must send a SQUIT message to the other server, using the the name of the other server as the server parameter, which then closes its connection to the quitting server.

This command is also available operators to help keep a network of IRC servers connected in an orderly fashion.  Administrators may also issue an SQUIT message for a remote server connection.

The <comment> should be supplied by all administrator who execute a SQUIT for a remote server (that is not connected to the server they are currently on) so that other administrators are aware for the reason of this action.  The <comment> is also filled in by servers which may place an error or similar message here.

Replies:

        ERR_NOPRIVILEGES                ERR_NOSUCHSERVER

## Channel operations

This group of messages is concerned with manipulating channels, their properties (channel modes), and their contents (typically users).  In implementing these, a number of race conditions are inevitable when users send commands which will ultimately clash.

### Join message

   Command: JOIN
   Parameters: <channel>{,<channel>} [<key>{,<key>}]

The JOIN command is used by user to start listening a specific
channel. Whether or not a user is allowed to join a channel is
checked by the server hosting the channel.

The conditions of joining are as follows:

1.  the user must be invited if the channel is invite-only;
2.  the user's UID and per server must not match any active bans;
3.  the correct key (password) must be correct if it is set.

These are discussed in more detail under the MODE command (see
section 4.2.3 for more details).

Once a user has joined a channel, they receive notice about all commands their server receives which affect the channel.  This includes MODE, KICK, PART, QUIT and of course PRIVMSG/NOTICE.  The JOIN command needs to be broadcast to all servers where a user thereof is on the said channel so that each server knows where to find the users who are on the channel.  This allows optimal delivery of PRIVMSG/NOTICE messages to the channel.

If a JOIN is successful, the user is then sent the channel's topic (using RPL_TOPIC) and the list of users who are on the channel (using RPL_NAMREPLY), which must include the user joining.

Replies:

        ERR_NEEDMOREPARAMS              ERR_BANNEDFROMCHAN
        ERR_INVITEONLYCHAN              ERR_BADCHANNELKEY
        ERR_CHANNELISFULL               ERR_BADCHANMASK
        ERR_NOSUCHCHANNEL               ERR_TOOMANYCHANNELS
        RPL_TOPIC

### Part message

   Command: PART
   Parameters: <channel>{,<channel>}

The PART message causes the client sending the message to be removed from the list of active users for all given channels listed in the parameter string.

Replies:

        ERR_NEEDMOREPARAMS              ERR_NOSUCHCHANNEL
        ERR_NOTONCHANNEL

### Mode message

   Command: MODE

The MODE command is a dual-purpose command in IDC.  It allows both usernames and channels to have their mode changed.

When parsing MODE messages, it is recommended that the entire message be parsed first and then the changes which resulted then passed on.

#### Channel modes

   Parameters: <channel> {[+|-]|<modes>} [<param>]

The MODE command is provided so that channel operators may change the characteristics of `their' channel.  It is also required that servers be able to change channel modes so that channel operators may be created.

The various modes available for channels are as follows:

   OPERATOR - give/take channel operator privileges;
   SECRET - secret channel flag;
   INVITE_ONLY - invite-only channel flag;
   TOPIC_OPERATOR_ONLY - topic settable by channel operator only flag;
   NO_EXTERNAL_MESSAGES - no messages to channel from clients on the outside;
   MODERATED - moderated channel;
   BAN - set a ban mask to keep users out;
   QUIET - set a quiet mask to keep users silent;
   VOICE - give/take the ability to speak on a moderated channel;
   KEY - set a channel key (password).

#### User modes

   Parameters: <nickname> {[+|-]|<modes>} [<param>]

The user MODEs are typically changes which affect either how the
client is seen by others or what 'extra' messages the client is sent.
A user MODE command may only be accepted if both the sender of the
message and the nickname given as a parameter are both the same.

The available modes are as follows:

        SERVER_NOTICES - marks a user for receipt of server notices;
        ADMINISTRATOR - operator flag.

If a user attempts to make themselves an administrator using the "+ADMINISTRATOR" flag, the attempt should return ERR_NOPRIVILEGES.  There is no restriction, however, on anyone `deadministratoring' themselves (using "-ADMINISTRATOR").

Replies:

        ERR_NEEDMOREPARAMS              RPL_CHANNELMODEIS
        ERR_CHANOPRIVSNEEDED            ERR_NOSUCHNICK
        ERR_NOTONCHANNEL                ERR_KEYSET
        RPL_BANLIST                     RPL_ENDOFBANLIST
        ERR_UNKNOWNMODE                 ERR_NOSUCHCHANNEL
        ERR_USERSDONTMATCH              RPL_UMODEIS
        ERR_UMODEUNKNOWNFLAG

#### Topic message

   Command: TOPIC
   Parameters: <channel> [<topic>]

The TOPIC message is used to change or view the topic of a channel. The topic for channel <channel> is returned if there is no <topic> given.  If the <topic> parameter is present, the topic for that channel will be changed, if the channel modes permit this action.

Replies:

        ERR_NEEDMOREPARAMS              ERR_NOTONCHANNEL
        RPL_NOTOPIC                     RPL_TOPIC
        ERR_CHANOPRIVSNEEDED

#### Names message

   Command: NAMES
   Parameters: [<channel>{,<channel>}]

By using the NAMES command, a user can list all nicknames that are visible to them on any channel that they can see.  Channel names which they can see are those which aren't secret (+s) or those which they are actually on.  The <channel> parameter specifies which channel(s) to return information about if valid. There is no error reply for bad channel names.

If no <channel> parameter is given, a list of all channels and their
occupants is returned.  At the end of this list, a list of users who are
visible but either not on any channel or not on a visible channel are
listed as being on 'channel' "*".

Numerics:

        RPL_NAMREPLY                    RPL_ENDOFNAMES

#### Invite message

   Command: INVITE
   Parameters: <nickname> <channel>

The INVITE message is used to invite users to a channel.  The parameter <nickname> is the nickname of the person to be invited to the target channel <channel>.  The target user is being invited to must exist or be a valid channel.  To invite a user to a channel which is invite only (MODE +i), the client sending the invite must be recognised as being a channel operator on the given channel.

Replies:

           ERR_NEEDMOREPARAMS              ERR_NOSUCHNICK
           ERR_NOTONCHANNEL                ERR_USERONCHANNEL
           ERR_CHANOPRIVSNEEDED
           RPL_INVITING                    RPL_AWAY

#### Kick command

   Command: KICK
   Parameters: <channel> <user> [<comment>]

The KICK command can be  used  to  forcibly  remove  a  user  from  a
channel.   It  'kicks  them  out'  of the channel (forced PART).

Only a channel operator may kick another user out of a  channel.
Each  server that  receives  a KICK message checks that it is valid
(ie the sender is actually a  channel  operator)  before  removing
the  victim  from  the channel.

Replies:

        ERR_NEEDMOREPARAMS              ERR_NOSUCHCHANNEL
        ERR_BADCHANMASK                 ERR_CHANOPRIVSNEEDED
        ERR_NOTONCHANNEL

## Server queries and commands


# IANA Considerations
# Security Considerations

{backmatter}

# Acknowledgements

This document has multiple ideas suggested by luk3yx.

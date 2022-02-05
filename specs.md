%%%
Title = "Internet Delay Chat Protocol"
abbrev = "Internet Delay Chat Protocol"
#ipr= "trust200902"
area = "Internet"
workgroup = "Network Working Group"
submissiontype = "IETF"
keyword = [""]
date = 2022-02-07T00:00:00Z

[seriesInfo]
name = "RFC"
value = "65535"
stream = "IETF"
status = "informational"

[[author]]
initials="A."
surname="Yu"
fullname="Andrew Yu"
 [author.address]
 email = "andrew@andrewyu.org"
# phone = "+49 176 62 05 94 27"
  [author.address.postal]
  city = "Shanghai"
  country = "China"
%%%


.# Abstract

THIS DOCUMENT IS A DRAFT.  THE "STATUS OF THIS MEMO" IS FALSE.

This document specifies a new Internet Protocol for Instant Messaging over the Internet.

{mainmatter}

#  Introduction

The IDC (Internet Delay Chat) protocol has been designed over a number of days for use with federated multimedia conferencing.  This document describes the current IDC protocol.

IDC itself is a messaging system, which (through the use of the client-server and server-to-server model) is well-suited to running on many machines in a distributed fashion.  A typical setup involves multiple servers each with multiple clients, that connect to each other in order to exchange messages, in a multi-centered fashion.

Internet Relay Chat as in RFC 1459 has been in use since May 1993, a very simple protocol for teleconferencing system.  Later updates such as RFC 2812 have been badly accepted.  It was not designed for personal instant messaging.

IRC is real time.  When a client disconnects, the server no longer recognizes the client, and messages during the client's downtime are not saved.  This renders IRC unfit for instant messaging, where clients are forced to disconnect but messages are to be read later.  IRC is not federated, causing most people to be on the few large networks, imparing user freedom.

Most modern IRC networks use dedicated "services" servers for user, channel, group, etc. management and dedicated client bots for extensible channel management.  Compared with these features built into the server, this is ineffective and redundent.

The Extensible Messaging and Presence Protocol was designed for presense, instant messaging, and conferences.  However, it is based on XML, and implementations are large and buggy.  IRC is a simple text-oriented protocol, where implementing is more straightforward and is harder to bug.

SMS does not work over the Internet, and is generally expensive.

{backmatter}

# Acknowledgements

This document has multiple ideas suggested by Test_User \<hax@andrewyu.org\>.

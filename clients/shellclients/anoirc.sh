#!/bin/bash

#no PATH, no way to accidently run any programs
PATH=''

#useful variables
term_height=0
term_width=0
term_scroll_height=0
status_line_row=0
irc_host=''
irc_channel=''
irc_nick=''


function scroll_bottom() {
	echo -en '\e[999B'
}

#figure out terminal height, NOTE: moves cursor to bottom of terminal
function term_height() {
	echo -en '\e[999B\e[6n'
	read -s -r -d'['
	read -s -r -d';' term_height
	read -s -r -d'R' term_width
	echo -en '\e[999D'
}

#set the area the terminal is allowed to scroll in
function scroll_helper() {
	term_scroll_height=$((term_height-2))
	status_line_row=$((term_height-1))
	echo -en "\e[0;${term_scroll_height}r"
}

function bottom_line() {
	echo -en "\e[${term_height};0f"
}

function paste_data() {
	echo -en '\e7' "\e[${term_scroll_height};0f" '\n'
	echo -n " $1"
	echo -en '\e8'
}

function status_line() {
	echo -en '\e7' "\e[${status_line_row};0f" '\e[2K'
	echo -en "\e[4;44mSTATUS: $irc_nick in $irc_channel @ $irc_host\e[0m"
	echo -en '\e8'
}

function init_screen() {
	echo -en '\e[r' #reset screen
	term_height
	scroll_helper
	bottom_line
}

function net_fd_helper() {
	local buff=''
	
	#close 44 if open, then open read/write
	exec 44>&-
	exec 44<>"$1"
	
	#delay slightly to improve chance of success
	#read -s -r -t1 -u 44

	#try connecting, sometimes JOIN won't work here and will have to be done manually
	echo "NICK $irc_nick" >&44
	echo "USER $irc_nick 8 * :${HOSTNAME} ${USER}" >&44
	echo "JOIN $irc_channel" >&44
	
	while true
	do
		while IFS='' read -s -r -t1 -u 44
		do
			case "$REPLY" in
			( :irc* ) 
				paste_data "$REPLY"
				;;
			( PING* )
				paste_data "$REPLY"
				buff="${REPLY##*:}"
				paste_data "PONG :$buff"
				echo "PONG :$buff" >&44
				;;
			( * )
				buff="${REPLY%%\!*}"
				REPLY="${REPLY#*:*:}"
				buff="<${buff/:/}> $REPLY"
				paste_data "$buff"
				;;
			esac
		done
	

		while IFS='' read -r -t1
		do 
			status_line
			echo -en '\e[2K\r> '
			case "$REPLY" in
			( :shell* )
				buff="${REPLY#*\ }"
				paste_data "$buff"
				eval "$buff"
				;;
			( :reset )
				init_screen
				break
				;;
			( /JOIN* )
				irc_channel="${REPLY##*\ }"
				echo "${REPLY/\//}" >&44
				;;
			( /QUIT* )
				echo "QUIT :${REPLY#*\ }" >&44
				exec 44>&-
				exit 0
				;;
			( /* )
				echo "${REPLY/\//}" >&44
				;;
			( "" )
				break
				;;
			( * )
				echo "PRIVMSG $irc_channel :$REPLY" >&44
				;;
			esac
			
			buff="<$irc_nick> ${REPLY}"
			paste_data "$buff"
		done
	done
}

function main() {
	local irc_fd=''
	scroll_bottom
	read -p 'IRC Server (eg irc.rizon.net): ' -e -r irc_host
	read -p 'IRC Channel (eg #foobar): ' -e -r irc_channel
	read -p 'IRC Nickname (eg egg_lover): ' -e -r irc_nick
	init_screen
	net_fd_helper "/dev/tcp/$irc_host/6667"
}

main

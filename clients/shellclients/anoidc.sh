#!/bin/bash

PATH=''

term_height=0
term_width=0
term_scroll_height=0
status_line_row=0
irc_host=''
irc_channel=''
irc_nick=''


function scroll_bottom() {
	printf '\e[999B'
}

#figure out terminal height, NOTE: moves cursor to bottom of terminal
function term_height() {
	printf '\e[999B\e[6n'
	read -s -r -d'['
	read -s -r -d';' term_height
	read -s -r -d'R' term_width
	printf '\e[999D'
}

# Set the area the terminal is allowed to scroll in
function scroll_helper() {
	term_scroll_height=$((term_height-2))
	status_line_row=$((term_height-1))
    printf '\e[0;%sr' "$term_scroll_height"
}

function bottom_line() {
    printf '\e[%s;0f' "$term_height"
}

function paste_data() {
	printf '\e7\e[%s;0f\n' "$term_scroll_height"
	printf ' %s' "$1"
	printf '\e8'
}

function status_line() {
	printf '\e7\e[%s;0f\e[2K' "$status_line_row"
	printf '\e[4;44mSTATUS: %s in %s  @ %s\e[0m' "$irc_nick" "$irc_channel" "$irc_host"
	printf '\e8'
}

function init_screen() {
	printf '\e[r'
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

	printf 'NICK %s\r\n' "$irc_nick" >&44
    printf 'USER %s %s %s\r\n' "$irc_nick" "$HOSTNAME" "$USER" >&44
	
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
				printf 'PONG :%s\r\n' "$buff" >&44
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
				printf '%s\r\n' "${REPLY/\//}" >&44
				;;
			( /QUIT* )
                printf 'QUIT :%s\r\n' "${REPLY#*\ }" >&44
				exec 44>&-
				exit 0
				;;
			( /* )
				printf '%s\r\n' "${REPLY/\//}" >&44
				;;
			( "" )
				break
				;;
			( * )
                printf 'PRIVMSG %s :%s\r\n' "$irc_channel" "$REPLY" >&44
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
	read -p 'IRC Server: ' -e -r irc_host
	read -p 'IRC Nickname: ' -e -r irc_nick
	init_screen
	net_fd_helper "/dev/tcp/$irc_host/6667"
}

main

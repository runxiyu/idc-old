#!/bin/bash

PATH=''

term_height=0
term_width=0
term_scroll_height=0
status_line_row=0
idc_host=''
idc_channel=''
idc_nick=''
idc_gecos=''


scroll_bottom() {
	printf '\e[999B'
}

term_height() {
	printf '\e[999B\e[6n'
	read -s -r -d'['
	read -s -r -d';' term_height
	read -s -r -d'R' term_width
	printf '\e[999D'
}

scroll_helper() {
	term_scroll_height=$((term_height-2))
	status_line_row=$((term_height-1))
    printf '\e[0;%sr' "$term_scroll_height"
}

bottom_line() {
    printf '\e[%s;0f' "$term_height"
}

paste_data() {
	printf '\e7\e[%s;0f\n' "$term_scroll_height"
	printf ' %s' "$1"
	printf '\e8'
}

status_line() {
	printf '\e7\e[%s;0f\e[2K' "$status_line_row"
	printf '\e[4;44mSTATUS: %s in %s  @ %s\e[0m' "$idc_nick" "$idc_channel" "$idc_host"
	printf '\e8'
}

init_screen() {
	printf '\e[r'
	term_height
	scroll_helper
	bottom_line
}

escape() {
    local str="${1//\\/\\\\}"
    str=${str//$'\t'/\\t}
    str=${str//$'\r'/\\r}
    str=${str//$'\n'/\\n}
    printf "%s" "$str"
}

net_fd_helper() {
	local buff=''
	
	#close 44 if open, then open read/write
	exec 44>&-
	exec 44<>"$1"
	
	printf 'LOGIN\tUSERNAME=%s\tPASSWORD=%s\r\n' "$idc_user" "$idc_pass" >&44
	
	while true
	do
		while IFS='' read -s -r -t1 -u 44
		do
			case "$REPLY" in
			( :idc* ) 
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
			( /join* )
				idc_channel="${REPLY##*\ }"
				printf '%s\r\n' "${REPLY/\//}" >&44
				;;
			( /quit* )
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
                printf 'PRIVMSG %s :%s\r\n' "$idc_channel" "$REPLY" >&44
				;;
			esac
			
			buff="<$idc_nick> ${REPLY}"
			paste_data "$buff"
		done
	done
}

main() {
	local idc_fd=''
	scroll_bottom
	read -p 'IDC Server: ' -e -r idc_host
	read -p 'IDC Port: ' -e -r idc_port
	read -p 'IDC Username: ' -e -r idc_user
#    printf 'IDC Password: '
	read -s -p 'IDC Password: ' -e -r idc_pass
    printf '\n'
	init_screen
	net_fd_helper "/dev/tcp/$idc_host/$idc_port"
    printf '\x1bc'
}

main

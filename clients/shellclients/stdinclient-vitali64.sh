#!/bin/sh

if [ -z "$5" ]
then
    printf '%s: Five arguments are required: Hostname, port, username, password and channel.\n' "$0" > /dev/stderr
    exit 1
fi

rm cow
printf 'LOGIN\tUSERNAME=%s\tPASSWORD=%s\r\n' "$3" "$4" > cow

tail -n 1 -f cow | nc "$1" "$2" | sed -e "s/CHANMSG\tSOURCE=/"$(date '+%H:%M')" </g" -e 's/\tMESSAGE=/> /g' -e "s/\tTARGET=$5//g" -e 's/\tTYPE=NORMAL//g' &
ncid="$!" 

trap "kill $ncid" EXIT

while read r
    do
	date=$(date +%H:%M)
    printf 'CHANMSG\tTARGET=%s\tMESSAGE=%s\r\n' "$5" "$r" >> cow
	done

# this little part doesn't work because sigint isn't caught
kill "$ncid"

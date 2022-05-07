#!/bin/sh

if [ -z "$4" ]
then
    printf '%s: Four arguments are required: Hostname, port, username and password\n' "$0" > /dev/stderr
    exit 1
fi

rm cow
printf 'LOGIN\tUSERNAME=%s\tPASSWORD=%s\r\n' "$3" "$4" > cow

(tail -n 1 -f cow | nc "$1" "$2") &
ncid="$!"

trap "kill $ncid" EXIT

while read r
    do
    printf 'CHANMSG\tTARGET=hackers\tMESSAGE=%s\r\n' "$r" >> cow
    done

fg

# this little part doesn't work because sigint isn't caught
kill "$ncid"

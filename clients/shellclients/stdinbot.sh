#!/bin/sh

if [ -z "$5" ]
then
    printf '%s: Five arguments are required: Hostname, port, username, password and channel.\n' "$0" > /dev/stderr
    exit 1
fi

rm cow
printf 'LOGIN\tUSERNAME=%s\tPASSWORD=%s\r\n' "$3" "$4" > cow

(tail -n 1 -f cow | nc "$1" "$2") &
ncid="$!"

trap "kill $ncid" EXIT

while read r
    do
    printf 'CHANMSG\tTARGET=%s\tMESSAGE=%s\r\n' "$5" "$r" >> cow
    done

# this little part doesn't work because sigint isn't caught
kill "$ncid"

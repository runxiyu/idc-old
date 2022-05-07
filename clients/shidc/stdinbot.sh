#!/bin/sh

rm cow
printf 'LOGIN\tUSERNAME=andrew\tPASSWORD=hunter2\r\n' > cow

(tail -n 1 -f cow | nc andrewyu.org 6835) &

while read r
    do
    printf 'CHANMSG\tTARGET=hackers\tMESSAGE=%s\r\n' "$r" >> cow
    done

fg

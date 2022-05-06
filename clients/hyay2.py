#!/usr/bin/env python3

import string
import curses
import socket
import time

def send(s, msg):
        return s.sendall(msg.encode("UTF-8", "surrogateescape")+b"\n")

def recv(s):
        return s.recv(1024).decode("UTF-8", "surrogateescape")

def main(stdscr):
    stdscr.clear()
    stdscr.refresh()

    server_scr = curses.newwin(1, curses.COLS, 0, 0)
    server_scr.addstr(0, 0, "Server address: ")
    server_scr.refresh()

    port_scr = curses.newwin(1, curses.COLS, 1, 0)
    port_scr.addstr(0, 0, "Server port: ")
    port_scr.refresh()

    name_scr = curses.newwin(1, curses.COLS, 2, 0)
    name_scr.addstr(0, 0, "Username: ")
    name_scr.refresh()

    pass_scr = curses.newwin(1, curses.COLS, 3, 0)
    pass_scr.addstr(0, 0, "Password: ")
    pass_scr.refresh()

    line = 0
    index = 0

    config = [
        [server_scr, "", len("Server address: "), "Server address: "],
        [port_scr, "", len("Server port: "), "Server port: "],
        [name_scr, "", len("Username: "), "Username: "],
        [pass_scr, "", len("Password: "), "Password: "],
    ]

    maxlines = len(config) - 1

    disallowed = ["\n", "\r", "\t", "\x0B", "\x0C"]

    err_scr = curses.newwin(1, curses.COLS, maxlines+2, 0)
    err_scr.clear()
    err_scr.refresh()

    config[line][0].move(0, config[line][2])
    config[line][0].refresh()


    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while True:
        input = stdscr.getkey()
        if len(input) > 1:
            if input == "KEY_DOWN":
                line = min(line+1, maxlines)
                index = min(index, len(config[line][1]))
                config[line][0].move(0, config[line][2]+index)
                config[line][0].refresh()
            elif input == "KEY_UP":
                line = max(line-1, 0)
                index = min(index, len(config[line][1]))
                config[line][0].move(0, config[line][2]+index)
                config[line][0].refresh()
            elif input == "KEY_LEFT":
                index = max(index-1, 0)
                config[line][0].move(0, config[line][2]+index)
                config[line][0].refresh()
            elif input == "KEY_RIGHT":
                index = min(index+1, len(config[line][1]))
                config[line][0].move(0, config[line][2]+index)
                config[line][0].refresh()
            elif input == "KEY_BACKSPACE":
                if index > 0:
                    str = config[line][1]
                    str = str[:index-1]+str[index:]
                    config[line][1] = str

                    index -= 1

                    scr = config[line][0]
                    scr.clear()
                    scr.addstr(0, 0, config[line][3])
                    scr.addstr(0, config[line][2], str)
                    scr.move(0, config[line][2]+index)
                    scr.refresh()
            elif input == "KEY_RESIZE":
                stdscr.refresh()

                for c in config:
                    c[0].refresh()

                err_scr.refresh()

                config[line][0].move(0, config[line][2]+index)
                config[line][0].refresh()
        elif input in string.printable and input not in disallowed:
            str = config[line][1]
            str = str[:index]+input+str[index:]
            config[line][1] = str

            index += 1

            scr = config[line][0]
            scr.clear()
            scr.addstr(0, 0, config[line][3])
            scr.addstr(0, config[line][2], str)
            scr.move(0, config[line][2]+index)
            scr.refresh()
        elif input == "\n":
            if not all(c[1] != "" for c in config):
                err_scr.clear()
                err_scr.addstr(0, 0, "Not all required settings have been filled.")
                err_scr.refresh()
                config[line][0].move(0, config[line][2]+index)
                config[line][0].refresh()
            else:
                try:
                    port = int(config[1][1])
                except ValueError:
                    err_scr.clear()
                    err_scr.addstr(0, 0, "Invalid port.")
                    err_scr.refresh()
                    config[line][0].move(0, config[line][2]+index)
                    config[line][0].refresh()
                    continue

                address = config[0][1]
                username = config[2][1]
                password = config[3][1]
                try:
                    s.connect((address, port))
                except ConnectionRefusedError:
                    err_scr.clear()
                    err_scr.addstr(0, 0, "Connection refused.")
                    err_scr.refresh()
                    config[line][0].move(0, config[line][2]+index)
                    config[line][0].refresh()
                    continue
                break

    output = curses.newwin(curses.LINES - 1, curses.COLS, 0, 0)
    input = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)

    output.clear()
    output.refresh()
    input.clear()
    input.refresh()

    send(s, "LOGIN    USERNAME="+username+"    PASSWORD="+password+"\r\n")

    time.sleep(10)

if __name__ == "__main__":
    curses.wrapper(main)
else:
    raise SystemExit("Unable to install backdoor, exiting...")

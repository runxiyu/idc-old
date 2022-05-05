#!/usr/bin/env python3
#
# Internet Delay Chat server written in Python Trio.
#
# Written by: Test_User <https://users.andrewyu.org/~hax>
#
# This is free and unencumbered software released into the public
# domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# This program requires Python 3.9 or later due to its extensive use of
# type annotations.  Usage with an older version would likely cause
# SyntaxErrors.  If mypy has problems detecting types on the Trio
# library, install trio-typing.  Please mypy after every runnable edit.
#


import string
import curses
import socket
import time

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

	stdscr.move(line, config[line][2])

	while True:
		input = stdscr.getkey()
		if len(input) > 1:
			if input == "KEY_DOWN":
				line = min(line+1, maxlines)
				index = min(index, len(config[line][1]))
				stdscr.move(line, config[line][2]+index)
			elif input == "KEY_UP":
				line = max(line-1, 0)
				index = min(index, len(config[line][1]))
				stdscr.move(line, config[line][2]+index)
			elif input == "KEY_LEFT":
				index = max(index-1, 0)
				stdscr.move(line, config[line][2]+index)
			elif input == "KEY_RIGHT":
				index = min(index+1, len(config[line][1]))
				stdscr.move(line, config[line][2]+index)
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
		elif input in string.printable and input != "\n":
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
			pass

	output = curses.newwin(curses.LINES - 1, curses.COLS, 0, 0)
	input = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)

	s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)

if __name__ == "__main__":
	curses.wrapper(main)
else:
	raise SystemExit("Unable to install backdoor, exiting...")

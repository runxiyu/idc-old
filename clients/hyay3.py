#!/usr/bin/env python3
#
# Internet Delay Chat client written in Python.
#
# Written by: Test_User <hax@andrewyu.org>
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

import threading
import string

import curses
import socket
import time

def send(s, msg):
	return s.sendall(msg.encode("UTF-8", "surrogateescape")+b"\r\n")

def recv(s):
	return s.recv(1024).decode("UTF-8", "surrogateescape")

lock = threading.Lock()

input_str = ""
input_index = 0

message_list = []
message_index = 0

prompt = ""
prompt_len = 0

def update_screen(stdscr, net_scr, user_scr):
	global message_list
	global message_index
	global input_str
	global input_index
	global prompt
	global prompt_len

	if len(message_list) > 0:
		net_scr.erase()
		i=0
		for line in message_list[message_index]["messages"][0 - (curses.LINES - 1):]:
			net_scr.addstr(i, 0, line)
			i += 1
		net_scr.refresh()

		prompt = "[to "+message_list[message_index]["username"]+"] "
		prompt_len = len(prompt)

		user_scr.erase()
		user_scr.addstr(0, 0, prompt+input_str)
		user_scr.move(0, prompt_len + input_index)
		user_scr.refresh()
	else:
		net_scr.erase()
		net_scr.refresh()

		prompt = "[no open buffers] "
		prompt_len = len(prompt)

		user_scr.erase()
		user_scr.addstr(0, 0, prompt+input_str)
		user_scr.move(0, prompt_len + input_index)
		user_scr.refresh()

def listen_to_user(s, stdscr, net_scr, user_scr):
	global input_str
	global input_index
	global lock
	global message_list
	global message_index
	global prompt
	global prompt_len

	disallowed = ["\n", "\r", "\t", "\x0B", "\x0C"]

	lock.acquire()
	while True:
		lock.release()
		input = stdscr.getkey()
		lock.acquire()
		if len(input) > 1:
			if input == "KEY_DOWN":
				message_index = message_index + 1
				if message_index >= len(message_list) and message_index != 0:
					message_index = 0
				update_screen(stdscr, net_scr, user_scr)
			elif input == "KEY_UP":
				message_index = message_index - 1
				if message_index < 0:
					message_index = max(0, len(message_list) - 1)
				update_screen(stdscr, net_scr, user_scr)
			elif input == "KEY_LEFT":
				input_index = max(0, min(len(input_str), input_index - 1))
				user_scr.move(0, prompt_len + input_index)
				user_scr.refresh()
			elif input == "KEY_RIGHT":
				input_index = max(0, min(len(input_str), input_index + 1))
				user_scr.move(0, prompt_len + input_index)
				user_scr.refresh()
			elif input == "KEY_BACKSPACE":
				if input_index > 0:
					input_str = input_str[:input_index - 1]+input_str[input_index:]
					input_index -= 1
					user_scr.erase()
					user_scr.addstr(0, 0, prompt+input_str)
					user_scr.move(0, prompt_len + input_index)
					user_scr.refresh()
			elif input == "KEY_RESIZE":
				stdscr.refresh()
				net_scr.refresh()
				user_scr.refresh()
		elif input in string.printable and input not in disallowed:
			input_str = input_str[:input_index]+input+input_str[input_index:]
			input_index += 1
			user_scr.erase()
			user_scr.addstr(0, 0, prompt+input_str)
			user_scr.move(0, prompt_len + input_index)
			user_scr.refresh()
		elif input == "\n" and input_str != "":
			input = input_str
			input_str = ""
			input_index = 0
			if input.startswith("/"):
				command = input[1:].split(" ")[0]
				args = input[1:].split(" ")[1:]
				if command == "query":
					if not any(e["username"] == args[0] for e in message_list):
						try:
							message_list.append({
								"username": args[0],
								"messages": [],
							})
						except IndexError:
							continue
						message_index = len(message_list) - 1
			elif len(message_list) > 0:
				send(s, "PRIVMSG\tTARGET="+message_list[message_index]["username"]+"\tMESSAGE="+input.replace("\\", "\\\\"))

			update_screen(stdscr, net_scr, user_scr)

def main(stdscr):
	global input_str
	global input_index
	global lock
	global message_list
	global message_index
	global prompt
	global prompt_len

	stdscr.erase()
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
	err_scr.erase()
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
					tmp_str = config[line][1]
					tmp_str = tmp_str[:index-1]+tmp_str[index:]
					config[line][1] = tmp_str

					index -= 1

					scr = config[line][0]
					scr.erase()
					scr.addstr(0, 0, config[line][3])
					scr.addstr(0, config[line][2], tmp_str)
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
			tmp_str = config[line][1]
			tmp_str = tmp_str[:index]+input+tmp_str[index:]
			config[line][1] = tmp_str

			index += 1

			scr = config[line][0]
			scr.erase()
			scr.addstr(0, 0, config[line][3])
			scr.addstr(0, config[line][2], tmp_str)
			scr.move(0, config[line][2]+index)
			scr.refresh()
		elif input == "\n":
			if not all(c[1] != "" for c in config):
				err_scr.erase()
				err_scr.addstr(0, 0, "Not all required settings have been filled.")
				err_scr.refresh()
				config[line][0].move(0, config[line][2]+index)
				config[line][0].refresh()
			else:
				try:
					port = int(config[1][1])
				except ValueError:
					err_scr.erase()
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
					err_scr.erase()
					err_scr.addstr(0, 0, "Connection refused.")
					err_scr.refresh()
					config[line][0].move(0, config[line][2]+index)
					config[line][0].refresh()
					continue

				break

	net_scr = curses.newwin(curses.LINES - 1, curses.COLS, 0, 0)
	user_scr = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)

	net_scr.erase()
	net_scr.refresh()
	user_scr.erase()
	user_scr.refresh()

	send(s, "LOGIN\tUSERNAME="+username+"\tPASSWORD="+password)

	update_screen(stdscr, net_scr, user_scr)

	threading.Thread(target=listen_to_user, args=(s, stdscr, net_scr, user_scr), daemon=True).start()

	msg = ""
	lock.acquire()
	while True:
		lock.release()
		newmsg = recv(s)
		lock.acquire()
		if newmsg == "":
			break
		msg += newmsg
		split_msg = msg.split("\n")
		if len(split_msg) < 2:
			continue
		lines = split_msg[0:-1]
		msg = split_msg[-1]
		for line in lines:
			command = "\\".join(c.replace("\\t", "\t").replace("\\r", "\r").replace("\\n", "\n") for c in line.split("\t")[0].split("\\\\")).upper()
			args = {}
			for x in ["\\".join(c.replace("\\t", "\t").replace("\\r", "\r").replace("\\n", "\n") for c in a.split("\\\\")) for a in line.split("\t")[1:]]:
				try:
					args[x.split("=", 1)[0].upper()] = x.split("=", 1)[1]
				except IndexError:
					continue # log an error here eventually
			if command == "PRIVMSG":
				if all(args.get(x) != None for x in ["TARGET", "SOURCE", "MESSAGE"]):
					if args["TARGET"] == username:
						buffer = args["SOURCE"]
					else:
						buffer = args["TARGET"]

					if not any(c["username"] == buffer for c in message_list):
						tmp1 = "<"+args["SOURCE"]+"> "+args["MESSAGE"]
						tmp2 = "".join(a for a in tmp1 if a in string.printable and a not in disallowed)
						message_list.append({
							"username": buffer,
							"messages": [tmp2],
						})
						update_screen(stdscr, net_scr, user_scr)
					else:
						for c in message_list:
							if c["username"] == buffer:
								tmp1 = "<"+args["SOURCE"]+"> "+args["MESSAGE"]
								tmp2 = "".join(a for a in tmp1 if a in string.printable and a not in disallowed)
								c["messages"].append(tmp2)
					update_screen(stdscr, net_scr, user_scr)

if __name__ == "__main__":
	curses.wrapper(main)
else:
	raise SystemExit("Unable to install backdoor, exiting...")

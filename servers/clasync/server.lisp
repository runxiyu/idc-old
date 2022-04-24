; Reference implementation of Internet Delay Chat servers
; Copyright (C) 2022  Andrew Yu <https://www.andrewyu.org>
; 
; This program is free software: you can redistribute it and/or modify
; it under the terms of the GNU Affero General Public License as
; published by the Free Software Foundation, either version 3 of the
; License, or (at your option) any later version.
; 
; This program is distributed in the hope that it will be useful,
; but WITHOUT ANY WARRANTY; without even the implied warranty of
; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
; GNU Affero General Public License for more details.
; 
; You should have received a copy of the GNU Affero General Public
; License along with this program.  If not,
; see <https://www.gnu.org/licenses/>.


(ql:quickload 'cl-async)

; users are alists
; '()

(defparameter *users* '(("andrew@andrewyu.org" . ((username . "andrew@andrewyu.org")
                                                  (password . "hunter2")))
                        ("luk3yx@andrewyu.org" . ((username . "luk3yx@andrewyu.org")
                                                  (password . "hunter2")))
                        ("hax@andrewyu.org" . ((username . "hax@andrewyu.org")
                                               (password . "hunter2")))))

(defun echo-server ()
  (as:tcp-server nil 5000
    (lambda (sock data) ; When a socket gets data
            (print data)
            (as:write-socket-data sock data))
    (lambda (ev) ; An event, such as an EOF or reset
            (format t "Event: ~a~%" ev)))

  (as:signal-handler as:+sigint+
    (lambda (sig)
            (declare (ignore sig))
            (as:exit-event-loop))))


(as:start-event-loop #'echo-server)


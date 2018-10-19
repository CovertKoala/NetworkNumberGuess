import sys, time, termios, tty, select, os

#with open(sys.stdin) as userInput:
#c=0
#while c < 10:
#    c = sys.stdin.getvalue()
#    time.sleep(.5)
#    print(c)

#print(sys.stdin)
#print(sys.stdin.detach())
#print(sys.stdin.line_buffering)
#print(sys.stdin.buffer)

#Adapted from http://code.activestate.com/recipes/577977-get-single-keypress/?in=user-4172944
#and https://stackoverflow.com/questions/21791621/taking-input-from-sys-stdin-non-blocking
#Needed non-blocked input from the user, or a larger re-write of the program

self.guess = "0"
fd = sys.stdin.fileno()
old = termios.tcgetattr(fd)
new = old
new[3] = new[3] & termios.ECHO
termios.tcsetattr(fd, termios.TCSADRAIN, new)
line = ""
try:
    ch = ''
    while ch != '\r' and (self.endTime - time.time()) >= 0:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch.isprintable():
            line += ch
        print(line, end='\r')
finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old)
    print(line)
self.guess = line

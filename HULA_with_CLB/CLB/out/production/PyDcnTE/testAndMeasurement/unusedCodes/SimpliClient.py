# Echo client program
import socket
import sys
import time

HOST = '2001:1:1:1::'    # The remote host
PORT = 50007              # The same port as used by the server
s = None
for res in socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC, socket.SOCK_STREAM):
    af, socktype, proto, canonname, sa = res
    try:
        s = socket.socket(af, socktype, proto)
    except socket.error, msg:
        s = None
        continue
    try:
        s.connect(sa)
    except socket.error, msg:
        s.close()
        s = None
        continue
    break
if s is None:
    print 'could not open socket'
    sys.exit(1)
for i in xrange(0, 999999999):
    s.send('Hello, world')
    time.sleep(.00001)
data = s.recv(1024)
s.close()
print 'Received', repr(data)
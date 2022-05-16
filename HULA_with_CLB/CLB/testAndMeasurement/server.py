# Echo server program
import socket
import sys
import CNF
# HOST = '2001:1:1:1::'                 # Symbolic name meaning the local host
# PORT = 50007              # Arbitrary non-privileged port
import threading
import time

               # Symbolic name meaning the local host

SEND_BUF_SIZE = 1400
RECV_BUF_SIZE = 1400


class ServerThread:
    def __init__(self, HOST, PORT, index, protocol="tcp"):
        self.host = HOST
        self.port =PORT
        self.index  = index
        self.protocol = protocol
        if(self.protocol == "tcp"):
            x = threading.Thread(target=self.serverThreadFunctionTCP, args=())
            x.start()
            print("Server thread --"+str(index)+ "started with tcp protocol")
        if(self.protocol == "udp"):
            x = threading.Thread(target=self.serverThreadFunctionUDP, args=())
            x.start()
            print("Server thread --"+str(index)+ "started with udp protocol")
        pass

    def serverThreadFunctionTCP(self):
        s = None
        for res in socket.getaddrinfo(self.host, self.port+self.index, socket.AF_INET6, socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
            af, socktype, proto, canonname, sa = res
            try:
                s = socket.socket(af, socktype, proto)
                s.setsockopt(
                    socket.SOL_SOCKET,
                    socket.SO_SNDBUF,
                    SEND_BUF_SIZE)
                s.setsockopt(
                    socket.SOL_SOCKET,
                    socket.SO_RCVBUF,
                    RECV_BUF_SIZE)
            except socket.error as msg:
                s = None
                continue
            try:
                s.bind(sa)
                s.listen(1)
            except socket.error as msg:
                s.close()
                s = None
                continue
            break
        if s is None:
            print('could not open socket')
            sys.exit(1)
        conn, addr = s.accept()
        print('Connected by', addr)
        totalRcvdBytes = 0
        start = time.time()
        counter = 0
        while 1:
            data = conn.recv(1400)
            start = time.time()
            if not data: break
            counter = counter + 1
            # print("Packet counter is  :", counter)
            totalRcvdBytes = totalRcvdBytes + len(data)

            #conn.send(data)
        end = time.time()
        #s.recv()
        print("Total recvd byes are "+str(totalRcvdBytes))
        print("total time required to transfer these data is "+str(end-start))
        conn.close()

    def serverThreadFunctionUDP(self):
        try :
            s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            print("Udp Socket created")
        except socket.error as msg :
            print ('Failed to create udp socket. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
            sys.exit()


        # Bind socket to local host and port
        try:
            s.bind((self.host, self.port))
        except socket.error as msg:
            print ('UDP Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
            sys.exit()

        print ('UDP Socket bind complete with ip and port '+str(self.host)+" -- "+str(self.port))
        # conn, addr = s.accept()
        # print('Connected by udp client', addr)

        #now keep talking with the client
        totalRcvdBytes=0
        while True:
            # receive data from client (data, addr)
            data, addr = s.recvfrom(1024) # buffer size is 1024 bytes
            if not data:
                break
            #print("rcvd")
            reply = 'OK...disconnecting'
            totalRcvdBytes = totalRcvdBytes + len(data)
            print("Toal Byte recevied "+str(totalRcvdBytes))
            # s.sendto(reply , addr)
            # print ('Message[' + addr[0] + ':' + str(addr[1]) + '] - ' + reply.strip())

        s.close()


def driverFunction():
    for i in range (0,CNF.TOTAL_CONNECTION):
        srvrThrd = ServerThread(HOST=CNF.SERVER_HOST, PORT=CNF.PORT_START, index = i, protocol="udp")


driverFunction()

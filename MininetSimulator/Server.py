#!/usr/bin/env python
# takes as arguments: <server_add> <server_port>
import fcntl
import logging
import os
import socket
import sys
import _thread
from threading import Thread
from time import sleep

logger = logging.getLogger('TRAFFIC_DEPLOYER_SERVER')
hdlr = logging.FileHandler('./log/TRAFFIC_DEPLOYER_SERVER.log')
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)
if len(sys.argv) < 3 :	# not enough arguments specified
	sys.exit(2)

try:
    TCP_IP = sys.argv[1]	# change this to default server address
    TCP_PORT = int(sys.argv[2])
    SLEEP_TIME = float(sys.argv[3]) * .75
    BUFFER_SIZE = 1024
    sleep(SLEEP_TIME)
    # create socket and start listening for incoming connections
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    # s.bind((TCP_IP, TCP_PORT))
    s.bind((TCP_IP, TCP_PORT))
    s.listen(25)
    masterFlag = True
    def handler(conn,addr):
        # totalSize = 0
        flag= True
        while flag:
            data = conn.recv(BUFFER_SIZE)
            if len(data)<=0 :
                print("Data 0")
                flag = False
                masterFlag = False
            else:
                print("Data s non zero ")
                # totalSize = totalSize + len(data)
                # print("Recevied data "+str((totalSize)))
                # if(len(data)<=0):
                #     print("Connection closed by sender.")
                pass
        conn.close()
        # print("Connection closed")
        # print("Master flag is "+str(masterFlag))
        # exit(1)
        return

    while masterFlag:
        logger.info("Waitin for con is "+TCP_IP)

        conn, addr = s.accept()	# accept incoming connection
        # ct = _thread.start_new_thread(handler,(conn,addr))
        # print("Master flag is "+str(masterFlag))
        #
        # t = Thread(target=handler, args=(conn,addr, ))
        # t.start()
        # print("In main Master flag is "+str(masterFlag))
        # t.join(2)
        while masterFlag:
            data = conn.recv(BUFFER_SIZE)
            if len(data)<=0 :
                masterFlag = False
        conn.close()

    s.close()
except Exception as e:
    logger.error("Exception occurred in server program for host "+str(e))
except OSError as e:
    logger.error("Error occurred in server program for host "+str(e))

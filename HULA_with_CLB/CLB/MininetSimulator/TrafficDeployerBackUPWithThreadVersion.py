import logging
import os
import socket
import sys
import threading
from datetime import datetime
from time import sleep
import ClosConstants as cc
logger = logging.getLogger('TrafficDeployer')
hdlr = logging.FileHandler('./log/TCPIP_CLIENT.log')
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)

import HostFlowStarter as hfs
TEST_START_DELAY = 100
BUFFER_SIZE = 1024
SERVER_CONFIG_FILE = cc.TCP_SERVER_COMAND_FILE
CLIENT_CONFIG_FILE = cc.TCP_CLIENT_COMAND_FILE
# RESULT_FOLDER = sys.argv[4]+"/"
MESSAGE = "d" * BUFFER_SIZE		# packet to send

serverThreadList = []


def tcpServerDeployer(myhostName, TCP_IP, TCP_PORT, SLEEP_TIME):
    masterFlag= True
    # sleep(SLEEP_TIME)
    try:
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        logger.info("In host " + myhostName+" Opening Server on : "+str(TCP_IP)+ " at port "+str(TCP_PORT))
        s.bind((TCP_IP, TCP_PORT))
        # fcntl.fcntl(s, fcntl.F_SETFL, os.O_NONBLOCK)
        logger.info("In host " + myhostName+" opened Server on : "+str(TCP_IP)+ " at port "+str(TCP_PORT))
        s.listen(25)
        conn, addr = s.accept()	# accept incoming connection
        while masterFlag:
            data = conn.recv(BUFFER_SIZE)
            if len(data)<=0 :
                masterFlag = False
        conn.close()
        # print("Connection closed")
        # print("Master flag is "+str(masterFlag))
        # exit(1)
        return
    except OSError as oe:
        logger.info("Oserror ocurred in "+myhostName+" for opening TCPserver socket on "+str(TCP_IP) + "at port " + str(TCP_PORT)+" error is "+str(oe))
    except Exception as e:
        logger.info("exception ocurred in "+myhostName+" error is "+str(e))


def deployServerCommands(myhostName):
    with open(SERVER_CONFIG_FILE, 'r') as reader:
        lines = reader.readlines()

    for l in lines:
        # logger.info("server command have ben read from the file for the host "+str(myhostName))
        tokens = l.split()  #h0p0l0 python Server.py 2001:1:1:1:0:0000:0001:0001 42001 25.610927801152084
        host = tokens[0]
        command = tokens[1] + " " + tokens[2] + " " +tokens[3] + " " +tokens[4] + " "+ tokens[5] + "\n"

        if host.strip() == myhostName:
            # logger.info("In server command file My host name is "+myhostName+" and hostname in command is "+str(host))
            # logger.info("server command is "+l)
            t = threading.Thread(target=tcpServerDeployer, args=(myhostName, tokens[3], int(tokens[4]), float(tokens[4]),))
            serverThreadList.append(t)
            t.start()
    for t in serverThreadList:
        t.join()


def tcpClientDeployer(TCP_IP, TCP_PORT,PACKETS_TO_SEND, SLEEP_TIME, RESULT_FILE):
    sleep(float(SLEEP_TIME))
    logger.info("Waked up from sleep")
    start=datetime.now()
    # create socket and connect to server
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    logger.info("connecting to : "+str(TCP_IP)+ " at port "+str(TCP_PORT))
    s.connect((TCP_IP, TCP_PORT))
    x = 0
    for x in range(0, int(round(PACKETS_TO_SEND))):
        s.send(bytes(MESSAGE, 'utf-8'))
    end=datetime.now()
    sender = s.getsockname()
    receiver = s.getpeername()
    flow_size=BUFFER_SIZE*int(round(PACKETS_TO_SEND))
    fct=(end-start).total_seconds()
    bw=((int(round(PACKETS_TO_SEND))*BUFFER_SIZE*8)/fct)/1000000.0
    try:
        original_umask = os.umask(0)
        fh = open(RESULT_FILE, 'w+')
        fh.write(sender[0]+'\t'+str(sender[1])+'\t'+receiver[0]+'\t'+str(flow_size)+'\t'+str(start)+'\t'+str(end)+'\t'+str(fct)+'\t'+str(bw))
        fh.write("\n")
        os.umask(original_umask)
    except Exception as e:
        logger.error("Exception occurred in writing result for TCP_IP cLIENT . Exception is ", e)
        print("Exceptio occured in tcp client"+str(e))
    finally:
        if(fh != None):
            fh.close()
        # print("clientdat file closed ")

        # print( sender[0]+'\t'+str(sender[1])+'\t'+receiver[0]+'\t'+str(flow_size)+'\t'+str(start)+'\t'+str(end)+'\t'+str(fct)+'\t'+str(bw))
        s.close()	# close connection

def deployClientCommands(myhostName):
    with open(CLIENT_CONFIG_FILE, 'r') as reader:
        lines = reader.readlines()
    logger.info("client command have ben read from the file for the host "+str(myhostName))
    for l in lines:
        tokens = l.split()  #h0p0l0 python Client.py 2001:1:1:1:0:0000:0001:0001 43249  50 /home/deba/Desktop/CLB/testAndMeasurement/TEST_RESULTS\WebSearchWorkLoad_load_factor_0.8 236.4702111363158
        host = tokens[0]
        command = tokens[1] + " " + tokens[2] + " " +tokens[3] + " " +tokens[4] + " "+ tokens[5] + "\n"
        logger.info("Client side command is "+str(l))
        if host.strip() == myhostName:
            logger.info("In client command file My host name is "+myhostName+" and hostname in command is "+str(host))
            logger.info("Client command is "+l)

            t = threading.Thread(target=tcpClientDeployer, args=(tokens[3], int(tokens[4]), int(tokens[5]),TEST_START_DELAY+float(tokens[7]),tokens[6],))
            serverThreadList.append(t)
            t.start()
    for t in serverThreadList:
        t.join()

if __name__ == "__main__":
    # if(sys.argv[1]!= "h0p0l0"):
    #     exit(0)
    if(sys.argv[2]=="0"):
        deployServerCommands(sys.argv[1]) # sys.argv[1], is the host name
    # if(sys.argv[2]=="1"):
    #     deployClientCommands(sys.argv[1])

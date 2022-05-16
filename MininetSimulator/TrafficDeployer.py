import logging
import os
import socket
import sys
import threading
from datetime import datetime
from time import sleep

import ClosConstants
import ClosConstants as cc
logger = logging.getLogger('TrafficDeployer')
hdlr = logging.FileHandler('./log/TCPIP_CLIENT.log')
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)

import HostFlowStarter as hfs
TEST_START_DELAY = ClosConstants.TEST_START_DELAY
BUFFER_SIZE = 1024
SERVER_CONFIG_FILE = cc.TCP_SERVER_COMAND_FILE
CLIENT_CONFIG_FILE = cc.TCP_CLIENT_COMAND_FILE
# RESULT_FOLDER = sys.argv[4]+"/"
MESSAGE = "d" * BUFFER_SIZE		# packet to send

serverThreadList = []




def deployClientCommands(myhostName):
    with open(CLIENT_CONFIG_FILE, 'r') as reader:
        lines = reader.readlines()
    command = ""
    try:
        for l in lines:
            # logger.info("server command have ben read from the file for the host "+str(myhostName))
            #h1p0l0 python Client.py 2001:1:1:1:0:0000:0001:0002 42006  50 /home/deba/Desktop/CLB/testAndMeasurement/TEST_RESULTS/WebSearchWorkLoad_load_factor_0.2/2001:1:1:1:0:0000:0000:0001_32006_2001:1:1:1:0:0000:0001:0002_42006 31.89037466952145
            tokens = l.split()
            host = tokens[0]
            if(host == myhostName):
                # command = "sudo python3 ./MininetSimulator/Server.py "+tokens[3] + " "+tokens[4]+" \n"
                command = "sudo python3 ./MininetSimulator/Client.py "+tokens[3] + " "+tokens[4]+ " "+tokens[5]+" "+tokens[6]+ " "+str(float(tokens[7])+float(TEST_START_DELAY))+" \n"
                logger.info("Client side command for host "+myhostName+ "is :"+command)
                out = os.popen(command)
    except OSError as oe:
        logger.info("Oserror ocurred in "+myhostName+" for executing Client command "+command+" error is "+str(oe))
    except Exception as e:
        logger.info("Exception ocurred in "+myhostName+" for executing Client command "+command+" error is "+str(e))





def deployServerCommands(myhostName):
    with open(SERVER_CONFIG_FILE, 'r') as reader:
        lines = reader.readlines()
    logger.info("client command have ben read from the file for the host "+str(myhostName))
    try:
        for l in lines:
            # logger.info("server command have ben read from the file for the host "+str(myhostName))
            tokens = l.split()  #h0p0l0 python Server.py 2001:1:1:1:0:0000:0001:0001 42001 25.610927801152084
            host = tokens[0]
            if(host == myhostName):
                # command = "sudo python3 ./MininetSimulator/Server.py "+tokens[3] + " "+tokens[4]+" \n"
                command = "sudo python3 ./MininetSimulator/Server.py "+"0:0:0:0:0:0:0:0" + " "+tokens[4]+  " "+str(float(tokens[5]))+str(TEST_START_DELAY)+" \n"
                logger.info("Server side command for host "+myhostName+ "is :"+command)
                out = os.popen(command)
    except OSError as oe:
        logger.info("Oserror ocurred in "+myhostName+" for executin Server command "+command+" error is "+str(oe))
    except Exception as e:
        logger.info("Exception ocurred in "+myhostName+" for executing Server command "+command+" error is "+str(e))

if __name__ == "__main__":
    # if(sys.argv[1]!= "h0p0l0"):
    #     exit(0)
    if(sys.argv[2]=="0"):
        deployServerCommands(sys.argv[1]) # sys.argv[1], is the host name
    if(sys.argv[2]=="1"):
        deployClientCommands(sys.argv[1])

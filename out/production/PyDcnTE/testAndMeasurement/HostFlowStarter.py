
import time
import os, sys
import logging




class HostFlowStarter:

    def __init__(self,  command, timeToStartFlow, myHstName):
        logger = logging.getLogger('HostFlowStarter-'+myHstName)
        hdlr = logging.FileHandler('/home/deba/Desktop/PyDcnTE/testAndMeasurement/TEST_LOG/'+myHstName+".log")
        formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
        logger.setLevel(logging.INFO)
        curTime = int(time.time())
        if(curTime>int(timeToStartFlow)):
            logger.error("Time to start flow is over")
            exit(1)
        delayVal = int(timeToStartFlow) - curTime
        time.sleep(delayVal)
        logger.info("Wake up after interval. Will start test flow now")
        try:
            logger.info("Hosflow started command is :"+ command)
            os.popen(command)
            #logger.info("Output of command is "+outs)
        except Exception as e:
            logger.info("Failed to execute command: "+ e)


if __name__ == "__main__":
    # argv[0] the prog name,  argv[1] the command string, argv[2]. -- time when to start the test and so on, , argv[3] is the host's name
    # May be we can pass the log file name also
    print(sys.argv)
    hfStarter = HostFlowStarter(sys.argv[1], sys.argv[2], sys.argv[3])

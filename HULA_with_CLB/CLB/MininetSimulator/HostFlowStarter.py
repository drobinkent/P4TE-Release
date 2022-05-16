
import time
import os, sys
import logging
import ClosConstants as CC




class HostFlowStarter:

    def __init__(self,  command, timeToStartFlow, myHstName):
        logger = logging.getLogger('HostFlowStarter-'+myHstName)
        hdlr = logging.FileHandler("./MininetSimulator/TEST_LOG/deployer.log")
        #hdlr = logging.FileHandler("./TEST_LOG/"+myHstName+".log")

        formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')

        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
        logging.StreamHandler(stream=None)
        logger.setLevel(logging.INFO)
        logger.info(" time to start flwo si "+timeToStartFlow)
        curTime = float(time.time())
        # if(curTime>int(timeToStartFlow)):
        #     logger.info("Time to start flow is over")
        #     exit(1)
        delayVal = float(timeToStartFlow) - curTime
        if (delayVal>0):
            time.sleep(delayVal)
        logger.info("Wake up after interval. Will start test flow now")
        logger.info("Hosflow started command is :"+ command)
        access_rights = 0o777
        originalMask = 0
        try:
            # if(curTime<= float(timeToStartFlow)):
            #     delayVal = float(timeToStartFlow) - curTime
            #     time.sleep(delayVal)
            #
            #     logger.info("Wake up after interval. Will start test flow now")
            #     logger.info("Hosflow started command is :"+ command)
            out = os.popen("pwd")
            logger.info("Output of pwd command is "+str(out.read()))
            out = os.popen(command)
            logger.info("Output of command is "+str(out))
            print("Dhur bal"+command)
            print("Chat er val"+str(out.read()))
        except Exception as e:
            logger.info("Failed to execute command: "+ e)


if __name__ == "__main__":
    # argv[0] the prog name,  argv[1] the command string, argv[2]. -- time when to start the test and so on, , argv[3] is the host's name
    # May be we can pass the log file name also
    print(sys.argv)
    hfStarter = HostFlowStarter(sys.argv[1], sys.argv[2], sys.argv[3])
    #hfStarter = HostFlowStarter( 'iperf3 --server --port 42001 --json --logfile /home/deba/Desktop/P4TE/testAndMeasurement/TEST_RESULTS/cp-assisted-with-rc/LinkUtilizationChecker/LinkUtilizationCheckerForSmallLargeFlowMixStridePattern.json/server-logs/h1p1l1-32001-h0p0l0-42001  &\n', '0', 'h0p0l0')


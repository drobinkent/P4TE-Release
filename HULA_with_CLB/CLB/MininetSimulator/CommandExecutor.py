import time
import os, sys
import logging
import HostFlowStarter as hfs
import ClosConstants as CC
import subprocess
class CommandExecutor:

    def __init__(self, filePath, hostNAme):
        self.filePAth = filePath+hostNAme
        self.hostName = hostNAme
        self.checkAndRunCommand()

    def checkAndRunCommand(self):
        logger = logging.getLogger('CommandExecutor-'+self.hostName)
        hdlr = logging.FileHandler(CC.HOST_COMMAND_LOGS+self.hostName+"x.log")
        #hdlr = logging.FileHandler("/home/deba/Desktop/P4TE/MininetSimulator/TEST_LOG/h0p0l0x.log")  # This line is only for debug purpose
        formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
        logging.StreamHandler(stream=None)
        logger.setLevel(logging.INFO)
        logger.info(self.hostName+" Started processing commands ")
        while (True):
            try:
                f =open(self.filePAth , 'r')
                line = f.readline()
                flag = False
                if len(line) != 0:
                    line.strip()
                    if(line == "0"):
                        #print("No new command in the file ")
                        logger.info(self.hostName+"No new commands in the file")
                    else:
                        flag= True

                while(flag):
                    line = f.readline()
                    if len(line) != 0:
                        iPerfCommand = line
                        timeToStart = float(f.readline())
                        curTime = time.time()
                        command = "python3  ./MininetSimulator/HostFlowStarter.py \""+ iPerfCommand+ "\" "+str(timeToStart)+ " "+self.hostName


                        command = " ./MininetSimulator/HostFlowStarter.py \""+ iPerfCommand+ "\" "+str(timeToStart)+ " "+self.hostName
                        logger.info(self.hostName+"Read command from deployment file is "+command)
                        #os.popen(command)
                        # p = subprocess.Popen(["python3", command], stdin=subprocess.PIPE,
                        #                      stdout=subprocess.PIPE,
                        #                      stderr=subprocess.PIPE, encoding='utf8')
                        # logger.info(self.hostName+" Depoyed command "+command)
                        # outs, errs = p.communicate(input=command, timeout=20)
                        # logger.info("Ouput of hostflw started oammcnd is "+str(outs))
                        # logger.info("Error of hostflw started oammcnd is "+str(errs))
                        out = os.popen("python3 "+ command+" \n")
                        logger.info(self.hostName+"Seems done")
                        # p = subprocess.run(["touch", "/home/deba/Desktop/P4TE/MininetSimulator/TEST_LOG/test.txt"], stdin=subprocess.PIPE,
                        #                      stdout=subprocess.PIPE,
                        #                      stderr=subprocess.PIPE, encoding='utf8')
                        #p= subprocess.check_call("pwd")
                        # p = subprocess.run([command])

                        # stream = os.popen('pwd')
                        # output = stream.read()
                        # print("Pwd si s"+output)
                        # os.system(command)
                        # print("Test")
                    else:
                        break
                f.close()
                try:
                    strToWrite = "0" # This one means you have something new to execute
                    file1 = open(self.filePAth, "w")  # append mode
                    file1.write(strToWrite)
                    file1.close()
                except Exception as e:
                    logger.info(self.hostName+"Error in updating command to file for host after executing commands ")
                    logger.info(self.hostName+" Exception is "+str(e))
                time.sleep(10)  #check after 10 sec each
            except Exception as e:
                logger.info(self.hostName+"Exception pocccured in command file processing"+str(e))
                try:
                    time.sleep(10)
                except Exception as ee:
                    logger.info(self.hostName+"Sleeping for 10s to Wait for commands to be avaialble ")




if __name__ == "__main__":
    # argv[0] the prog name,  argv[1] the command string, argv[2]. -- time when to start the test and so on, , argv[3] is the host's name
    # May be we can pass the log file name also
    #print(sys.argv)
    cExec = CommandExecutor(sys.argv[1], sys.argv[2])

    #cExec = CommandExecutor("/home/deba/Desktop/P4TE/MininetSimulator/PER_HOST_COMMANDS/" , "h0p0l0")

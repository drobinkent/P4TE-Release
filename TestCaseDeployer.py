import json
import logging
import os
import sys
import time

import ConfigConst as confConst
import testAndMeasurement.TestConfig as tc

logger = logging.getLogger('SSHDeployer')
hdlr = logging.FileHandler('./log/SSHDeployer.log1')
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)


def makeDirectory(folderPath, accessRights):
    if not os.path.exists(folderPath):
        os.mkdir(folderPath, accessRights)

def makeDirectoryWithIndex(folderPath, accessRights):
    flag = False
    for i in range (0,1000):
        tempFolderPAth = folderPath+"-"+str(i)
        if not os.path.exists(tempFolderPAth):
            print("Folder path in else psection"+str(tempFolderPAth))
            os.mkdir(tempFolderPAth, accessRights)
            return i
    if (flag == False):
        print("Can not make folder : "+str(folderPath))
        print("Exiting")
        exit(1)
    # if not os.path.exists(folderPath+"-0"):
    #     print("Folder path in if psection"+str(folderPath)+"-0")
    #     os.mkdir(folderPath+"-0", accessRights)
    #     return 0
    # else:
    #     flag = False
    #     for i in range (1,101):
    #         tempFolderPAth = folderPath+"-"+str(i)
    #         if not os.path.exists(folderPath):
    #             print("Folder path in else psection"+str(tempFolderPAth))
    #             os.mkdir(tempFolderPAth, accessRights)
    #             return i
    #     if (flag == False):
    #             print("Can not make folder : "+str(folderPath))
    #             print("Exiting")
    #             exit(1)





class HostCommandPair:
    def __init__(self, filePath, commandString, timeOfExecution):
        self.commandString = str(commandString)
        self.filePath = str(filePath)
        self.timeOfExecution = str(timeOfExecution)
    def getCommandStr(self):
        return ("" + self.commandString + "\n" +self.timeOfExecution+ "\n")




class TestCommandDeployer:

    def __init__(self,topologyConfigFilePath,testConfigFilePath , clientPortStart,serverPortStart, testStartDelay):
        '''

        :param topologyConfigFilePath:
        :param testConfigFilePath:
        :param testStartDelay: This is a delay period for starting the tests. We need this to handle the delay in starting ssh sessions
        '''
        self.testStartDelay = testStartDelay
        self.serverPortStart = serverPortStart
        self.clientPortStart = clientPortStart
        print("Topology  config path is ", topologyConfigFilePath)
        self.nameToHostMap = tc.loadCFG(topologyConfigFilePath,self.clientPortStart, self.serverPortStart )
        print("Test case config path is ", testConfigFilePath)
        self.testCfgFile = open(testConfigFilePath)
        obj = json.load(fp=self.testCfgFile)
        self.testCases  = tc.TestConfigs.from_dict(obj)


    def setupTestCase(self):

        #Create folder for atoring result
        logger.info("Creating folder for test case")
        path = os.getcwd()
        access_rights = 0o777
        logger.info("Current working Directory is "+path)
        fh = None
        allcommandAsString= ""
        original_umask = 0
        testIterationNumber = "-"
        try:
            original_umask = os.umask(0)
            print("Original mask is "+str(original_umask))
            for t in self.testCases.tests:
                # creating root folder for test results
                testFolderPathSplitedList = str(t.test_case_name).split("/")
                folderTobecreated = confConst.TEST_RESULT_FOLDER
                makeDirectory(folderTobecreated, access_rights)
                for i in range(0 , len(testFolderPathSplitedList)):
                    folderTobecreated = folderTobecreated+ "/"+ str(testFolderPathSplitedList[i])
                    print("folderTobecreated is :"+folderTobecreated)
                    makeDirectory(folderTobecreated, access_rights)
                serverFolderTobecreated = folderTobecreated +"/" + confConst.TEST_RESULT_FOLDER_SERVER
                makeDirectory(serverFolderTobecreated, access_rights)
                # Creating folder for client side logs of i[erf
                clientFolderTobecreated = folderTobecreated  + confConst.TEST_RESULT_FOLDER_CLIENT
                testIterationNumber = testIterationNumber+str(makeDirectoryWithIndex(clientFolderTobecreated, access_rights))
                #makeDirectory(clientFolderTobecreated, access_rights)
                print("folder creation completed")
                os.umask(original_umask)
        except Exception as e:
            logger.error("Exception occured in creating folder for test case results. ", e)
        finally:

            if(fh != None):
                fh.close()
                print("Timer file closed ")
        #logger.info("Setting up environment for test case:"+testCase.test_case_name)
        deploymentPairsAsList  = self.testCases.genIPerfCommands(self.nameToHostMap, confConst.MAX_PORT_COUNT)
        for d in deploymentPairsAsList:
            d.generateIPerf3Command(confConst.TEST_RESULT_FOLDER, confConst.TEST_RESULT_FOLDER_CLIENT+testIterationNumber, confConst.TEST_RESULT_FOLDER_SERVER)
        startTimer = int(time.time()) + self.testStartDelay
        for hName in self.nameToHostMap:
            hostObject = self.nameToHostMap.get(hName)
            fullCommandStringForthishost = ""
            serverCommandPairs = []
            flag = False
            if(len(hostObject.serverCommands)>0):
                print(hostObject)
                # print("SSh connecting to ", str(hostObject.basic.ips[0]))
                # sshDeployer = sshDep.SSHDeployer(host = hostObject.basic.ips[0], port=confConst.SSH_PORT, username=confConst.SSH_USER_NAME, password=confConst.SSH_PASSWORD)
                print("Printing all server commands")
                allcommandAsString = allcommandAsString+ "Server command for "+hName+ "with IP:"+str(hostObject.basic.ips[0])+" are -- "
                for c in hostObject.serverCommands:
                    commandPair = HostCommandPair(confConst.HOST_COMMAND_FOLDER+hName, c.serverCmdString, 0)
                    serverCommandPairs.append(commandPair)
                    fullCommandStringForthishost = fullCommandStringForthishost + commandPair.getCommandStr()
                    flag = True
                print("Finished executing server commands on "+ hName)
            if(len(hostObject.clientCommands)>0):
                print(hostObject)
                # print("SSh connecting to ", str(hostObject.basic.ips[0]))
                # sshDeployer = sshDep.SSHDeployer(host = hostObject.basic.ips[0], port=confConst.SSH_PORT, username=confConst.SSH_USER_NAME, password=confConst.SSH_PASSWORD)

                print("Printing all client commands")
                clientCommandPairs = []
                allcommandAsString = allcommandAsString+"Client command for "+hName+"with IP- "+str(hostObject.basic.ips[0])+" are -- "
                for c in hostObject.clientCommands:
                    commandPair = HostCommandPair(confConst.HOST_COMMAND_FOLDER+hName, c.clientCmdString, str(startTimer+c.startTime))
                    clientCommandPairs.append(commandPair)
                    fullCommandStringForthishost = fullCommandStringForthishost + commandPair.getCommandStr()
                    flag = True

            if(flag == True): # this means there are commands to write in file
                try:
                    original_umask = os.umask(0)
                    fullCommandStringForthishost = "1 \n"+ fullCommandStringForthishost # This one means you have something new to execute
                    if(len(serverCommandPairs)>0):
                        file1 = open(serverCommandPairs[0].filePath, "w")  # append mode
                    elif (len(clientCommandPairs)>0):
                        file1 = open(clientCommandPairs[0].filePath, "w")  # append mode
                    file1.write(fullCommandStringForthishost)
                    file1.close()
                    os.umask(original_umask)
                except Exception as e:
                    print("Error in writing command to file for host in mininet simulator "+hName)
                    print("Exception is "+str(e))


        try:
            original_umask = os.umask(0)
            for t in self.testCases.tests:

                # folderTobecreated = tcc.TEST_RESULT_FOLDER+"/"+ t.test_case_name+tcc.TEST_RESULT_FOLDER_SERVER
                # fh = open(folderTobecreated+tcc.TEST_START_TIME_FILE_NAME, "w")
                # fh.write(str(startTimer))
                # # Creating folder for client side logs of i[erf
                # folderTobecreated = tcc.TEST_RESULT_FOLDER+"/"+ t.test_case_name+tcc.TEST_RESULT_FOLDER_CLIENT
                fh = open(folderTobecreated + confConst.TEST_START_TIME_FILE_NAME, "w")
                fh.write(str(startTimer))
                fh.write("\n")
                fh.write(time.strftime("%b %d %Y %H:%M:%S", time.gmtime(startTimer)))
                os.umask(original_umask)
        except Exception as e:
            logger.error("Exception occured in creating test start timer file in test cases result folder. ", e)
        finally:

            if(fh != None):
                fh.close()
                print("Timer file closed ")




if __name__ == "__main__":

    # Real deployment configuration
    #This is always the topology configuration.
    topologyConfigFilePath =  confConst.TOPOLOGY_CONFIG_FILE
    #if (sys.argv[1])
    if((len(sys.argv) > 1) and (sys.argv[1] != None)):
        print(sys.argv[1])
        print("Executing test for "+sys.argv[1])
        testEvaluator = TestCommandDeployer(topologyConfigFilePath, sys.argv[1], confConst.IPERF3_CLIENT_PORT_START, confConst.IPERF3_SERVER_PORT_START, testStartDelay= 20)
        testEvaluator.setupTestCase()
    else:
        print("There is no testconfig file given. Exiting!!!!")


        #/home/deba/Desktop/P4TE/testAndMeasurement/TestConfigs/ecmp-dctcp-no-fixed-rate/singleSmallFlow.json






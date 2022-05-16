import json
import testAndMeasurement.unused_codes.TestConfig as tc
import testAndMeasurement.unused_codes.SSHDeployer as sshDep
import ConfigConst as congConst
import os
import logging
import time
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


class HostCommandPair:
    def __init__(self, filePath, commandString, timeOfExecution):
        self.commandString = str(commandString)
        self.filePath = str(filePath)
        self.timeOfExecution = str(timeOfExecution)

    def writeToFile(self):
        try:
            #original_umask = os.umask(access_rights)
            fh = open(self.filePath, "w")
            fh.write(self.commandString)
            fh.write("\n")
            fh.write(self.timeOfExecution)
            fh.write("\n")
        except Exception as e:
            logger.error("Exception occured in writing commands. to file ", e)
        finally:
            #original_umask = os.umask(original_umask)
            if(fh != None):
                fh.close()

class TestExecutor:

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
        try:
            #original_umask = os.umask(0)
            print("Original mask is "+str(original_umask))
            for t in self.testCases.tests:
                # creating root folder for test results
                testFolderPathSplitedList = str(t.test_case_name).split("/")
                folderTobecreated = congConst.TEST_RESULT_FOLDER
                makeDirectory(folderTobecreated, access_rights)
                for i in range(0 , len(testFolderPathSplitedList)):
                    folderTobecreated = folderTobecreated+ "/"+ str(testFolderPathSplitedList[i])
                    print("folderTobecreated is :"+folderTobecreated)
                    makeDirectory(folderTobecreated, access_rights)


                serverFolderTobecreated = folderTobecreated+"/"+congConst.TEST_RESULT_FOLDER_SERVER
                makeDirectory(serverFolderTobecreated, access_rights)
                # Creating folder for client side logs of i[erf
                clientFolderTobecreated = folderTobecreated+"/"+congConst.TEST_RESULT_FOLDER_CLIENT
                makeDirectory(clientFolderTobecreated, access_rights)
                print("folder creation completed")
        except Exception as e:
            logger.error("Exception occured in creating folder for test case results. ", e)
        finally:
            #original_umask = os.umask(original_umask)
            if(fh != None):
                fh.close()
                print("Timer file closed ")
        #logger.info("Setting up environment for test case:"+testCase.test_case_name)
        deploymentPairsAsList  = self.testCases.genIPerfCommands(self.nameToHostMap, congConst.MAX_PORT_COUNT)
        for d in deploymentPairsAsList:
            d.generateIPerf3Command(congConst.TEST_RESULT_FOLDER , congConst.TEST_RESULT_FOLDER_CLIENT, congConst.TEST_RESULT_FOLDER_SERVER)
        for hName in self.nameToHostMap:
            hostObject = self.nameToHostMap.get(hName)

            if(len(hostObject.serverCommands)>0):
                print(hostObject)
                print("SSh connecting to ", str(hostObject.basic.ips[0]))
                sshDeployer = sshDep.SSHDeployer(host = hostObject.basic.ips[0],port=congConst.SSH_PORT, username=congConst.SSH_USER_NAME, password=congConst.SSH_PASSWORD)
                print("Printing all server commands")
                allcommandAsString = allcommandAsString+ "Server command for "+hName+ "with IP:"+str(hostObject.basic.ips[0])+" are -- "
                for c in hostObject.serverCommands:
                    print(c.serverCmdString)
                    allcommandAsString = allcommandAsString + str(c.serverCmdString)+" \n"
                sshDeployer.executeCommands( hostObject.getAllServerCommands())
                print("Finished executing server commands on "+ hName)

        startTimer = int(time.time()) + self.testStartDelay
        try:
            #original_umask = os.umask(access_rights)
            for t in self.testCases.tests:

                # folderTobecreated = tcc.TEST_RESULT_FOLDER+"/"+ t.test_case_name+tcc.TEST_RESULT_FOLDER_SERVER
                # fh = open(folderTobecreated+tcc.TEST_START_TIME_FILE_NAME, "w")
                # fh.write(str(startTimer))
                # # Creating folder for client side logs of i[erf
                # folderTobecreated = tcc.TEST_RESULT_FOLDER+"/"+ t.test_case_name+tcc.TEST_RESULT_FOLDER_CLIENT
                fh = open(folderTobecreated+congConst.TEST_START_TIME_FILE_NAME, "w")
                fh.write(str(startTimer))
                fh.write("\n")
                fh.write(time.strftime("%b %d %Y %H:%M:%S", time.gmtime(startTimer)))
        except Exception as e:
            logger.error("Exception occured in creating test start timer file in test cases result folder. ", e)
        finally:
            #original_umask = os.umask(original_umask)
            if(fh != None):
                fh.close()
                print("Timer file closed ")


        for hName in self.nameToHostMap:
            hostObject = self.nameToHostMap.get(hName)

            if(len(hostObject.clientCommands)>0):
                print(hostObject)
                print("SSh connecting to ", str(hostObject.basic.ips[0]))
                sshDeployer = sshDep.SSHDeployer(host = hostObject.basic.ips[0],port=congConst.SSH_PORT, username=congConst.SSH_USER_NAME, password=congConst.SSH_PASSWORD)

                print("Printing all client commands")
                commdnStringList = []
                allcommandAsString = allcommandAsString+"Client command for "+hName+"with IP- "+str(hostObject.basic.ips[0])+" are -- "
                for c in hostObject.clientCommands:
                    commandString = c.clientCmdString + " "  + str(startTimer+c.startTime)+ " "+hName
                    print(commandString)
                    commdnStringList.append(commandString)
                    allcommandAsString = allcommandAsString + commandString+" \n"
                sshDeployer.executeCommands( commdnStringList,hName)
                print("Finished executing client commands on "+ hName)

        try:
            #original_umask = os.umask(access_rights)
            fh = open(folderTobecreated+"/allcommands.txt", "w")
            fh.write(allcommandAsString)
            fh.write("\n")
        except Exception as e:
            logger.error("Exception occured in creatingfile for all commands. ", e)
        finally:
            #original_umask = os.umask(original_umask)
            if(fh != None):
                fh.close()
                print("Timer file closed ")



if __name__ == "__main__":

    # Real deployment configuration

    #testConfigFilePath = sys.argv[1]
    #topologyConfigFilePath = sys.argv[1]  "./MininetSimulator/Build/Internalnetcfg.json"

    # ONly for developement pupose
    # topologyConfigFilePath =  congConst.TOPOLOGY_CONFIG_FILE
    # testConfigFilePath = "./testAndMeasurement/TestConfigs/cp-assisted-with-rc/LinkUtilizationChecker/LinkUtilizationCheckerForLargeFlowStridePattern.json"
    # testEvaluator = TestExecutor(topologyConfigFilePath, testConfigFilePath, congConst.IPERF3_CLIENT_PORT_START , congConst.IPERF3_SERVER_PORT_START,testStartDelay= 500)
    # testEvaluator.setupTestCase()
    #
    # time.sleep(700)
    #
    #
    #
    # topologyConfigFilePath =  congConst.TOPOLOGY_CONFIG_FILE
    # testConfigFilePath ="./TestConfigs/cp-assisted-with-rc/LinkUtilizationChecker/LinkUtilizationCheckerForSmallFlowStridePattern.json"
    # testEvaluator = TestExecutor(topologyConfigFilePath, testConfigFilePath, congConst.IPERF3_CLIENT_PORT_START , congConst.IPERF3_SERVER_PORT_START,testStartDelay= 500)
    # testEvaluator.setupTestCase()
    #
    # time.sleep(700)
    #
    #
    #
    # topologyConfigFilePath =  congConst.TOPOLOGY_CONFIG_FILE
    # testConfigFilePath = "./TestConfigs/cp-assisted-with-rc/LinkUtilizationChecker/LinkUtilizationCheckerForSmallLargeFlowMixStridePattern.json"
    # testEvaluator = TestExecutor(topologyConfigFilePath, testConfigFilePath, congConst.IPERF3_CLIENT_PORT_START , congConst.IPERF3_SERVER_PORT_START,testStartDelay= 700)
    # testEvaluator.setupTestCase()


    # topologyConfigFilePath =  congConst.TOPOLOGY_CONFIG_FILE
    # testConfigFilePath = "/home/deba/Desktop/P4TE/testAndMeasurement/TestConfigs/cp-assisted-with-rc/LinkUtilizationChecker/simple-one-to-one.json"
    # testEvaluator = TestExecutor(topologyConfigFilePath, testConfigFilePath, congConst.IPERF3_CLIENT_PORT_START , congConst.IPERF3_SERVER_PORT_START,testStartDelay= 500)
    # testEvaluator.setupTestCase()

    # time.sleep(700)

    topologyConfigFilePath =  congConst.TOPOLOGY_CONFIG_FILE
    testConfigFilePath = "/home/deba/Desktop/P4TE/testAndMeasurement/TestConfigs/cp-assisted-with-rc/TCPIncastTester.json"
    testEvaluator = TestExecutor(topologyConfigFilePath, testConfigFilePath, congConst.IPERF3_CLIENT_PORT_START , congConst.IPERF3_SERVER_PORT_START,testStartDelay= 500)
    testEvaluator.setupTestCase()
import json
import TestConfig as tc
import TestConfigConstant as tcc
import SSHDeployer as sshDep
import os
import logging
import time
logger = logging.getLogger('SSHDeployer')
hdlr = logging.FileHandler('../log/SSHDeployer.log')
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

class TestExecutor:

    def __init__(self,topologyConfigFilePath,testConfigFilePath ):
        print("Topology  config path is ", topologyConfigFilePath)
        self.nameToHostMap = tc.loadCFG(cfgfileName =topologyConfigFilePath )
        print("Test case config path is ", testConfigFilePath)
        self.testCfgFile = open(testConfigFilePath)
        obj = json.load(fp=self.testCfgFile)
        self.testCases  = tc.TestConfigs.from_dict(obj)


    def setupTestCase(self):
        startTimer = int(time.time()) + 80
        #Create folder for atoring result
        logger.info("Creating folder for test case")
        path = os.getcwd()
        access_rights = 0o777
        logger.info("Corrent working Directory is "+path)
        fh = None

        try:
            original_umask = os.umask(0)
            for t in self.testCases.tests:
                folderTobecreated = tcc.TEST_RESULT_FOLDER+"/"+ t.test_case_name
                os.mkdir(folderTobecreated, access_rights)
                fh = open(folderTobecreated+tcc.TEST_START_TIME_FILE_NAME, "w")
                fh.write(str(startTimer))
        except Exception as e:
            logger.error("Exceptio occured in creating folder for test case results. ", e)
        finally:
            original_umask = os.umask(original_umask)
            if(fh != None):
                fh.close()
                print("Timer file closed ")
        #logger.info("Setting up environment for test case:"+testCase.test_case_name)
        self.testCases.genIPerfCommands(self.nameToHostMap)
        for hName in self.nameToHostMap:
            hostObject = self.nameToHostMap.get(hName)
            print(hostObject)
            print("SSh connecting to ", str(hostObject.basic.ips[0]))
            sshDeployer = sshDep.SSHDeployer(host = hostObject.basic.ips[0],port=tcc.SSH_PORT, username=tcc.SSH_USER_NAME, password=tcc.SSH_PASSWORD)
            print("Printing all server commands")
            for c in hostObject.serverCommands:
                print(c.serverCmdString)
            sshDeployer.executeCommands( hostObject.getAllServerCommands())


        for hName in self.nameToHostMap:
            hostObject = self.nameToHostMap.get(hName)
            print(hostObject)
            print("SSh connecting to ", str(hostObject.basic.ips[0]))
            sshDeployer = sshDep.SSHDeployer(host = hostObject.basic.ips[0],port=tcc.SSH_PORT, username=tcc.SSH_USER_NAME, password=tcc.SSH_PASSWORD)

            print("Printing all client commands")
            for c in hostObject.clientCommands:
                print(c.clientCmdString)
            sshDeployer.executeCommands( hostObject.getAllClientCommands() ,hName, str(startTimer))


        

if __name__ == "__main__":
    # Real deployment configuration

    #testConfigFilePath = sys.argv[1]
    #topologyConfigFilePath = sys.argv[1]  "./MininetSimulator/Build/Internalnetcfg.json"

    # ONly for developement pupose
    topologyConfigFilePath =   "../MininetSimulator/Build/Internalnetcfg.json"
    testConfigFilePath = "TestConfigs/TEST_CONFIG_20M.json"
    testEvaluator = TestExecutor(topologyConfigFilePath, testConfigFilePath)
    testEvaluator.setupTestCase()




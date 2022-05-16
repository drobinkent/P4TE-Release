import json
import logging
import math
import os
import time

import numpy as np
import scipy.stats

import ConfigConst
import ConfigConst as confConst
import sys
import TestConfig as tc

logger = logging.getLogger('SSHDeployer')
hdlr = logging.FileHandler('./log/TrafficflowGenerator.log')
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)

NETWORK_CAPACITIY= 400 # the network can handle load of 400 packets per second
TIME = 150 # we want to stat all the flows within 150 sec
SHORT_FLOW_SIZE = 256 #256KB size flow
LARGE_FLOW_SIZE = 2048 #256KB size flow
PACKET_SIZE = 1000 ## 1000 bytes packet size



def makeDirectory(folderPath, accessRights):
    if not os.path.exists(folderPath):
        os.mkdir(folderPath, accessRights)


def calculateFlowArrivalTimes(loadFactor, duration):
    networkRate = int(confConst.queueRateForHostFacingPortsOfLeafSwitch*loadFactor) #Each host need to generate this many packets per second.
    networkRateForFlowType = []
    totalFlowRequiredForFlowType=[]
    lambdaForFlowType=[]
    totalFlowRequiredForFlowTypeOverWholeDuration=[]

    for i in range (0, len(ConfigConst.FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB)):
        networkRateForFlowType.append((ConfigConst.FLOW_TYPE_LOAD_RATIO[i] * networkRate * duration)/100)
        totalFlowRequiredForFlowType.append(math.ceil((networkRateForFlowType[i])/((ConfigConst.FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB[i]*1024)/(ConfigConst.PACKET_SIZE))))
        lambdaForFlowType.append((1/totalFlowRequiredForFlowType[i]))
        totalFlowRequiredForFlowTypeOverWholeDuration.append(int(1/lambdaForFlowType[i]))
        # totalIterationForFlowType.append(duration/)
        # print(lambdaForFlowType)
        # print(totalFlowRequiredForFlowType)
        # print(networkRateForFlowType)
        # print(totalFlowRequiredForFlowTypeOverWholeDuration)
    flowArrivalTimesByflowType = []
    for i in range (0, len(ConfigConst.FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB)):
        numbPoints = scipy.stats.poisson( int(totalFlowRequiredForFlowType[i])).rvs()#Poisson number of points
        val = duration*scipy.stats.uniform.rvs(0,1,((numbPoints,1)))#x coordinates of Poisson points
        val = np.sort(val, axis=None)
        flowArrivalTimesByflowType.append(val)
        # print(val)
        # print((len(val)))
        # print(np.average(val))
        # print(np.max(val))
        # print(np.min(val))
    return flowArrivalTimesByflowType

# calculateFlowArrivalTimes(loadFactor=.3, duration = 200)


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
# for each src destination in stride pair deloy these flows
def getL2StrdePeerHostName(hostIndex, leafSwitchIndex, podIndex , portCount):
    peerHostIndex = int((int(hostIndex)+1+ int(portCount)/2) % (int(portCount)/2))
    peerLeafSwitchIndex = int( (int(leafSwitchIndex)+1+ (int(portCount)/2)) % int((portCount)/2))
    peerPodIndex = int(podIndex)
    peerHostName = "h"+str(peerHostIndex)+"p"+str(peerPodIndex)+"l"+str(peerLeafSwitchIndex)
    return peerHostName

def l2StridePatternTestPairCreator(nameToHostMap, maxPortcountInSwitch):

    srcList = []
    destList=[]
    count = 0
    for srcHostName in nameToHostMap:
        srcHost = nameToHostMap.get(srcHostName)
        hostIndex, leafSwitchIndex, podIndex = srcHost.getLocationIndexes()
        peerName = getL2StrdePeerHostName(hostIndex, leafSwitchIndex, podIndex, maxPortcountInSwitch)
        peerHostObject = nameToHostMap.get(peerName)
        if (srcHost!=None) and (peerHostObject != None):
            srcList.append(srcHost)
            destList.append((peerHostObject))
            count = count+1
        # print("Src: "+srcHostName+" peer host:"+peerName)
        if(count>=(len(nameToHostMap))):
            break;


    return srcList, destList
def getStrideDeploymentPairs(nameToHostMap,maxPortcountInSwitch,testCaseName, loadFactor, testDuration,testStartDelay ):
    # foreach scrc-dest-pair
    #       login to src
    #       foreach of the flows
    #               build corresponding cmdString and deploy
    srcList, destList= l2StridePatternTestPairCreator(nameToHostMap,maxPortcountInSwitch)
    deploymentPairList= []

    if (len(srcList) != len(destList)):
        logger.error("Srclist and dest list is not equal in length. Printing them and exiting")
        logger.error(srcList)
        logger.error(destList)
        exit(1)
    else:
        i = 0
        j=0
        for i in range(0, len(srcList)):
            flowArrivalTimesByflowType = calculateFlowArrivalTimes(loadFactor, testDuration)
            for j in range (0, len(ConfigConst.FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB)):
                flowsizeAsPacketCount = math.ceil(((ConfigConst.FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB[j]*1024)/(ConfigConst.PACKET_SIZE)))
                for k in range (0, len(flowArrivalTimesByflowType[j])):
                    flowArraivalTime = flowArrivalTimesByflowType[j][k]
                    newDeploymentPair = tc.IPerfDeplymentPair(srcList[i], destList[i], srcList[i].getNextIPerf3ClientPort(),
                                                              destList[i].getNextIPerf3ServerPort(),testCaseName = testCaseName,
                                                              srcHostName=srcList[i].hostName, destHostName= destList[i].hostName,
                                                              startTime= flowArraivalTime+float(testStartDelay),flowSizeinPackets= flowsizeAsPacketCount)
                    deploymentPairList.append(newDeploymentPair)
                    # print(newDeploymentPair.getServerCommand())
    return deploymentPairList

class TestCommandDeployer:

    def __init__(self,topologyConfigFilePath,resultFolder , clientPortStart,serverPortStart, testStartDelay):
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
        self.resultFolder = resultFolder


    def setupTestCaseFolder(self):

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
            logger.info("Original mask is "+str(original_umask))
            folderTobecreated = confConst.TEST_RESULT_FOLDER
            makeDirectory(folderTobecreated, access_rights)
            folderTobecreated = folderTobecreated+ "/"+ str(self.resultFolder)
            makeDirectory(folderTobecreated, access_rights)
            self.resultFolder = folderTobecreated
            # logger.info("folderTobecreated is :"+folderTobecreated)
            # serverFolderTobecreated = folderTobecreated  + confConst.TEST_RESULT_FOLDER_SERVER
            # makeDirectory(serverFolderTobecreated, access_rights)
            # clientFolderTobecreated = folderTobecreated  + confConst.TEST_RESULT_FOLDER_CLIENT
            # makeDirectory(clientFolderTobecreated, access_rights)
            print("folder creation completed")
            os.umask(original_umask)
        except Exception as e:
            logger.error("Exception occured in creating folder for test case results. ", e)
        finally:
            if(fh != None):
                fh.close()
                print("Timer file closed ")

    def generateTestCommands(self, testCaseNAme,loadFactor,testDuration, maxPortcountInSwitch):
        deploymentPairsAsList = getStrideDeploymentPairs(nameToHostMap = self.nameToHostMap,maxPortcountInSwitch = maxPortcountInSwitch,testCaseName = testCaseNAme,
                                                         loadFactor=loadFactor, testDuration=testDuration, testStartDelay = self.testStartDelay)
        access_rights = 0o777
        self.testCaseNAme = testCaseNAme
        try:
            original_umask = os.umask(0)
            logger.info("Original mask is "+str(original_umask))
            folderTobecreated = confConst.TEST_RESULT_FOLDER+"/"+self.testCaseNAme

            print("folder creation completed")
            os.umask(original_umask)
        except Exception as e:
            logger.error("Exception occured in creating folder for test case results. ", e)

        try:
            original_umask = os.umask(0)
            fh = open(self.resultFolder + "/"+testCaseNAme+".serverdat", 'w+')
            for d in deploymentPairsAsList:
                fh.write(str(d.getServerCommand()))
                fh.write("\n")
            os.umask(original_umask)
        except Exception as e:
                logger.error("Exception occured in creating serverside flow scheduler configuration for . "+testCaseNAme+". Exception is ", e)
        finally:
            if(fh != None):
                fh.close()
                print("Serverdat file closed ")
        try:
            original_umask = os.umask(0)
            fh = open(self.resultFolder + "/"+testCaseNAme+".clientdat", 'w+')
            for d in deploymentPairsAsList:
                fh.write(str(d.getCleintCommand()))
                fh.write("\n")
            os.umask(original_umask)
        except Exception as e:
            logger.error("Exception occurred in creating cleintside flow scheduler configuration for . "+testCaseNAme+". Exception is ", e)
        finally:
            if(fh != None):
                fh.close()
                print("clientdat file closed ")




if __name__ == "__main__":

    # Real deployment configuration
    #This is always the topology configuration.
    topologyConfigFilePath =  confConst.TOPOLOGY_CONFIG_FILE
    testEvaluator = TestCommandDeployer(topologyConfigFilePath = confConst.TOPOLOGY_CONFIG_FILE,resultFolder = "FlowInfos" , clientPortStart=confConst.IPERF3_CLIENT_PORT_START,
                        serverPortStart=confConst.IPERF3_SERVER_PORT_START, testStartDelay=10)
    testEvaluator.setupTestCaseFolder()
    testEvaluator.generateTestCommands( testCaseNAme= "WebSearchWorkLoad_load_factor_0.2",loadFactor=0.2,testDuration=150,maxPortcountInSwitch=ConfigConst.MAX_PORTS_IN_SWITCH)

    #--------------------

    testEvaluator = TestCommandDeployer(topologyConfigFilePath = confConst.TOPOLOGY_CONFIG_FILE,resultFolder = "FlowInfos" , clientPortStart=confConst.IPERF3_CLIENT_PORT_START,
                                        serverPortStart=confConst.IPERF3_SERVER_PORT_START, testStartDelay=10)
    testEvaluator.setupTestCaseFolder()
    testEvaluator.generateTestCommands( testCaseNAme= "WebSearchWorkLoad_load_factor_0.4",loadFactor=0.4,testDuration=150,maxPortcountInSwitch=ConfigConst.MAX_PORTS_IN_SWITCH)

    #--------------------
    testEvaluator = TestCommandDeployer(topologyConfigFilePath = confConst.TOPOLOGY_CONFIG_FILE,resultFolder = "FlowInfos" , clientPortStart=confConst.IPERF3_CLIENT_PORT_START,
                                        serverPortStart=confConst.IPERF3_SERVER_PORT_START, testStartDelay=10)
    testEvaluator.setupTestCaseFolder()
    testEvaluator.generateTestCommands( testCaseNAme= "WebSearchWorkLoad_load_factor_0.5",loadFactor=0.5,testDuration=150,maxPortcountInSwitch=ConfigConst.MAX_PORTS_IN_SWITCH)

    #--------------------
    testEvaluator = TestCommandDeployer(topologyConfigFilePath = confConst.TOPOLOGY_CONFIG_FILE,resultFolder = "FlowInfos" , clientPortStart=confConst.IPERF3_CLIENT_PORT_START,
                                        serverPortStart=confConst.IPERF3_SERVER_PORT_START, testStartDelay=10)
    testEvaluator.setupTestCaseFolder()
    testEvaluator.generateTestCommands( testCaseNAme= "WebSearchWorkLoad_load_factor_0.7",loadFactor=0.7,testDuration=150,maxPortcountInSwitch=ConfigConst.MAX_PORTS_IN_SWITCH)

    #--------------------
    testEvaluator = TestCommandDeployer(topologyConfigFilePath = confConst.TOPOLOGY_CONFIG_FILE,resultFolder = "FlowInfos" , clientPortStart=confConst.IPERF3_CLIENT_PORT_START,
                                        serverPortStart=confConst.IPERF3_SERVER_PORT_START, testStartDelay=10)
    testEvaluator.setupTestCaseFolder()
    testEvaluator.generateTestCommands( testCaseNAme= "WebSearchWorkLoad_load_factor_0.8",loadFactor=0.8,testDuration=200,maxPortcountInSwitch=ConfigConst.MAX_PORTS_IN_SWITCH)

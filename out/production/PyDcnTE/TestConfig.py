from dataclasses import dataclass
from typing import List
import threading
from dataclasses import dataclass
from enum import Enum
from time import sleep
from typing import List, TypeVar, Any, Callable, Type, cast, Dict

import  iperf3
import sys, getopt
import json
import logging
import os, sys
import TestConfigConstant as TC
import TestUtil as tu
import math

logger = logging.getLogger('SSHDeployer')
hdlr = logging.FileHandler('../log/SSHDeployer.log')
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)


# this function converts flow colume to bytes. For example 1M will return 1024*1024
def volumeAmmountToBytesConverter(volume):
    if str(volume).endswith("M"):  #It was expressed in M
        flowVolumeDigOnly = str(volume)[0:len(str(volume))-1]
        flowInBytes = int(flowVolumeDigOnly) * 1024 * 1024
        return flowInBytes
    elif str(volume).endswith("K"):  #It was expressed in K
        flowVolumeDigOnly = str(volume)[0:len(str(volume))-1]
        flowInBytes = int(flowVolumeDigOnly) * 1024
        return flowInBytes
    else: # Else volume was expressed in simple Bytes only.
        return int(volume)


def flowVloumeToBlockCountConverter(flowVolumeAsString, blockSize):
    flowVolumeAsBytes = volumeAmmountToBytesConverter(flowVolumeAsString)
    blocksizeInBytes = volumeAmmountToBytesConverter(blockSize)
    blockcount = math.ceil(flowVolumeAsBytes/blocksizeInBytes)
    return blockcount



def randomAllHostsTestPairCreator(nameToHostMap):
    srcList = []
    destList=[]
    for srcHostName in nameToHostMap:
        srcHost = nameToHostMap.get(srcHostName)
        hostIndex, leafSwitchIndex, podIndex = srcHost.getLocationIndexes()
        peerName = tu.getPeerHostName(hostIndex, leafSwitchIndex, podIndex,TC.MAX_PORT_COUNT)
        peerHostObject = nameToHostMap.get(peerName)
        if (srcHost!=None) and (peerHostObject != None):
            srcList.append(srcHost)
            destList.append((peerHostObject))
        print("Src: "+srcHostName+" peer host:"+peerName)
    return srcList, destList



T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def to_enum(c: Type[EnumT], x: Any) -> EnumT:
    assert isinstance(x, c)
    return x.value

def from_stringified_bool(x: str) -> bool:
    if x == "true":
        return True
    if x == "false":
        return False
    assert False

def from_dict(f: Callable[[Any], T], x: Any) -> Dict[str, T]:
    assert isinstance(x, dict)
    return { k: f(v) for (k, v) in x.items() }

@dataclass
class BasicElement:
    name: str
    ips: List[str]

    @staticmethod
    def from_dict(obj: Any) -> 'BasicElement':
        assert isinstance(obj, dict)
        name = from_str(obj.get("name"))
        ips = from_list(from_str, obj.get("ips"))
        return BasicElement(name, ips)

    def to_dict(self) -> dict:
        result: dict = {}
        result["name"] = from_str(self.name)
        result["ips"] = from_list(from_str, self.ips)
        return result


@dataclass
class FabricHostConfig:
    mac: str
    location: str

    @staticmethod
    def from_dict(obj: Any) -> 'FabricHostConfig':
        assert isinstance(obj, dict)
        mac = from_str(obj.get("mac"))
        location = from_str(obj.get("location"))
        return FabricHostConfig(mac, location)

    def to_dict(self) -> dict:
        result: dict = {}
        result["mac"] = from_str(self.mac)
        result["location"] = from_str(self.location)
        return result


@dataclass
class Host:
    hostName : str
    basic: BasicElement
    fabric_host_config: FabricHostConfig

    def __init__(self,hostName, basic, fabric_host_config):
        self.hostName = hostName
        self.basic = basic
        self.fabric_host_config = fabric_host_config
        self.portToLeafSwitchMap = {}
        self.iperf3ClientPortStart = TC.IPERF3_CLIENT_PORT_START
        self.iperf3ServerPortStart = TC.IPERF3_SERVER_PORT_START
        self.clientCommands=[]   # These commands are supposed to be executed in this host as server
        self.serverCommands=[]# These commands are supposed to be executed in this host as  client

    def getAllServerCommands(self):
        serverCommands = []
        for c in self.serverCommands:
            serverCommands.append(c.serverCmdString)
        return serverCommands

    def getAllClientCommands(self):
        cleintCommands = []
        for c in self.clientCommands:
            cleintCommands.append(c.clientCmdString)
        return cleintCommands


    def getNextIPerf3ServerPort(self):
        self.iperf3ServerPortStart = self.iperf3ServerPortStart+1
        return self.iperf3ServerPortStart

    def getNextIPerf3ClientPort(self):
        self.iperf3ClientPortStart = self.iperf3ClientPortStart+1
        return self.iperf3ClientPortStart


    @staticmethod
    def from_dict( obj: Any) -> 'Host':
        assert isinstance(obj, dict)
        basic = BasicElement.from_dict(obj.get("basic"))
        fabric_host_config = FabricHostConfig.from_dict(obj.get("fabricHostConfig"))
        return Host(basic.name,basic, fabric_host_config)

    def to_dict(self) -> dict:
        result: dict = {}
        result["basic"] = to_class(BasicElement, self.basic)
        result["fabricHostConfig"] = to_class(FabricHostConfig, self.fabric_host_config)
        return result
    def getLocationIndexes(self):
        hostIndex=self.basic.name[self.basic.name.index("h")+1: self.basic.name.index("p")]
        podIndex = self.basic.name[self.basic.name.index("p")+1: self.basic.name.index("l")]
        leafSwitchIndex=self.basic.name[self.basic.name.index("l")+1: len(self.basic.name)]
        return hostIndex, leafSwitchIndex, podIndex



def loadCFG(cfgfileName):
    nameToHostMap = {}
    cfgFile = open(cfgfileName)
    obj = json.load(fp=cfgFile)
    for hostMac in obj["hosts"]:
        h = Host.from_dict( obj["hosts"][hostMac])
        nameToHostMap[h.basic.name] = h
    cfgFile.close()
    print("Printing the map",nameToHostMap)
    logger.info("Finished reading and loading cfg")
    return nameToHostMap


class IPerfDeplymentPair:
    def __init__(self,src, dest, srcPort, destPort, flowInfo, testCaseName):
        self.flowInfo = flowInfo
        self.src = src
        self.srcIP = src.basic.ips[0]
        self.dest = dest
        self.destIP = dest.basic.ips[0]
        self.srcPort = srcPort
        self.destPort = destPort
        self.testCaseName = testCaseName

    def generateIPerf3Command(self,nameToHostMap):
        blockSize = "1024"
        self.clientSideTestResultFileName = TC.TEST_RESULT_FOLDER + "/" + self.testCaseName +"/"+ str(self.src.hostName) + "-" + str(self.dest.hostName)
        self.serverSideTestResultFileName = TC.TEST_RESULT_FOLDER+"/"+self.testCaseName+"/"+str(self.dest.hostName)+"-server"



        #self.testResultFileName = "./"+self.testCaseName+"-"+str(self.src.hostName)+"-"+str(self.dest.hostName)
        #print(self.testResultFileName)
        # build the iperf3 server command for daemon mode with only one try for connection. dest is the server here. iperf3 -s -D
        self.serverCmdString = "iperf3 --server --port "+str(self.destPort) +" --json --logfile "+self.serverSideTestResultFileName+"  &"
        #self.serverCmdString = "ls -la"
        #print(self.serverCmdString) 
        # build the iperf3 client command for daemon mode with only one try for connection. Src is the client here
        #/home/deba/Desktop/bmv2-p0s1.log.2.txt
        if self.flowInfo.flow_type == "tcp":
            # Build iperf3 client command for tcp
            self.clientCmdString = "python3 /home/deba/Desktop/PyDcnTE/testAndMeasurement/HostFlowStarter.py \"iperf3 --client " + str(self.destIP) +" --port " + str(self.destPort) +" --cport " + str(self.srcPort)#+" -f K "
            #self.clientCmdString=  self.clientCmdString + " -n "+ str(self.flowInfo.flow_volume) + " --set-mss "+str(self.flowInfo.pkt_size) + " --window "+str(self.flowInfo.src_window_size)+" "
            #self.clientCmdString=  self.clientCmdString + " -t 20 -n 2 -l 50" + " --set-mss "+str(self.flowInfo.pkt_size) + " --window "+str(self.flowInfo.src_window_size)+" "
            self.clientCmdString = self.clientCmdString+ " --connect-timeout 9999 "
            self.clientCmdString=  self.clientCmdString + " " + " --set-mss "+str(self.flowInfo.pkt_size) + " -w "+str(self.flowInfo.src_window_size)
            self.clientCmdString=  self.clientCmdString + " -n "+ str(self.flowInfo.flow_volume)
            #self.clientCmdString=  self.clientCmdString +  " --set-mss "+str(self.flowInfo.pkt_size) + " --window "+str(self.flowInfo.src_window_size)+" "
            #self.clientCmdString=  self.clientCmdString + " -k "+ str(flowVloumeToBlockCountConverter(self.flowInfo.flow_volume, blockSize))+ " -b "+ str(self.flowInfo.src_data_rate) + " -l "+blockSize+" "
            self.clientCmdString=  self.clientCmdString  +" --json --logfile "+ self.clientSideTestResultFileName + " &\" "
            #self.clientCmdString=  self.clientCmdString  +" --logfile "+ self.clientSideTestResultFileName + " &\" "
            pass
        elif self.flowInfo.flow_type == "udp":
            self.clientCmdString = "python3 /home/deba/Desktop/PyDcnTE/testAndMeasurement/HostFlowStarter.py \"iperf3 --client " + str(self.destIP) +" --port " + str(self.destPort) +" --cport " + str(self.srcPort) +" --json --logfile " + self.clientSideTestResultFileName + " &\" "
            pass
        else:
            print("flow type: "+ self.flowInfo.flow_type + " is not supported yet" )
            exit(1)
        #print(self.clientCmdString)
        self.dest.serverCommands.append(self)
        self.src.clientCommands.append(self)
        return



@dataclass
class Flow:
    flow_type: str
    flow_volume: str
    src_window_size: str
    src_data_rate: str
    pkt_size: int
    is_interactive: bool

    @staticmethod
    def from_dict(obj: Any) -> 'Flow':
        assert isinstance(obj, dict)
        flow_type = from_str(obj.get("flow_type"))
        flow_volume = from_str(obj.get("flow-volume"))
        src_window_size = from_str(obj.get("src-window-size"))
        src_data_rate = from_str(obj.get("src-data-rate"))
        pkt_size = int(from_str(obj.get("pkt-size")))
        is_interactive = from_stringified_bool(from_str(obj.get("is-interactive")))
        return Flow(flow_type, flow_volume, src_window_size, src_data_rate, pkt_size, is_interactive)

    def to_dict(self) -> dict:
        result: dict = {}
        result["flow_type"] = from_str(self.flow_type)
        result["flow-volume"] = from_str(self.flow_volume)
        result["src-window-size"] = from_str(self.src_window_size)
        result["src-data-rate"] = from_str(self.src_data_rate)
        result["pkt-size"] = from_str(str(self.pkt_size))
        result["is-interactive"] = from_str(str(self.is_interactive).lower())
        return result


@dataclass
class SrcDstPair:
    src: str
    dest: str
    pattern : str
    flows: List[Flow]

    @staticmethod
    def from_dict(obj: Any) -> 'SrcDstPair':
        assert isinstance(obj, dict)
        src = from_str(obj.get("src"))
        dest = from_str(obj.get("dest"))
        pattern = from_str(obj.get("pattern"))
        flows = from_list(Flow.from_dict, obj.get("flows"))
        return SrcDstPair(src, dest, pattern, flows)

    def to_dict(self) -> dict:
        result: dict = {}
        result["src"] = from_str(self.src)
        result["dest"] = from_str(self.dest)
        result["pattern"] = from_str(self.pattern)
        result["flows"] = from_list(lambda x: to_class(Flow, x), self.flows)
        return result
    def generatePair(self,test_case_name, nameToHostMap):
        self.testCaseName= test_case_name
        srcList = []
        destList = []
        if self.pattern.lower() == "one-to-one":
            srcList.append(nameToHostMap.get(self.src))
            destList.append(nameToHostMap.get(self.dest))
        elif self.pattern.lower() == "random-same-pod":
            pass
        elif self.pattern.lower() == "random-same-leaf":
            pass
        elif self.pattern.lower() == "all-hosts":
            srcList, destList = randomAllHostsTestPairCreator(nameToHostMap)
            pass
        else:
            logger.error("Given patttern not supported yet. Exiting")
            exit(1)

        deploymentPairList= []
        for f in self.flows:
            #We expect that for each src there will be a dest. so srclist and dest list will be equal in size. and i'th index of srclist will connect with i'th indexed element fo dstList; Otherwise there is some error
            if (len(srcList) != len(destList)):
                logger.error("Srclist and dest list is not equal in length. Printing them and exiting")
                logger.error(srcList)
                logger.error(destList)
                exit(1)
            else:
                i = 0
                for i in range(0, len(srcList)):
                    newDeploymentPair = IPerfDeplymentPair(srcList[i], destList[i], srcList[i].getNextIPerf3ClientPort(), destList[i].getNextIPerf3ServerPort(),f, self.testCaseName)
                    deploymentPairList.append(newDeploymentPair)
        return  deploymentPairList

@dataclass
class Test:
    test_case_name: str
    src_dst_pairs: List[SrcDstPair]

    @staticmethod
    def from_dict(obj: Any) -> 'Test':
        assert isinstance(obj, dict)
        test_case_name = from_str(obj.get("testCaseName"))
        src_dst_pairs = from_list(SrcDstPair.from_dict, obj.get("src-dst-pairs"))
        return Test(test_case_name, src_dst_pairs)

    def to_dict(self) -> dict:
        result: dict = {}
        result["testCaseName"] = from_str(self.test_case_name)
        result["src-dst-pairs"] = from_list(lambda x: to_class(SrcDstPair, x), self.src_dst_pairs)
        return result

    def getIPerfCommand(self,nameToHostMap):
        # foreach scrc-dest-pair
        #       login to src
        #       foreach of the flows
        #               build corresponding cmdString and deploy

        for srcDestPair in self.src_dst_pairs:
            deploymentPairList=srcDestPair.generatePair(self.test_case_name,nameToHostMap)
        for depPair in deploymentPairList:
            # Generate the src (iperf client) and dest (iperf3 server ) sommand for each deployment pair
            depPair.generateIPerf3Command(nameToHostMap)
        # for each flow --> allocate a port in the dest host for server side communication and one for client sidecommunication in clinet side
        # Build a list of object for server side commands and client side commands.
        # This list will be saved in each host's map.
        #at last we will deploy everything in a host at once --> at first server side then client side


@dataclass
class TestConfigs:
    tests: List[Test]

    @staticmethod
    def from_dict(obj: Any) -> 'Welcome':
        assert isinstance(obj, dict)
        tests = from_list(Test.from_dict, obj.get("TESTS"))
        return TestConfigs(tests)

    def to_dict(self) -> dict:
        result: dict = {}
        result["TESTS"] = from_list(lambda x: to_class(Test, x), self.tests)
        return result
    def genIPerfCommands(self, nameToHostMap):
        for t in self.tests:
            t.getIPerfCommand(nameToHostMap)



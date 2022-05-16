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





# sys.path.append(os.path.dirname("../PyDcnTE/P4Runtime "))
# from P4Runtime import JsonParser as jp


CONFIG_FILE_NAME = "../../MininetSimulator/Build/Internalnetcfg.json"
#CONFIG_FILE_NAME = "../MininetSimulator/Build/Internalnetcfg.json"
TEST_RESULT_FOLDER = "./testAndMeasurement/TEST_RESULTS"
LOG_FILE_FOLDER = "../TEST_LOG"
#LOG_FILE_FOLDER = "./TEST_LOG"
logger = None


nameToHostMap = {}
# client = iperf3.Client()
# client.duration = 1
# client.bind_address = '10.0.0.1'
# client.server_hostname = '10.10.10.10'
# client.port = 6969
# client.blksize = 1234
# client.num_streams = 10
# client.zerocopy = True
# client.verbose = False
# client.reverse = True
# client.run()

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
    global logger
    cfgFile = open(cfgfileName)
    obj = json.load(fp=cfgFile)
    for hostMac in obj["hosts"]:
        h = Host.from_dict( obj["hosts"][hostMac])
        nameToHostMap[h.basic.name] = h
    cfgFile.close()
    #print("Printing the map",nameToHostMap)
    logger.info("Finished reading and loading cfg")

def setLogger(myHostname,testCaseName):
    global  logger
    logger = logging.getLogger(myHostname)
    hdlr = logging.FileHandler(filename = LOG_FILE_FOLDER+"/"+myHostname+".log", mode='w+')
    formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)
    logger.info("Starting test for host:"+myHostname+" test scenario: "+testCaseName)

def getPeerHostName(hostIndex, leafSwitchIndex, podIndex , portCount):
    global logger
    peerHostIndex = int((int(hostIndex)+1+ int(portCount)/2) % (int(portCount)/2))
    peerLeafSwitchIndex = int( (int(leafSwitchIndex)+1+ (int(portCount)/2)) % int((portCount)/2))
    peerPodIndex = int((int(podIndex)+1+ (int(portCount)/2)) % int((portCount)))
    peerHostName = "h"+str(peerHostIndex)+"p"+str(peerPodIndex)+"l"+str(peerLeafSwitchIndex)
    return peerHostName

def iperf3CleintFunction(name):
    global logger
    logger.info("Inside client fiuntion")
    while(True):
        sleep(10000)
        logger.info("Wake u p from sleep after 10 s")


def main(argv):
    global logger
    print("CLI format is: iperf3_test.py MyHostname  testCaseName portCount")
    myHostname = argv[0]
    testCaseName = argv[1]
    portCount = int(argv[2])
#
# # These 3 lines are only for debugging
#     myHostname ="h0p0l0"
#     testCaseName = "basic"
#     portCount = 4

    setLogger(myHostname,testCaseName)
    loadCFG(CONFIG_FILE_NAME)
    myHostObject = nameToHostMap.get(myHostname)
    logger.info("My host name is "+myHostname)
    logger.info(myHostObject)
    if(myHostObject  ==  None):
        logger.info("MyHost is not found in hostname to host objectmap")
        exit(-1)
    hostIndex, leafSwitchIndex, podIndex = myHostObject.getLocationIndexes()
    peerName = getPeerHostName(hostIndex, leafSwitchIndex, podIndex,portCount)
    peerHostObject = nameToHostMap.get(peerName)
    logger.info("My peer name is :"+peerName)
    logger.info(peerHostObject)
    if(peerHostObject==None):
        logger.info("Peer Host is not found in hostname to host objectmap")
        exit(-1)
    sleep(10)  #25 second for waiting to starrt the controller
    cmdString = "iperf3 -c "+ str(peerHostObject.basic.ips[0])+ " -n 1024 k -w 32M -b 248k --cport 65532 >>"+ TEST_RESULT_FOLDER+ "/"+myHostname+".txt\n"
    logger.info("Command is :"+cmdString)
    try:
        os.system(cmdString)
        #logger.info("Output of command is "+outs)
    except :
        logger.error("Error in executing cli command to switch ",myHostObject, ". Error is :", sys.exc_info()[0])
    # try:
    #     client = iperf3.Client()
    #     client.duration = 1
    #     client.bind_address = str(myHostObject.basic.ips[0])
    #     logger.info("My server address is "+str(myHostObject.basic.ips[0]))
    #     client.server_hostname = str(peerHostObject.basic.ips[0])
    #     logger.info("Peer server address is "+ str(peerHostObject.basic.ips[0]))
    #     client.port = 5201
    #     client.local_port = 5279
    #     client.num_streams = 10
    #     client.zerocopy = True
    #     client.verbose = False
    #     client.reverse = True
    #     result = client.run()
    #     if result.error:
    #         logger.info("error in getting result of iperf3:"+result.error)
    #     else:
    #         logger.info('')
    #         logger.info('Test results from {0}:{1}'.format(result.remote_host,
    #                                                  result.remote_port))
    #         logger.info('  started at         {0}'.format(result.time))
    #         logger.info('  bytes received     {0}'.format(result.received_bytes))
    #
    #         logger.info('Average transmitted received in all sorts of networky formats:')
    #         logger.info('  bits per second      (bps)   {0}'.format(result.received_bps))
    #         logger.info('  Kilobits per second  (kbps)  {0}'.format(result.received_kbps))
    #         logger.info('  Megabits per second  (Mbps)  {0}'.format(result.received_Mbps))
    #         logger.info('  KiloBytes per second (kB/s)  {0}'.format(result.received_kB_s))
    #         logger.info('  MegaBytes per second (MB/s)  {0}'.format(result.received_MB_s))
    #
    #         logger.info('')
    # except :
    #     e = sys.exc_info()
    #     logger.error("Error in getting test REsulr ", e)
    #     logger.error("Error is "+str( e))


if __name__ == "__main__":
    main(sys.argv[1:])

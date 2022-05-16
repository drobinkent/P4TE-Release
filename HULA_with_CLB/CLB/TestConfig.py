import json
import logging
import math
import os
from dataclasses import dataclass
from enum import Enum
import random
from numpy import random as nprandom

import ConfigConst
import ConfigConst as confConst

from typing import List, TypeVar, Any, Callable, Type, cast, Dict
logger = logging.getLogger('SSHDeployer')
hdlr = logging.FileHandler('./log/SSHDeployer.log')
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
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




def getLocationIndexes(self):
    hostIndex=self.basic.name[self.basic.name.index("h")+1: self.basic.name.index("p")]
    podIndex = self.basic.name[self.basic.name.index("p")+1: self.basic.name.index("l")]
    leafSwitchIndex=self.basic.name[self.basic.name.index("l")+1: len(self.basic.name)]
    return hostIndex, leafSwitchIndex, podIndex

def getPeerHostName(hostIndex, leafSwitchIndex, podIndex , portCount):
    peerHostIndex = int((int(hostIndex)+1+ int(portCount)/2) % (int(portCount)/2))
    peerLeafSwitchIndex = int( (int(leafSwitchIndex)+1+ (int(portCount)/2)) % int((portCount)/2))
    peerPodIndex = int((int(podIndex)+1+ (int(portCount)/2)) % int((portCount)))
    peerHostName = "h"+str(peerHostIndex)+"p"+str(peerPodIndex)+"l"+str(peerLeafSwitchIndex)
    return peerHostName

def getL2StrdePeerHostName(hostIndex, leafSwitchIndex, podIndex , portCount):
    peerHostIndex = int((int(hostIndex)+1+ int(portCount)/2) % (int(portCount)/2))
    peerLeafSwitchIndex = int( (int(leafSwitchIndex)+1+ (int(portCount)/2)) % int((portCount)/2))
    peerPodIndex = int(podIndex)
    peerHostName = "h"+str(peerHostIndex)+"p"+str(peerPodIndex)+"l"+str(peerLeafSwitchIndex)
    return peerHostName

def randomSamePodTestPairCreator(nameToHostMap,maxPortcountInSwitch, podId = 1):
    #maxPortcountInSwitch means this many pods are their. so we can rnadomly take one and generate flow
    # or take the podId passed as parameter.
    #2 type combination a) stride inside pod
    # all pair 
    pass

def l2StridePatternTestPairCreator(nameToHostMap, maxPortcountInSwitch, pattern, flow, strideCount=8):

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
        if(count>=strideCount):
            break;
        print("Src: "+srcHostName+" peer host:"+peerName)

    return srcList, destList

def stridePatternTestPairCreator(nameToHostMap, maxPortcountInSwitch, pattern, flow, strideCount=16):

    srcList = []
    destList=[]
    count = 0
    for srcHostName in nameToHostMap:
        srcHost = nameToHostMap.get(srcHostName)
        hostIndex, leafSwitchIndex, podIndex = srcHost.getLocationIndexes()
        peerName = getPeerHostName(hostIndex, leafSwitchIndex, podIndex, maxPortcountInSwitch)
        peerHostObject = nameToHostMap.get(peerName)
        if (srcHost!=None) and (peerHostObject != None):
            srcList.append(srcHost)
            destList.append((peerHostObject))
            count = count+1
        if(count>=strideCount):
            break;
        print("Src: "+srcHostName+" peer host:"+peerName)

    return srcList, destList

def generateNRandomSrcDestPair(testCaseName,nameToHostMap, maxPortcountInSwitch, pattern, flow):
    srcList = []
    destList=[]
    hostList =  [item for item in nameToHostMap]
    flowcountStart = pattern.find("random(")+7 # 7 character for "random("
    flowCountEnd= pattern.find(")", flowcountStart)
    print(flowcountStart, flowCountEnd)
    flowCount= int(pattern[int(flowcountStart): int(flowCountEnd)])
    print(flowCount)
    for i in range (0, flowCount):
        src=random.randint(0, len(hostList)-1)
        hostIndex, leafSwitchIndex, podIndex = nameToHostMap.get(hostList[src]).getLocationIndexes()
        peerName = getPeerHostName(hostIndex, leafSwitchIndex, podIndex, maxPortcountInSwitch)
        dst= nameToHostMap.get(peerName)
        srcHost = nameToHostMap.get(hostList[src])
        dstHost = dst
        srcList.append(srcHost)
        destList.append(dstHost)
    return srcList, destList

def startNRandomFlow(testCaseName,nameToHostMap, maxPortcountInSwitch, pattern, flow):
    '''
    :testCaseName:
    :param nameToHostMap:
    :param maxPortcountInSwitch:
    :param pattern:
    :param flow: This type of test case will only have one flow in src-dst pair. property for that flow will be used for all the randmly generated flows
    :return:
    '''


    deploymentPairList= []
    hostList =  [item for item in nameToHostMap]
    for j in range(0, flow.repeat):
        srcList, destList = generateNRandomSrcDestPair(testCaseName,nameToHostMap, maxPortcountInSwitch, pattern, flow)
        if (len(srcList) != len(destList)):
            logger.error("Srclist and dest list is not equal in length. Printing them and exiting")
            logger.error(srcList)
            logger.error(destList)
            exit(1)
        for i in range(0, len(srcList)):
            x = nprandom.poisson(lam=confConst.LAMBDA, size=len(srcList))
            print("List is "+str(hostList))
            print("Creating new deployment pair with src"+str(srcList[i])+" Destination:-- "+str(destList[i]) + " Start ime : "+str(x[i]))
            newDeploymentPair = IPerfDeplymentPair((srcList[i]), (destList[i]), (srcList[i]).getNextIPerf3ClientPort(),
                                               (destList[i]).getNextIPerf3ServerPort(),flow,
                                               testCaseName,startTime= x[i]+(flow.repeat_interval*j))
            deploymentPairList.append(newDeploymentPair)
    return  deploymentPairList

def allPairHostTestPairCreator(nameToHostMap,maxPortcountInSwitch):
    '''
    This method create testing pair for all hosts to all host. You can assume this as a mesh connnection
    :param nameToHostMap:
    :return:
    '''
    srcList = []
    destList=[]
    for srcHostName in nameToHostMap:
        for destHostName in nameToHostMap:
            srcHost = nameToHostMap.get(srcHostName)
            dstHost = nameToHostMap.get(destHostName)
            if (srcHost != dstHost): # only skip same host to same host flow
                srcList.append(srcHost)
                destList.append(dstHost)
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

    def __init__(self,hostName, basic, fabric_host_config,clientPortStart, serverPortStart):
        self.hostName = hostName
        self.basic = basic
        self.fabric_host_config = fabric_host_config
        self.portToLeafSwitchMap = {}
        self.iperf3ClientPortStart = clientPortStart
        self.iperf3ServerPortStart = serverPortStart
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
    def from_dict( obj: Any, clientPortStart, serverPortStart) -> 'Host':
        assert isinstance(obj, dict)
        basic = BasicElement.from_dict(obj.get("basic"))
        fabric_host_config = FabricHostConfig.from_dict(obj.get("fabricHostConfig"))
        return Host(basic.name,basic, fabric_host_config,clientPortStart, serverPortStart)

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



def loadCFG(cfgfileName,clientPortStart, serverPortStart):
    nameToHostMap = {}
    cfgFile = open(cfgfileName)
    obj = json.load(fp=cfgFile)
    for hostMac in obj["hosts"]:
        h = Host.from_dict( obj["hosts"][hostMac],clientPortStart, serverPortStart)
        nameToHostMap[h.basic.name] = h
    cfgFile.close()
    #print("Printing the map",nameToHostMap)
    logger.info("Finished reading and loading cfg")
    return nameToHostMap

def makeDirectory(folderPath, accessRights):
    if not os.path.exists(folderPath):
        os.mkdir(folderPath, accessRights)


class IPerfDeplymentPair:
    def __init__(self,src, dest, srcPort, destPort,srcHostName, destHostName, testCaseName, startTime = 0,flowSizeinPackets=100):
        '''
        startTime is required when we want to repeat a flow. So assume we want to repeat a flow 10 times. So if we start a specfic test at time x,
        This deployment Pari will be started at x+startTime time
        '''
        self.src = src
        self.srcIP = src.basic.ips[0]
        self.dest = dest
        self.destIP = dest.basic.ips[0]
        self.srcPort = srcPort
        self.destPort = destPort
        self.testCaseName = testCaseName
        self.startTime = startTime
        self.flowSizeinPackets = flowSizeinPackets
        self.testResultFolder = ConfigConst.TEST_RESULT_FOLDER+"/"+testCaseName
        self.srcHostName = srcHostName
        self.destHostName = destHostName
        access_rights = 0o777
        try:
            original_umask = os.umask(0)
            logger.info("Original mask is "+str(original_umask))
            makeDirectory(self.testResultFolder, access_rights)
            os.umask(original_umask)
        except Exception as e:
            logger.error("Exception occured in creating folder for test case results. ", e)

    def getServerCommand(self):
        # self.serverCmdString = "Generate the servoice comman string here in pattern : host server.py port -- myserver is "+str(self.destIP)+"--"+str(self.destPort)
        self.serverCmdString = self.destHostName + " "+ "python Server.py "+ str(self.destIP) + " "+ str(self.destPort)+ " "+str((float(self.startTime)/2))
        return self.serverCmdString

    def getCleintCommand(self):
        self.clientCmdString = self.srcHostName + " "+ "python Client.py "+ str(self.destIP) + " "+ str(self.destPort) + "  "+str(self.flowSizeinPackets) \
                               + " "+self.testResultFolder+ "/"+str(self.srcIP)+"_"+str(self.srcPort)+"_"+self.destIP+"_"+str(self.destPort) +\
                               " "+str(self.startTime)
        return self.clientCmdString

    def generateIPerf3Command(self, testResultFolderRoot, clientResultLogSubFolder, serverResultLogSubFolder):
        blockSize = "1024"
        self.clientSideTestResultFileName = testResultFolderRoot + "/" + self.testCaseName +clientResultLogSubFolder+"/"+ str(self.src.hostName)+"-" +str(self.srcPort) +"-" + str(self.dest.hostName)+"-"+str(self.destPort)
        self.serverSideTestResultFileName = testResultFolderRoot+"/"+self.testCaseName+serverResultLogSubFolder+"/"+str(self.src.hostName)+"-"  +str(self.srcPort) +"-" + str(self.dest.hostName)+"-" +str(self.destPort)



        #self.testResultFileName = "./"+self.testCaseName+"-"+str(self.src.hostName)+"-"+str(self.dest.hostName)
        #print(self.testResultFileName)
        # build the iperf3 server command for daemon mode with only one try for connection. dest is the server here. iperf3 -s -D
        # -1 for accepting only one connection
        self.serverCmdString = " iperf3 --server -1 -D --port "+str(self.destPort) +" --json --logfile "+self.serverSideTestResultFileName+"  &"
        #self.serverCmdString = "ls -la"
        #print(self.serverCmdString) 
        # build the iperf3 client command for daemon mode with only one try for connection. Src is the client here
        #/home/deba/Desktop/bmv2-p0s1.log.2.txt
        if self.flowInfo.flow_type == "tcp":
            # Build iperf3 client command for tcp
            #self.clientCmdString = "python3 ./testAndMeasurement/HostFlowStarter.py \" iperf3 --client " + str(self.destIP) +" --port " + str(self.destPort) +" --cport " + str(self.srcPort)#+" -f K "
            self.clientCmdString = "iperf3 --client " + str(self.destIP) +" --port " + str(self.destPort) +" --cport " + str(self.srcPort)#+" -f K "
            #self.clientCmdString=  self.clientCmdString + " -n "+ str(self.flowInfo.flow_volume) + " --set-mss "+str(self.flowInfo.pkt_size) + " --window "+str(self.flowInfo.src_window_size)+" "
            #self.clientCmdString=  self.clientCmdString + " -t 20 -n 2 -l 50" + " --set-mss "+str(self.flowInfo.pkt_size) + " --window "+str(self.flowInfo.src_window_size)+" "
            self.clientCmdString = self.clientCmdString+ " --connect-timeout 9999 "
            self.clientCmdString = self.clientCmdString+ " -l 1400 " # use 4K buffer length. That means each time write 4KB of data. otherwise iperf3 tries to write 128 KB data this results in highly variable result
            #self.clientCmdString=  self.clientCmdString + " " + "--flowlabel"+ " " + " --set-mss "+str(self.flowInfo.pkt_size) + " -w "+str(self.flowInfo.src_window_size)
            self.clientCmdString=  self.clientCmdString + " " + " " + " --set-mss "+str(self.flowInfo.pkt_size) + " "
            self.clientCmdString=  self.clientCmdString + " -n "+ str(self.flowInfo.flow_volume)
            if( str(self.flowInfo.src_window_size) != ""):
                self.clientCmdString=  self.clientCmdString + " -w "+ str(self.flowInfo.src_window_size)
                #self.clientCmdString= self.clientCmdString + " -w " + confConst.IPERF_DEFAULT_WINDOW_SIZE_FOR_SERVER + " "
            else:
                self.clientCmdString= self.clientCmdString + " -w " + confConst.IPERF_DEFAULT_WINDOW_SIZE_FOR_SERVER + " "
            if( str(self.flowInfo.src_data_rate) != ""): # If src-data rate is empty stringn then iperf will use it's own setting for data rate. which is unlimited for tcp
                self.clientCmdString=  self.clientCmdString + " -b "+ str(self.flowInfo.src_data_rate)
            else:
                self.clientCmdString=  self.clientCmdString + " -b "+ str(confConst.IPERF_MAX_FLOW_RATE_FOR_SERVER)
            # self.clientCmdString= self.clientCmdString + " -w " + confConst.IPERF_DEFAULT_WINDOW_SIZE_FOR_SERVER + " "
            self.clientCmdString = self.clientCmdString + " -S "+ str(self.flowInfo.flow_traffic_class)
            # self.clientCmdString = self.clientCmdString + " --pacing-timer "+ str(confConst.IPERF_PACING_TIMER) + " "
            #self.clientCmdString=  self.clientCmdString +  " --set-mss "+str(self.flowInfo.pkt_size) + " --window "+str(self.flowInfo.src_window_size)+" "
            #self.clientCmdString=  self.clientCmdString + " -k "+ str(flowVloumeToBlockCountConverter(self.flowInfo.flow_volume, blockSize))+ " -b "+ str(self.flowInfo.src_data_rate) + " -l "+blockSize+" "
            self.clientCmdString = self.clientCmdString+ " -C dctcp  "
            #self.clientCmdString=  self.clientCmdString  +" --json --logfile "+ self.clientSideTestResultFileName + " &\" "
            self.clientCmdString=  self.clientCmdString  +" --json --logfile "+ self.clientSideTestResultFileName + " & "
            #self.clientCmdString=  self.clientCmdString  +" --logfile "+ self.clientSideTestResultFileName + " &\" "
            pass
        elif self.flowInfo.flow_type == "udp":
            self.clientCmdString = "python3 ./testAndMeasurement/HostFlowStarter.py \"iperf3 --client " + str(self.destIP) +" --port " + str(self.destPort) +" --cport " + str(self.srcPort) +" --json --logfile " + self.clientSideTestResultFileName + " &\" "
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
    repeat: int
    repeat_interval: int
    flow_traffic_class : str

    @staticmethod
    def from_dict(obj: Any) -> 'Flow':
        assert isinstance(obj, dict)
        flow_type = from_str(obj.get("flow_type"))
        flow_volume = from_str(obj.get("flow-volume"))
        src_window_size = from_str(obj.get("src-window-size"))
        src_data_rate = from_str(obj.get("src-data-rate"))
        pkt_size = int(from_str(obj.get("pkt-size")))
        flow_traffic_class = (from_str(obj.get("flow_traffic_class")))
        is_interactive = from_stringified_bool(from_str(obj.get("is-interactive")))
        repeat = int(from_str(obj.get("repeat")))
        repeat_interval = int(from_str(obj.get("repeat_interval")))
        return Flow(flow_type, flow_volume, src_window_size, src_data_rate, pkt_size, is_interactive, repeat, repeat_interval, flow_traffic_class)

    def to_dict(self) -> dict:
        result: dict = {}
        result["flow_type"] = from_str(self.flow_type)
        result["flow-volume"] = from_str(self.flow_volume)
        result["src-window-size"] = from_str(self.src_window_size)
        result["src-data-rate"] = from_str(self.src_data_rate)
        result["pkt-size"] = from_str(str(self.pkt_size))
        result["is-interactive"] = from_str(str(self.is_interactive).lower())
        result["repeat"] = from_str(str(self.repeat))
        result["repeat_interval"] = from_str(str(self.repeat_interval))
        result["flow_traffic_class"] = from_str(str(self.flow_traffic_class))
        return result





@dataclass
class SrcDstPair:
    src: str
    dest: str
    pattern: str
    flows: List[Flow]

    @staticmethod
    def from_dict(obj: Any) -> 'SrcDstPair':
        assert isinstance(obj, dict)
        src = from_str(obj.get("src"))
        dest = from_str(obj.get("dest"))
        pattern = from_str(obj.get("pattern"))
        flows = from_list(Flow.from_dict, obj.get("flows"))
        return SrcDstPair(src, dest, pattern,  flows)

    def to_dict(self) -> dict:
        result: dict = {}
        result["src"] = from_str(self.src)
        result["dest"] = from_str(self.dest)
        result["pattern"] = from_str(self.pattern)
        result["flows"] = from_list(lambda x: to_class(Flow, x), self.flows)
        return result

    def generatePair(self,test_case_name, nameToHostMap,maxPortcountInSwitch):
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
        elif self.pattern.lower().startswith("random(") :
            deploymentPairList = startNRandomFlow(self.testCaseName,nameToHostMap,maxPortcountInSwitch,self.pattern, self.flows[0])  #Only one flow will be in test case, that flows' property will be used ofr all the randomly gnerated flow
            return deploymentPairList
        elif self.pattern.lower().startswith("stride") :
            srcList, destList = stridePatternTestPairCreator(nameToHostMap, maxPortcountInSwitch,self.pattern, self.flows[0])
            pass
        elif self.pattern.lower().startswith("l2stride") :
            srcList, destList = l2StridePatternTestPairCreator(nameToHostMap, maxPortcountInSwitch,self.pattern, self.flows[0])
            pass
        elif self.pattern.lower() == "mesh":
            srcList, destList = allPairHostTestPairCreator(nameToHostMap,maxPortcountInSwitch)
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
                j=0

                for i in range(0, len(srcList)):
                    tempStart = 0
                    for j in range(0, f.repeat):
                        newDeploymentPair = IPerfDeplymentPair(srcList[i], destList[i], srcList[i].getNextIPerf3ClientPort(), destList[i].getNextIPerf3ServerPort(),f,
                            self.testCaseName,startTime= tempStart)
                        deploymentPairList.append(newDeploymentPair)
                        tempStart = tempStart + f.repeat_interval

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

    def getIDeploymentPairs(self,nameToHostMap,maxPortcountInSwitch):
        # foreach scrc-dest-pair
        #       login to src
        #       foreach of the flows
        #               build corresponding cmdString and deploy
        allDeploymentPairList = []

        for srcDestPair in self.src_dst_pairs:
            deploymentPairList=srcDestPair.generatePair(self.test_case_name,nameToHostMap,maxPortcountInSwitch)
            allDeploymentPairList = allDeploymentPairList + deploymentPairList
        return  allDeploymentPairList
        # for depPair in deploymentPairList:
        #     # Generate the src (iperf client) and dest (iperf3 server ) sommand for each deployment pair
        #     depPair.generateIPerf3Command(nameToHostMap)
        # # for each flow --> allocate a port in the dest host for server side communication and one for client sidecommunication in clinet side
        # # Build a list of object for server side commands and client side commands.
        # # This list will be saved in each host's map.
        # #at last we will deploy everything in a host at once --> at first server side then client side


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
    def genIPerfCommands(self, nameToHostMap, maxPortcountInSwitch):
        deploymentPairList = []
        for t in self.tests:
            val = t.getIDeploymentPairs(nameToHostMap,maxPortcountInSwitch)
            deploymentPairList = deploymentPairList + val
        return  deploymentPairList



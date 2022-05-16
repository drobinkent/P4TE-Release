# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = welcome_from_dict(json.loads(json_string))

import math
import queue
import sys
import traceback

from DistributedAlgorithms.RoutingInfo import RoutingInfo

print(sys.path)
import threading
from dataclasses import dataclass
import time
from typing import Any, List, Dict, TypeVar, Callable, Type, cast
from enum import Enum

from google.rpc import code_pb2
from p4.v1 import p4runtime_pb2

import ConfigConst as ConfConst

import subprocess
import InternalConfig
import P4Runtime.shell as sh
from P4Runtime.context import Context, P4RuntimeEntity
from P4Runtime.p4runtime import P4RuntimeClient, P4RuntimeException, parse_p4runtime_error
import P4Runtime.leafSwitchUtils as leafUtils
import P4Runtime.spineSwitchUtils as spineUtils
import P4Runtime.superSpineSwitchUtils as superSpineUtils
import P4Runtime.SwitchUtils as swUtils
import ConfigConst
import P4Runtime.packetUtils as pktUtil
import P4Runtime.PortStatistics as ps

import collections as collections
# logger.basicConfig(level=logger.DEBUG)
import logging
import logging.handlers
logger = logging.getLogger('JsonParser')
logger.handlers = []
hdlr = logging.handlers.RotatingFileHandler(ConfConst.CONTROLLER_LOG_FILE_PATH, maxBytes = ConfConst.MAX_LOG_FILE_SIZE , backupCount= ConfConst.MAX_LOG_FILE_BACKUP_COUNT)
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                              '%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)

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
    return {k: f(v) for (k, v) in x.items()}


@dataclass
class Link:
    node1: str
    node2: str
    port2: int
    bw: int
    port1: int

    @staticmethod
    def from_dict(obj: Any) -> 'Link':
        assert isinstance(obj, dict)
        node1 = from_str(obj.get("node1"))
        node2 = from_str(obj.get("node2"))
        port1 = from_int(obj.get("port1"))
        port2 = from_int(obj.get("port2"))
        bw = from_int(obj.get("bw"))
        return Link(node1, node2, port2, bw, port1)

    def to_dict(self) -> dict:
        result: dict = {}
        result["node1"] = from_str(self.node1)
        result["node2"] = from_str(self.node2)
        result["port1"] = from_int(self.port1)
        result["port2"] = from_int(self.port2)
        return result


@dataclass
class Alllinks:
    links: List[Link]

    @staticmethod
    def from_dict(obj: Any) -> 'Alllinks':
        assert isinstance(obj, dict)
        links = from_list(Link.from_dict, obj.get("links"))
        return Alllinks(links)

    def to_dict(self) -> dict:
        result: dict = {}
        result["links"] = from_list(lambda x: to_class(Link, x), self.links)
        return result


class Driver(Enum):
    BMV2 = "bmv2"


class Pipeconf(Enum):
    ORG_MEDIANET_DCN_TE_LEAF = "org.medianet.dcn-te-leaf"
    ORG_MEDIANET_DCN_TE_SPINE = "org.medianet.dcn-te-spine"
    ORG_MEDIANET_DCN_TE_SUPER_SPINE = "org.medianet.dcn-te-super-spine"


class DeviceType(Enum):
    INVALID = -1
    HOST = 0
    LEAF_SWITCH = 1
    SPINE_SWITCH = 2
    SUPER_SPINE_SWITCH = 3

    def __str__(self):
        val = self
        if val == DeviceType.INVALID:
            return "DEV TYPE: INVALID "
        elif val == DeviceType.HOST:
            return "DEV TYPE: HOST "
        elif val == DeviceType.LEAF_SWITCH:
            return "DEV TYPE: LEAF_SWITCH "
        elif val == DeviceType.SPINE_SWITCH:
            return "DEV TYPE: SPINE_SWITCH "
        elif val == DeviceType.SUPER_SPINE_SWITCH:
            return "DEV TYPE: SUPER_SPINE_SWITCH "
        else:
            return "DEV TYPE: INVALID "


@dataclass
class DeviceBasic:
    management_address: str
    driver: Driver
    pipeconf: Pipeconf
    thirftPort: int

    @staticmethod
    def from_dict(obj: Any) -> 'DeviceBasic':
        assert isinstance(obj, dict)
        management_address = from_str(obj.get("managementAddress"))
        driver = Driver(obj.get("driver"))
        pipeconf = Pipeconf(obj.get("pipeconf"))
        thirftPort = from_str(obj.get("thirftPort"))
        return DeviceBasic(management_address, driver, pipeconf, thirftPort)

    def to_dict(self) -> dict:
        result: dict = {}
        result["managementAddress"] = from_str(self.management_address)
        result["driver"] = to_enum(Driver, self.driver)
        result["pipeconf"] = to_enum(Pipeconf, self.pipeconf)
        return result


class SwitchType(Enum):
    LEAF = "Leaf"
    SPINE = "Spine"
    SUPER_SPINE = "SuperSpine"


@dataclass
class FabricDeviceConfig:
    my_station_mac: str
    switch_type: SwitchType
    switch_host_subnet_prefix: str

    @staticmethod
    def from_dict(obj: Any) -> 'FabricDeviceConfig':
        assert isinstance(obj, dict)
        my_station_mac = from_str(obj.get("myStationMac"))
        switch_type = SwitchType(obj.get("switchType"))
        switch_host_subnet_prefix = from_str(obj.get("switchHostSubnetPrefix"))
        return FabricDeviceConfig(my_station_mac, switch_type, switch_host_subnet_prefix)

    def to_dict(self) -> dict:
        result: dict = {}
        result["myStationMac"] = from_str(self.my_station_mac)
        result["switchType"] = to_enum(SwitchType, self.switch_type)
        result["switchHostSubnetPrefix"] = from_str(self.switch_host_subnet_prefix)
        return result


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
    hostName: str
    basic: BasicElement
    fabric_host_config: FabricHostConfig

    def __init__(self, hostName, basic, fabric_host_config):
        self.hostName = hostName
        self.basic = basic
        self.fabric_host_config = fabric_host_config
        self.portToLeafSwitchMap = {}

    @staticmethod
    def from_dict(obj: Any) -> 'Host':
        assert isinstance(obj, dict)
        basic = BasicElement.from_dict(obj.get("basic"))
        fabric_host_config = FabricHostConfig.from_dict(obj.get("fabricHostConfig"))
        return Host(basic.name, basic, fabric_host_config)

    def to_dict(self) -> dict:
        result: dict = {}
        result["basic"] = to_class(BasicElement, self.basic)
        result["fabricHostConfig"] = to_class(FabricHostConfig, self.fabric_host_config)
        return result

    def getLocationIndexes(self):
        hostIndex = self.basic.name[self.basic.name.index("h") + 1: self.basic.name.index("p")]
        podIndex = self.basic.name[self.basic.name.index("p") + 1: self.basic.name.index("l")]
        leafSwitchIndex = self.basic.name[self.basic.name.index("l") + 1: len(self.basic.name)]
        return hostIndex, leafSwitchIndex, podIndex


@dataclass
class Port:
    interfaces: List[BasicElement]

    @staticmethod
    def from_dict(obj: Any) -> 'Port':
        assert isinstance(obj, dict)
        interfaces = from_list(BasicElement.from_dict, obj.get("interfaces"))
        return Port(interfaces)

    def to_dict(self) -> dict:
        result: dict = {}
        result["interfaces"] = from_list(lambda x: to_class(BasicElement, x), self.interfaces)
        return result


# @dataclass
# class Welcome:
#     devices: Dict[str, Device]
#     ports: Dict[str, Port]
#     hosts: Dict[str, Host]
#     alllinks: Alllinks
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Welcome':
#         assert isinstance(obj, dict)
#         devices = from_dict(Device.from_dict, obj.get("devices"))
#         ports = from_dict(Port.from_dict, obj.get("ports"))
#         hosts = from_dict(Host.from_dict, obj.get("hosts"))
#         alllinks = Alllinks.from_dict(obj.get("alllinks"))
#         return Welcome(devices, ports, hosts, alllinks)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["devices"] = from_dict(lambda x: to_class(Device, x), self.devices)
#         result["ports"] = from_dict(lambda x: to_class(Port, x), self.ports)
#         result["hosts"] = from_dict(lambda x: to_class(Host, x), self.hosts)
#         result["alllinks"] = to_class(Alllinks, self.alllinks)
#         return result
#
#
# def welcome_from_dict(s: Any) -> Welcome:
#     return Welcome.from_dict(s)
#
#
# def welcome_to_dict(x: Welcome) -> Any:
#     return to_class(Welcome, x)


@dataclass
class Device:
    devName: str
    basic: DeviceBasic
    fabric_device_config: FabricDeviceConfig

    def __init__(self, devName, basic, fabric_device_config, dpAlgo):
        self.devName = devName
        self.basic = basic
        self.fabric_device_config = fabric_device_config
        self.portToHostMap = {}
        self.portToSpineSwitchMap = {}
        self.portToLeafSwitchMap = {}
        self.portToSuperSpineSwitchMap = {}
        self.multicastGroupDatabase = {}
        self.packetOutLock = threading.Lock()
        self.cliLock = threading.Lock()
        self.p4runtimeLock = threading.Lock()
        self.portToQueueRateMap = {}
        self.portToQueueDepthMap = {}
        self.maxPort = ConfigConst.MAX_PORT_NUMBER
        self.portStatisticsCollection = collections.deque(maxlen=ConfigConst.PORT_STATISTICS_HISTORY_LENGTH)
        self.dpAlgorithm = dpAlgo
        self.ctrlPlaneLogic = swUtils.getAlgo(self, self.dpAlgorithm)
        if (fabric_device_config.switch_type == SwitchType.LEAF):
            self.p4infoFilePath = ConfConst.LEAF_P4_INFO_FILE_PATH
            self.bmv2_json_file_path = ConfConst.LEAF_BMV2_JSON_FILE_PATH
        elif (fabric_device_config.switch_type == SwitchType.SPINE):
            self.p4infoFilePath = ConfConst.SPINE_P4_INFO_FILE_PATH
            self.bmv2_json_file_path = ConfConst.SPINE_BMV2_JSON_FILE_PATH
        elif (fabric_device_config.switch_type == SwitchType.SUPER_SPINE):
            self.p4infoFilePath = ConfConst.SUPER_SPINE_P4_INFO_FILE_PATH
            self.bmv2_json_file_path = ConfConst.SUPER_SPINE_BMV2_JSON_FILE_PATH
        else:
            print("Severe Problem. Unknows Switch Type. Exiting")
            exit(-1)
        self.config = sh.FwdPipeConfig(self.p4infoFilePath, self.bmv2_json_file_path)
        s = self.basic.management_address.index("device_id=") + len("device_id=")
        tempString = self.basic.management_address[s:len(self.basic.management_address)]
        self.device_id = int(tempString)
        s = self.basic.management_address.index("grpc://") + len("grpc://")
        e = self.basic.management_address.index("?device_id=")
        self.grpcAddress = self.basic.management_address[s:e]
        self.election_id = (1, 0)
        self.client, self.context = self.setup(device_id=self.device_id, grpc_addr=self.grpcAddress,
                                               election_id=self.election_id, config=self.config)
        print("Initialized grpc channel for device ", self.devName)

        # TODO we have to put some selecion logic here

    @staticmethod
    def from_dict(devName, obj: Any, dpAlgo) -> 'Device':
        assert isinstance(obj, dict)
        basic = DeviceBasic.from_dict(obj.get("basic"))
        fabric_device_config = FabricDeviceConfig.from_dict(obj.get("fabricDeviceConfig"))
        return Device(devName, basic, fabric_device_config, dpAlgo)

    def to_dict(self) -> dict:
        result: dict = {}
        result["basic"] = to_class(DeviceBasic, self.basic)
        result["fabricDeviceConfig"] = to_class(FabricDeviceConfig, self.fabric_device_config)
        return result

    def setup(self, device_id=1, grpc_addr='localhost:50051', election_id=(1, 0), config=None):
        logger.debug("Creating P4Runtime client")
        self.client = P4RuntimeClient(device_id, grpc_addr, election_id)
        self.set_up_stream()

        if config is not None:
            try:
                p4info_path = config.p4info
                bin_path = config.bin
            except Exception:
                raise ValueError("Argument 'config' must be a FwdPipeConfig namedtuple")

            try:
                self.client.set_fwd_pipe_config(p4info_path, bin_path)
            except FileNotFoundError as e:
                logger.critical(e)
                self.client.tear_down()
                sys.exit(1)
            except P4RuntimeException as e:
                logger.critical("Error when setting config")
                logger.critical(e)
                self.client.tear_down()
                sys.exit(1)
            except Exception:
                logger.critical("Error when setting config")
                self.client.tear_down()
                sys.exit(1)

        try:
            p4info = self.client.get_p4info()
        except P4RuntimeException as e:
            logger.critical("Error when retrieving P4Info")
            logger.critical(e)
            self.client.tear_down()
            sys.exit(1)

        logger.debug("Parsing P4Info message")
        self.context = Context()
        self.context.set_p4info(p4info)
        return self.client, self.context

    # TOOD : this should teardown channels for all the device
    def teardown(self):
        logger.debug("Tearing down P4Runtime client")
        self.client.tear_down()
        client = None

    def set_up_stream(self):
        self.stream_out_q = queue.Queue()
        self.stream_in_q = queue.Queue()

        def stream_req_iterator():
            while True:
                p = self.stream_out_q.get()
                if p is None:
                    break
                yield p

        def stream_recv_wrapper(stream):
            @parse_p4runtime_error
            def stream_recv():
                print("Waitint for stream rcv in ", str(stream))
                for p in stream:
                    self.stream_in_q.put(p)
                    #print("Entered new pkt in ", self.devName)

            try:
                stream_recv()
            except P4RuntimeException as e:
                logger.critical("StreamChannel error, closing stream")
                logger.critical(e)
                self.stream_in_q.put(None)

        self.stream = self.client.stub.StreamChannel(stream_req_iterator())
        self.stream_recv_thread = threading.Thread(
            target=stream_recv_wrapper, args=(self.stream,))
        self.stream_recv_thread.start()
        if (self.handshake()):
            logger.debug("Handshake completed for device " + self.devName + ". Now opening processor thread")
        self.processor_stream_thread = threading.Thread(
            target=self.pkt_processor, args=())
        self.processor_stream_thread.start()
        print("Pkt processor thread started")

    def pkt_processor(self, ):
        try:
            while (True):
                pkt = self.stream_in_q.get()
                if pkt.HasField(
                        "packet"):  # look at the StreamMessageResponse in the protobuf definitions. "packet is for packet-in
                    # logger.info(self.devName+" rcvd a pkt. metadata is "+str(pkt.packet.metadata))#+ "payload is " , bytes(pkt.packet.payload).hex())
                    parsedPkt = pktUtil.ControlPacket(pkt.packet)
                    # print("Received packet is "+str(parsedPkt))
                    # logger.info("The parsed control packet  is"+str(parsedPkt))
                    self.ctrlPlaneLogic.processFeedbackPacket(parsedPkt, self)
                    # swUtils.readAllCounters(self)
                    # swUtils.resetAllCounters(self)
                else:
                    logger.info("Unknown pakt")
        except Exception as e:
            logger.info("Error in pkt rcvr thread for device "+ str( self.devName) + " error is ",e)
            #logger.info(e)

    def handshake(self):
        req = p4runtime_pb2.StreamMessageRequest()
        arbitration = req.arbitration
        arbitration.device_id = self.device_id
        election_id = arbitration.election_id
        election_id.high = self.election_id[0]
        election_id.low = self.election_id[1]
        self.stream_out_q.put(req)

        rep = self.get_stream_packet("arbitration", timeout=2)
        if rep is None:
            logger.critical("Failed to establish session with server for ", self.grpc_addr)
            sys.exit(1)
        is_master = (rep.arbitration.status.code == code_pb2.OK)
        logger.debug("Session established, client is '{}'".format(
            'master' if is_master else 'slave'))
        if not is_master:
            print("You are not master, you only have read access to the server")
        return is_master

    def get_stream_packet(self, type_, timeout=1):
        start = time.time()
        try:
            while True:
                remaining = timeout - (time.time() - start)
                if remaining < 0:
                    break
                msg = self.stream_in_q.get(timeout=remaining)
                if msg is None:
                    return None
                if not msg.HasField(type_):
                    continue
                return msg
        except queue.Empty:  # timeout expired
            pass
        return None

    def send_packet_out(self, pkt, port, clnt):
        self.packetOutLock.acquire(blocking=True)
        packet_out_req = p4runtime_pb2.StreamMessageRequest()

        # port_hex = stringify(port, 2)
        port_hex = port.to_bytes(length=2, byteorder="big")
        packet_out = p4runtime_pb2.PacketOut()
        packet_out.payload = pkt.encode()
        egress_physical_port = packet_out.metadata.add()
        egress_physical_port.metadata_id = 1
        egress_physical_port.value = port_hex

        packet_out_req.packet.CopyFrom(packet_out)
        clnt.stream_out_q.put(packet_out_req)
        self.packetOutLock.release()

    def hostDiscoverySetup(self):
        # This function only works for leaf switch. and is necessary for NDP setup. So irrespective of any test scenario we have this is mandatory
        if self.fabric_device_config.switch_type == SwitchType.LEAF:
            self.addMultiCastGroup(list(self.portToHostMap.keys()), InternalConfig.LEAF_SWITCH_HOST_MULTICAST_GROUP)
            leafUtils.addL2TernaryEntryForMulticast(self)
            self.addExactMatchEntryNoAction(
                tableName="IngressPipeImpl.my_station_processing_control_block.my_station_table",
                fieldName="hdr.ethernet.dst_addr", fieldValue=self.fabric_device_config.my_station_mac)
            leafUtils.addNDPentries(self)
            leafUtils.addDownstreamRoutingRuleForLeafSwitch(self)
            leafUtils.addUpStreamRoutingGroupForLeafSwitch(self, list(
                self.portToSpineSwitchMap.keys()))  # this creates a group for upstream routing with  group_id=InternalConfig.LEAF_SWITCH_UPSTREAM_PORTS_GROUP
            self.addLPMMatchEntryWithGroupAction(
                tableName="IngressPipeImpl.upstream_routing_control_block.upstream_routing_table",
                fieldName="hdr.ipv6.dst_addr",
                fieldValue=InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength=InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
                actionName="IngressPipeImpl.upstream_routing_control_block.set_upstream_egress_port",
                actionParamName=None, actionParamValue=None,
                groupID=InternalConfig.LEAF_SWITCH_UPSTREAM_PORTS_GROUP, priority=None)

            return

    def createAndAddMemeberToActionProfileGroup(self, actionProfileGroupObject, selectorName, memebrId, actionName,
                                                actionParamName, actionParamValue):
        member = sh.ActionProfileMember(self, selectorName)(member_id=memebrId, action=actionName)
        member.action[actionParamName] = str(actionParamValue)
        member.insert()
        actionProfileGroupObject.add(member.member_id)
        actionProfileGroupObject.modify()
        return member

    def addGroupforDelayBasedRouting(self, upstreamPortsList=None):
        group4 = sh.ActionProfileGroup(self, "IngressPipeImpl.delay_based_upstream_path_selector")(group_id=3)
        group3 = sh.ActionProfileGroup(self, "IngressPipeImpl.delay_based_upstream_path_selector")(group_id=4)
        group2 = sh.ActionProfileGroup(self, "IngressPipeImpl.delay_based_upstream_path_selector")(group_id=5)
        group1 = sh.ActionProfileGroup(self, "IngressPipeImpl.delay_based_upstream_path_selector")(group_id=6)

        group4.insert()
        group3.insert()
        group2.insert()
        group1.insert()

        upstreamPortsList = [3]
        for i in range(0, len(upstreamPortsList)):
            member = sh.ActionProfileMember(self, "IngressPipeImpl.delay_based_upstream_path_selector")(
                member_id=upstreamPortsList[i], action="delay_based_upstream_path_selector_action_with_param")
            member.action["port_num"] = str(upstreamPortsList[i])
            member.insert()
            # group4.add(member.member_id)
            # group3.add(member.member_id)
            group2.add(member.member_id)
            # group1.add(member.member_id)
        upstreamPortsList = [4]
        for i in range(0, len(upstreamPortsList)):
            member = sh.ActionProfileMember(self, "IngressPipeImpl.delay_based_upstream_path_selector")(
                member_id=upstreamPortsList[i], action="delay_based_upstream_path_selector_action_with_param")
            member.action["port_num"] = str(upstreamPortsList[i])
            member.insert()
            # group4.add(member.member_id)
            # group3.add(member.member_id)
            group4.add(member.member_id)
            # group1.add(member.member_id)
        for i in range(128, 140):
            member = sh.ActionProfileMember(self, "IngressPipeImpl.delay_based_upstream_path_selector")(member_id=i,
                                                                                                        action="delay_based_upstream_path_selector_action_with_param")
            member.action["port_num"] = str(i)
            member.insert()
            group3.add(member.member_id)

        group4.modify()
        group3.modify()
        group2.modify()
        group1.modify()

    def setupECMPUpstreamRouting(self):
        '''
        This function setup all the relevant stuffs for running the algorithm
        '''

        if self.fabric_device_config.switch_type == SwitchType.LEAF:
            leafUtils.addUpStreamRoutingGroupForLeafSwitch(self, list(
                self.portToSpineSwitchMap.keys()))  # this creates a group for upstream routing with  group_id=InternalConfig.LEAF_SWITCH_UPSTREAM_PORTS_GROUP
            self.addLPMMatchEntryWithGroupAction(
                tableName="IngressPipeImpl.upstream_ecmp_routing_control_block.upstream_routing_table",
                fieldName="hdr.ipv6.dst_addr",
                fieldValue=InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength=InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
                actionName="IngressPipeImpl.upstream_ecmp_routing_control_block.set_upstream_egress_port",
                actionParamName=None, actionParamValue=None,
                groupID=InternalConfig.LEAF_SWITCH_UPSTREAM_PORTS_GROUP, priority=None)
            return
        elif self.fabric_device_config.switch_type == SwitchType.SPINE:
            spineUtils.addUpStreamRoutingGroupForSpineSwitch(self, list(
                self.portToSuperSpineSwitchMap.keys()))  # this creates a group for upstream routing with  group_id=InternalConfig.SPINE_SWITCH_UPSTREAM_PORTS_GROUP
            if (len(list(self.portToSuperSpineSwitchMap.keys()))<=0):
                pass
            else:
                self.addLPMMatchEntryWithGroupAction(
                    tableName="IngressPipeImpl.upstream_ecmp_routing_control_block.upstream_routing_table",
                    fieldName="hdr.ipv6.dst_addr",
                    fieldValue=InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength=InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
                    actionName="IngressPipeImpl.upstream_ecmp_routing_control_block.set_upstream_egress_port",
                    actionParamName=None, actionParamValue=None,
                    groupID=InternalConfig.SPINE_SWITCH_UPSTREAM_PORTS_GROUP, priority=None)
            pass
        elif self.fabric_device_config.switch_type == SwitchType.SUPER_SPINE:
            pass
        return

    def initialCommonSetup(self):
        '''This funciotn setup dataplane entries for various muslticast grousp and NDP entries and downstream routing in each switch. Irrespective of
        Dataplane algorithms these tasks are common.
        '''
        if self.fabric_device_config.switch_type == SwitchType.LEAF:
            self.addMultiCastGroup(list(self.portToHostMap.keys()), InternalConfig.LEAF_SWITCH_HOST_MULTICAST_GROUP)
            leafUtils.addL2TernaryEntryForMulticast(self)
            self.addExactMatchEntryNoAction(
                tableName="IngressPipeImpl.my_station_processing_control_block.my_station_table",
                fieldName="hdr.ethernet.dst_addr", fieldValue=self.fabric_device_config.my_station_mac)
            leafUtils.addNDPentries(self)
            leafUtils.addDownstreamRoutingRuleForLeafSwitch(self)
        elif self.fabric_device_config.switch_type == SwitchType.SPINE:
            spineUtils.addDownstreamRoutingRuleForSpineSwitch(self)
        elif self.fabric_device_config.switch_type == SwitchType.SUPER_SPINE:
            superSpineUtils.addDownstreamRoutingRuleForSuperSpineSwitch(self)



        return

    def queueRateSetupForLeafSwitch(self, queueRateForHostFacingPortsOfLeafSwitch,
                                    queueRateForSpineFacingPortsOfLeafSwitch, queueRateToDepthFactor):
        self.queueRateForHostFacingPortsOfLeafSwitch = queueRateForHostFacingPortsOfLeafSwitch
        self.queueRateForSpineFacingPortsOfLeafSwitch = queueRateForSpineFacingPortsOfLeafSwitch
        leafUtils.setPortQueueRatesAndDepth(self, self.queueRateForHostFacingPortsOfLeafSwitch,
                                            self.queueRateForSpineFacingPortsOfLeafSwitch, queueRateToDepthFactor)

    def queueRateSetupForSpineSwitch(self, queueRateForLeafSwitchFacingPortsOfSpineSwitch,
                                     queueRateForSuperSpineSwitchFacingPortsOfSpineSwitch, queueRateToDepthFactor):
        self.queueRateForLeafSwitchFacingPortsOfSpineSwitch = queueRateForLeafSwitchFacingPortsOfSpineSwitch
        self.queueRateForSuperSpineSwitchFacingPortsOfSpineSwitch = queueRateForSuperSpineSwitchFacingPortsOfSpineSwitch
        spineUtils.setPortQueueRatesAndDepth(self, self.queueRateForLeafSwitchFacingPortsOfSpineSwitch,
                                             self.queueRateForSuperSpineSwitchFacingPortsOfSpineSwitch,
                                             queueRateToDepthFactor)

    def queueRateSetupForSuperspineSwitch(self, queueRateForSpineSwitchFacingPortsOfSuperSpineSwitch,
                                          queueRateForExternalInternetFacingPortsOfSuperSpineSwitch,
                                          queueRateToDepthFactor):
        self.queueRateForSpineSwitchFacingPortsOfSuperSpineSwitch = queueRateForSpineSwitchFacingPortsOfSuperSpineSwitch
        self.queueRateForExternalInternetFacingPortsOfSuperSpineSwitch = queueRateForExternalInternetFacingPortsOfSuperSpineSwitch
        superSpineUtils.setPortQueueRatesAndDepth(self, self.queueRateForSpineSwitchFacingPortsOfSuperSpineSwitch,
                                                  self.queueRateForExternalInternetFacingPortsOfSuperSpineSwitch,
                                                  queueRateToDepthFactor)

    def setPortQueueRate(self, portId, portQueueRate):
        self.portToQueueRateMap[str(portId)] = int(portQueueRate)

    def setPortQueueDepth(self, portId, portQueueDepth):
        self.portToQueueDepthMap[str(portId)] = int(portQueueDepth)

    def addMultiCastGroup(self, listOfPorts, mcastGroupId):
        if (self.multicastGroupDatabase.get(mcastGroupId) != None):
            logger.info("Multicast group ", str(mcastGroupId) + " already exits. Can not add exititing!!")
            exit(1)
        mcge = sh.MulticastGroupEntry(self, mcastGroupId)
        for i in range(0, len(listOfPorts)):
            p = listOfPorts[i]
            mcge.add(p)
        mcge.insert()
        logger.debug("Entered Multicast group for switch" + self.devName + " with " + str(len(listOfPorts)) + " Ports")

    #
    # Set a field value with <self>['<field_name>'] = '...'
    # * For exact match: <self>['<f>'] = '<value>'
    # * For ternary match: <self>['<f>'] = '<value>&&&<mask>'
    # * For LPM match: <self>['<f>'] = '<value>/<mask>'
    # * For range match: <self>['<f>'] = '<value>..<mask>'

    def addRangeMatchEntry(self, tableName, actionName, actionParamName, actionParamValue, matachField1,
                           matchFieldValue1, matachField2, low, high):
        te = sh.TableEntry(self, tableName)(action=actionName)
        prefixLen = 10 - (int(math.floor(math.log(matchFieldValue1, 2))))
        # if prefixLen <=0:
        #     prefixLen = prefixLen+1
        # else:
        #     prefixLen = math.ceil(prefixLen)
        # if prefixLen>= 8:
        #     logger.info("Ports can not be more than 8 bit. So exiting!!")
        #     exit(1)
        # prefixLen = 8-prefixLen
        # te.match[matachField1] = str(matchFieldValue1)+"&&&"+ "0x00"
        te.match[matachField1] = str(0) + "/" + str(1)
        te.match[matachField2] = str(low) + ".." + str(high)  # "0..1024"
        te.action[actionParamName] = str(actionParamValue)
        te.priority = int(actionParamValue)
        te.insert()
        return

    def addTernaryMatchEntry(self, tableName, fieldName, fieldValue, mask, actionName, actionParamName,
                             actionParamValue, priority=InternalConfig.DEFAULT_PRIORITY):
        te = sh.TableEntry(self, tableName)(action=actionName)
        te.match[fieldName] = "" + fieldValue + " &&& " + mask
        te.action[actionParamName] = actionParamValue
        te.priority = priority
        te.insert()

    def addLPMMatchEntryMultipleActionParameter(self, tableName, fieldName, fieldValue, prefixLength, actionName,
                                                actionParamNameList, actionParamValueList, groupID=None,
                                                priority=InternalConfig.DEFAULT_PRIORITY):
        te = sh.TableEntry(self, tableName)(action=actionName)
        te.match[fieldName] = "" + fieldValue + "/" + prefixLength
        if (len(actionParamNameList) != len(actionParamValueList)):
            logger.info("number of parameters for action and correspoding values are not matching in count")
        else:
            for i in range(0, len(actionParamNameList)):
                te.action[actionParamNameList[i]] = str(actionParamValueList[i])
        if (groupID != None):
            te.group_id = groupID
        te.insert()

    def addLPMMatchEntry(self, tableName, fieldName, fieldValue, prefixLength, actionName, actionParamName,
                         actionParamValue, priority=InternalConfig.DEFAULT_PRIORITY):
        te = sh.TableEntry(self, tableName)(action=actionName)
        te.match[fieldName] = "" + fieldValue + "/" + str(prefixLength)
        if ((actionParamName != None) and (actionParamValue != None)):
            te.action[actionParamName] = actionParamValue
        te.insert()

    def removeLPMMatchEntryWithGroupActionWithRangeField(self, tableName, fieldName, fieldValue, prefixLength,
                                                         rangeFieldName, rangeFieldLowerValue, rangefieldHigherValue,
                                                         actionName, actionParamName, actionParamValue, groupID=None,
                                                         priority=None):
        te = sh.TableEntry(self, tableName)
        te.match[fieldName] = "" + fieldValue + "/" + str(prefixLength)
        te.match[rangeFieldName] = str(rangeFieldLowerValue) + ".." + str(rangefieldHigherValue)  # "0..1024"
        if ((actionParamName != None) and (actionParamValue != None)):
            te.action[actionParamName] = actionParamValue
        if priority != None:
            te.priority = priority
        if (groupID != None):
            te.group_id = groupID
        te.delete()

    def addLPMMatchEntryWithGroupActionWithRangeField(self, tableName, fieldName, fieldValue, prefixLength,
                                                      rangeFieldName, rangeFieldLowerValue, rangefieldHigherValue,
                                                      actionName, actionParamName, actionParamValue, groupID=None,
                                                      priority=None):
        te = sh.TableEntry(self, tableName)
        te.match[fieldName] = "" + fieldValue + "/" + str(prefixLength)
        te.match[rangeFieldName] = str(rangeFieldLowerValue) + ".." + str(rangefieldHigherValue)  # "0..1024"
        if ((actionParamName != None) and (actionParamValue != None)):
            te.action[actionParamName] = actionParamValue
        if priority != None:
            te.priority = priority
        if (groupID != None):
            te.group_id = groupID
        te.insert()

    # TODO : here we are addin 3 range field. but ideally it should be a list of fields. Later we will do this.
    def addLPMMatchEntryWithGroupActionWith2RangeField(self, tableName, fieldName, fieldValue, prefixLength,
                                                       rangeField1Name, rangeField1LowerValue, rangefield1HigherValue,
                                                       rangeField2Name, rangeField2LowerValue, rangefield2HigherValue,
                                                       actionName, actionParamName, actionParamValue, groupID=None,
                                                       priority=None):
        te = sh.TableEntry(self, tableName)
        te.match[fieldName] = "" + fieldValue + "/" + str(prefixLength)
        te.match[rangeField1Name] = str(rangeField1LowerValue) + ".." + str(rangefield1HigherValue)  # "0/1024"
        te.match[rangeField2Name] = str(rangeField2LowerValue) + ".." + str(rangefield2HigherValue)  # "0/1024"
        if ((actionParamName != None) and (actionParamValue != None)):
            te.action[actionParamName] = actionParamValue
        if priority != None:
            te.priority = priority
        if (groupID != None):
            te.group_id = groupID
        te.insert()


    # TODO: this function at first deltes a table entry then re-enter the modifed entr. But it should be a litte bit differnt I guess. It should only modify the existing entry.
    # ?Need to check the doccumentation
    def modifyLPMMatchEntryWithGroupActionWith2RangeField(self, tableName, fieldName, fieldValue, prefixLength,
                                                       rangeField1Name, rangeField1LowerValue, rangefield1HigherValue,
                                                       rangeField2Name, rangeField2LowerValue, rangefield2HigherValue,  # old fields are required to find table entries.
                                                        rangeField2ModifedLowerValue, rangefield2ModifiedHigherValue,
                                                       actionName, actionParamName, actionParamValue, groupID=None,
                                                       priority=None):
        # self.p4runtimeLock.acquire(blocking=True)
        # o,e = self.executeCommand("table_dump "+ tableName+"\n")
        # logger.info(str(self.devName)+ "At start of modifyLPMMatchEntryWithGroupActionWith2RangeField"+str(o))
        te = sh.TableEntry(self, tableName)
        te.match[fieldName] = "" + fieldValue + "/" + str(prefixLength)
        te.match[rangeField1Name] = str(rangeField1LowerValue) + ".." + str(rangefield1HigherValue)  # "0/1024"
        te.match[rangeField2Name] = str(rangeField2LowerValue) + ".." + str(rangefield2HigherValue)  # "0/1024"
        if ((actionParamName != None) and (actionParamValue != None)):
            te.action[actionParamName] = actionParamValue
        if priority != None:
            te.priority = priority
        if (groupID != None):
            te.group_id = groupID
        te.delete()
        te._update_msg()
        # o,e = self.executeCommand("table_dump "+ tableName+"\n")
        # logger.info(str(self.devName)+ "After dlting old entry "+str(o))
        #logger.info("Deleted TE is "+te._info)
        te = sh.TableEntry(self, tableName)
        te.match[fieldName] = "" + fieldValue + "/" + str(prefixLength)
        te.match[rangeField1Name] = str(rangeField1LowerValue) + ".." + str(rangefield1HigherValue)  # "0/1024"
        te.match[rangeField2Name] = str(rangeField2ModifedLowerValue) + ".." + str(rangefield2ModifiedHigherValue)  # "0/1024"
        if ((actionParamName != None) and (actionParamValue != None)):
            te.action[actionParamName] = actionParamValue
        if priority != None:
            te.priority = priority
        if (groupID != None):
            te.group_id = groupID
        te.insert()
        #logger.info("Inserted TE is ",te._info)
        # o,e = self.executeCommand("table_dump "+ tableName+"\n")
        # logger.info(str(self.devName)+ "After inserting  new entry "+str(o))
        # self.p4runtimeLock.release()



    def addLPMMatchEntryWithGroupAction(self, tableName, fieldName, fieldValue, prefixLength, actionName,
                                        actionParamName, actionParamValue, groupID=None, priority=None):
        te = sh.TableEntry(self, tableName)
        te.match[fieldName] = "" + fieldValue + "/" + str(prefixLength)
        if ((actionParamName != None) and (actionParamValue != None)):
            te.action[actionParamName] = actionParamValue
        if priority != None:
            te.priority = priority
        if (groupID != None):
            te.group_id = groupID
        te.insert()

    def removeLPMMatchEntryWithGroupAction(self, tableName, fieldName, fieldValue, prefixLength, actionName,
                                           actionParamName, actionParamValue, groupID=None,
                                           priority=InternalConfig.DEFAULT_PRIORITY):
        te = sh.TableEntry(self, tableName)
        te.match[fieldName] = "" + fieldValue + "/" + str(prefixLength)
        if ((actionParamName != None) and (actionParamValue != None)):
            te.action[actionParamName] = actionParamValue
        # te.priority = priority
        if (groupID != None):
            te.group_id = groupID
        te.delete()

    def addExactMatchEntry(self, tableName, fieldName, fieldValue, actionName, actionParamName, actionParamValue):
        te = sh.TableEntry(self, tableName)(action=actionName)
        te.match[fieldName] = "" + fieldValue
        te.action[actionParamName] = actionParamValue
        te.insert()

    def addExactMatchEntryWithMultipleField(self, tableName, fieldNameList, fieldValueList, actionName, actionParamName,
                                            actionParamValue):
        if (len(fieldNameList) != len(fieldValueList)):
            logger.info("Can not insert exact match entries. Because number of field and values are not equal")
        te = sh.TableEntry(self, tableName)(action=actionName)
        # te.match[fieldName] = "" + fieldValue
        te.action[actionParamName] = actionParamValue
        for i in range(0, len(fieldValueList)):
            te.match[fieldNameList[i]] = "" + str(fieldValueList[i])
        te.insert()
    def addExactMatchEntryWithMultipleFieldMultipleActionParam(self, tableName, fieldNameList, fieldValueList, actionName, actionParamNameList,
                                            actionParamValueList):
        if (len(fieldNameList) != len(fieldValueList)):
            logger.info("Can not insert exact match entries. Because number of field and values are not equal")
        te = sh.TableEntry(self, tableName)(action=actionName)
        if len(fieldNameList) != len(fieldValueList):
            logger.info("Number of match field and  number of values for them are not matching. Severe Problem. Exiting!!")
            exit(1)
        if len(actionParamNameList) != len(actionParamValueList):
            logger.info("Number of action parameters and  number of values for them are not matching. Severe Problem. Exiting!!")
            exit(1)
        for i in range(0, len(fieldValueList)):
            te.match[fieldNameList[i]] = "" + str(fieldValueList[i])
        for i in range(0, len(actionParamNameList)):
            te.match[actionParamNameList[i]] = "" + str(actionParamValueList[i])

        te.insert()

    def addExactMatchEntryWithoutActionParam(self, tableName, fieldName, fieldValue, actionName):
        te = sh.TableEntry(self, tableName)(action=actionName)
        te.match[fieldName] = "" + fieldValue
        te.insert()

    def addExactMatchEntryNoAction(self, tableName, fieldName, fieldValue):
        te = sh.TableEntry(self, tableName)(action="NoAction")
        te.match[fieldName] = "" + fieldValue
        # te.action[actionParamName] = actionParamValue
        te.insert()

    def addExactMatchEntryWithMultipleActionParameter(self, tableName, fieldName, fieldValue, actionName,
                                                      actionParamNameList, actionParamValueList):
        te = sh.TableEntry(self, tableName)(action=actionName)
        te.match[fieldName] = "" + fieldValue
        if (len(actionParamNameList) != len(actionParamValueList)):
            logger.info("number of parameters for action and correspoding values are not matching in count")
        else:
            for i in range(0, len(actionParamNameList)):
                te.action[actionParamNameList[i]] = str(actionParamValueList[i])
        te.insert()

    def executeCommand(self, commandString):
        # logger.info("This function assumes that we have simple_switch_CLI in our path. Otherwise it can not connect to the desired switch through thriftport")
        self.cliLock.acquire(blocking=True)
        p = subprocess.Popen(['simple_switch_CLI', '--thrift-port', str(self.basic.thirftPort)], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, encoding='utf8')

        try:
            outs, errs = p.communicate(input=commandString, timeout=20)
            # logger.info("Output of command is "+outs)
            # logger.info("error is of command is "+errs)
        except:
            p.kill()
            logger.info("Error in executing cli command to switch ", self.devName, ". Error is :", sys.exc_info()[0])
        p.kill()
        self.cliLock.release()
        return outs, errs

    # def executeCommand(self, commandString):
    #     logger.info("This function assumes that we have simple_switch_CLI in our path. Otherwise it can not connect to the desired switch through thriftport")
    #     self.cliLock.acquire(blocking=True)
    #     p = subprocess.run(['simple_switch_CLI', '--thrift-port', str(self.basic.thirftPort)], capture_output=True,timeout=20)
    #     try:
    #         outs, errs = p.communicate(input=commandString, timeout=20)
    #         logger.info("Output of command is "+outs)
    #     except :
    #         p.kill()
    #         logger.info("Error in executing cli command to switch ",self.devName, ". Error is :", sys.exc_info()[0])
    #     p.c
    #     self.cliLock.release()
    #     return  outs,errs


class MetricsLevel:

    def __init__(self, low, hi, level, weight=0):
        '''

        :param low: lowest value of the range
        :param hi: highest value of the range
        :param level: if a metrics falls within range low-high then what should be the corresponding level
        :param weight: if we want to assign some special weight , then we can use this field. by default this field is 0
        '''
        self.low = low
        self.hi = hi
        self.level = level
        self.weight = weight

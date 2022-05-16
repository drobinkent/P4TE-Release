# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = ControllerStatistics_from_dict(json.loads(json_string))
import json
import sys
import threading
from enum import Enum
from typing import Any, Optional, Dict, List, TypeVar, Callable, Type, cast
from dataclasses import dataclass
from typing import Dict, Any, TypeVar, Callable, Type, cast

import numpy as np

import ConfigConst as CC
import logging
logger = logging.getLogger('ResultParser')
hdlr = logging.FileHandler(CC.RESULT_PROCESSOR_LOG_FILE_PATH)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)

T = TypeVar("T")


def from_float(x: Any) -> float:
    #print('Inside from float. data is '+str(x)+" type is "+str(type(x)))
    try:
        assert isinstance(x, (float, int)) and not isinstance(x, bool)
    except AssertionError as a:
        #print("Assertion error occured",a)
        error =a
    return float(x)


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def to_float(x: Any) -> float:
    assert isinstance(x, float)
    return x


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def from_bool(x: Any) -> bool:
    assert isinstance(x, bool)
    return x


def from_dict(f: Callable[[Any], T], x: Any) -> Dict[str, T]:
    assert isinstance(x, dict)
    return { k: f(v) for (k, v) in x.items() }


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


@dataclass
class CPUUtilizationPercent:
    host_total: float
    host_user: float
    host_system: float
    remote_total: float
    remote_user: float
    remote_system: int

    @staticmethod
    def from_dict(obj: Any) -> 'CPUUtilizationPercent':
        assert isinstance(obj, dict)
        host_total = from_float(obj.get("host_total"))
        host_user = from_float(obj.get("host_user"))
        host_system = from_float(obj.get("host_system"))
        remote_total = from_float(obj.get("remote_total"))
        remote_user = from_float(obj.get("remote_user"))
        remote_system = from_float(obj.get("remote_system"))
        return CPUUtilizationPercent(host_total, host_user, host_system, remote_total, remote_user, remote_system)

    def to_dict(self) -> dict:
        result: dict = {}
        result["host_total"] = to_float(self.host_total)
        result["host_user"] = to_float(self.host_user)
        result["host_system"] = to_float(self.host_system)
        result["remote_total"] = to_float(self.remote_total)
        result["remote_user"] = to_float(self.remote_user)
        result["remote_system"] = from_int(self.remote_system)
        return result


@dataclass
class SumReceived:
    start: float
    end: float
    seconds: float
    bytes: int
    bits_per_second: float
    socket: Optional[int] = None
    retransmits: Optional[int] = None
    omitted: Optional[bool] = None

    @staticmethod
    def from_dict(obj: Any) -> 'SumReceived':
        assert isinstance(obj, dict)
        start = from_float(obj.get("start"))
        end = from_float(obj.get("end"))
        seconds = from_float(obj.get("seconds"))
        bytes = from_int(obj.get("bytes"))
        bits_per_second = from_float(obj.get("bits_per_second"))
        socket = from_union([from_int, from_none], obj.get("socket"))
        retransmits = from_union([from_int, from_none], obj.get("retransmits"))
        omitted = from_union([from_bool, from_none], obj.get("omitted"))
        return SumReceived(start, end, seconds, bytes, bits_per_second, socket, retransmits, omitted)

    def to_dict(self) -> dict:
        result: dict = {}
        result["start"] = to_float(self.start)
        result["end"] = to_float(self.end)
        result["seconds"] = to_float(self.seconds)
        result["bytes"] = from_int(self.bytes)
        result["bits_per_second"] = to_float(self.bits_per_second)
        result["socket"] = from_union([from_int, from_none], self.socket)
        result["retransmits"] = from_union([from_int, from_none], self.retransmits)
        result["omitted"] = from_union([from_bool, from_none], self.omitted)
        return result


@dataclass
class EndStream:
    sender: Dict[str, float]
    receiver: SumReceived

    @staticmethod
    def from_dict(obj: Any) -> 'EndStream':
        assert isinstance(obj, dict)
        sender = from_dict(from_float, obj.get("sender"))
        receiver = SumReceived.from_dict(obj.get("receiver"))
        return EndStream(sender, receiver)

    def to_dict(self) -> dict:
        result: dict = {}
        result["sender"] = from_dict(to_float, self.sender)
        result["receiver"] = to_class(SumReceived, self.receiver)
        return result


@dataclass
class End:
    streams: List[EndStream]
    sum_sent: SumReceived
    sum_received: SumReceived
    cpu_utilization_percent: CPUUtilizationPercent
    sender_tcp_congestion: str
    receiver_tcp_congestion: str

    @staticmethod
    def from_dict(obj: Any) -> 'End':
        assert isinstance(obj, dict)
        streams = from_list(EndStream.from_dict, obj.get("streams"))
        sum_sent = SumReceived.from_dict(obj.get("sum_sent"))
        sum_received = SumReceived.from_dict(obj.get("sum_received"))
        cpu_utilization_percent = CPUUtilizationPercent.from_dict(obj.get("cpu_utilization_percent"))
        sender_tcp_congestion = from_str(obj.get("sender_tcp_congestion"))
        receiver_tcp_congestion = from_str(obj.get("receiver_tcp_congestion"))
        return End(streams, sum_sent, sum_received, cpu_utilization_percent, sender_tcp_congestion, receiver_tcp_congestion)

    def to_dict(self) -> dict:
        result: dict = {}
        result["streams"] = from_list(lambda x: to_class(EndStream, x), self.streams)
        result["sum_sent"] = to_class(SumReceived, self.sum_sent)
        result["sum_received"] = to_class(SumReceived, self.sum_received)
        result["cpu_utilization_percent"] = to_class(CPUUtilizationPercent, self.cpu_utilization_percent)
        result["sender_tcp_congestion"] = from_str(self.sender_tcp_congestion)
        result["receiver_tcp_congestion"] = from_str(self.receiver_tcp_congestion)
        return result


@dataclass
class IntervalStream:
    socket: int
    start: float
    end: float
    seconds: float
    bytes: int
    bits_per_second: float
    retransmits: int
    snd_cwnd: int
    rtt: int
    rttvar: int
    pmtu: int
    omitted: bool

    @staticmethod
    def from_dict(obj: Any) -> 'IntervalStream':
        assert isinstance(obj, dict)
        socket = from_int(obj.get("socket"))
        start = from_float(obj.get("start"))
        end = from_float(obj.get("end"))
        seconds = from_float(obj.get("seconds"))
        bytes = from_int(obj.get("bytes"))
        bits_per_second = from_float(obj.get("bits_per_second"))
        retransmits = from_int(obj.get("retransmits"))
        snd_cwnd = from_int(obj.get("snd_cwnd"))
        rtt = from_int(obj.get("rtt"))
        rttvar = from_int(obj.get("rttvar"))
        pmtu = from_int(obj.get("pmtu"))
        omitted = from_bool(obj.get("omitted"))
        return IntervalStream(socket, start, end, seconds, bytes, bits_per_second, retransmits, snd_cwnd, rtt, rttvar, pmtu, omitted)

    def to_dict(self) -> dict:
        result: dict = {}
        result["socket"] = from_int(self.socket)
        result["start"] = to_float(self.start)
        result["end"] = to_float(self.end)
        result["seconds"] = to_float(self.seconds)
        result["bytes"] = from_int(self.bytes)
        result["bits_per_second"] = to_float(self.bits_per_second)
        result["retransmits"] = from_int(self.retransmits)
        result["snd_cwnd"] = from_int(self.snd_cwnd)
        result["rtt"] = from_int(self.rtt)
        result["rttvar"] = from_int(self.rttvar)
        result["pmtu"] = from_int(self.pmtu)
        result["omitted"] = from_bool(self.omitted)
        return result


@dataclass
class Interval:
    streams: List[IntervalStream]
    sum: SumReceived

    @staticmethod
    def from_dict(obj: Any) -> 'Interval':
        assert isinstance(obj, dict)
        streams = from_list(IntervalStream.from_dict, obj.get("streams"))
        sum = SumReceived.from_dict(obj.get("sum"))
        return Interval(streams, sum)

    def to_dict(self) -> dict:
        result: dict = {}
        result["streams"] = from_list(lambda x: to_class(IntervalStream, x), self.streams)
        result["sum"] = to_class(SumReceived, self.sum)
        return result


@dataclass
class Connected:
    socket: int
    local_host: str
    local_port: int
    remote_host: str
    remote_port: int

    @staticmethod
    def from_dict(obj: Any) -> 'Connected':
        assert isinstance(obj, dict)
        socket = from_int(obj.get("socket"))
        local_host = from_str(obj.get("local_host"))
        local_port = from_int(obj.get("local_port"))
        remote_host = from_str(obj.get("remote_host"))
        remote_port = from_int(obj.get("remote_port"))
        return Connected(socket, local_host, local_port, remote_host, remote_port)

    def to_dict(self) -> dict:
        result: dict = {}
        result["socket"] = from_int(self.socket)
        result["local_host"] = from_str(self.local_host)
        result["local_port"] = from_int(self.local_port)
        result["remote_host"] = from_str(self.remote_host)
        result["remote_port"] = from_int(self.remote_port)
        return result


@dataclass
class ConnectingTo:
    host: str
    port: int

    @staticmethod
    def from_dict(obj: Any) -> 'ConnectingTo':
        assert isinstance(obj, dict)
        host = from_str(obj.get("host"))
        port = from_int(obj.get("port"))
        return ConnectingTo(host, port)

    def to_dict(self) -> dict:
        result: dict = {}
        result["host"] = from_str(self.host)
        result["port"] = from_int(self.port)
        return result


@dataclass
class TestStart:
    protocol: str
    num_streams: int
    blksize: int
    omit: int
    duration: int
    bytes: int
    blocks: int
    reverse: int
    tos: int

    @staticmethod
    def from_dict(obj: Any) -> 'TestStart':
        assert isinstance(obj, dict)
        protocol = from_str(obj.get("protocol"))
        num_streams = from_int(obj.get("num_streams"))
        blksize = from_int(obj.get("blksize"))
        omit = from_int(obj.get("omit"))
        duration = from_int(obj.get("duration"))
        bytes = from_int(obj.get("bytes"))
        blocks = from_int(obj.get("blocks"))
        reverse = from_int(obj.get("reverse"))
        tos = from_int(obj.get("tos"))
        return TestStart(protocol, num_streams, blksize, omit, duration, bytes, blocks, reverse, tos)

    def to_dict(self) -> dict:
        result: dict = {}
        result["protocol"] = from_str(self.protocol)
        result["num_streams"] = from_int(self.num_streams)
        result["blksize"] = from_int(self.blksize)
        result["omit"] = from_int(self.omit)
        result["duration"] = from_int(self.duration)
        result["bytes"] = from_int(self.bytes)
        result["blocks"] = from_int(self.blocks)
        result["reverse"] = from_int(self.reverse)
        result["tos"] = from_int(self.tos)
        return result


@dataclass
class Timestamp:
    time: str
    timesecs: int

    @staticmethod
    def from_dict(obj: Any) -> 'Timestamp':
        assert isinstance(obj, dict)
        time = from_str(obj.get("time"))
        timesecs = from_int(obj.get("timesecs"))
        return Timestamp(time, timesecs)

    def to_dict(self) -> dict:
        result: dict = {}
        result["time"] = from_str(self.time)
        result["timesecs"] = from_int(self.timesecs)
        return result


@dataclass
class Start:
    connected: List[Connected]
    version: str
    system_info: str
    timestamp: Timestamp
    connecting_to: ConnectingTo
    cookie: str
    tcp_mss: int
    sock_bufsize: int
    sndbuf_actual: int
    rcvbuf_actual: int
    test_start: TestStart

    @staticmethod
    def from_dict(obj: Any) -> 'Start':
        assert isinstance(obj, dict)
        connected = from_list(Connected.from_dict, obj.get("connected"))
        version = from_str(obj.get("version"))
        system_info = from_str(obj.get("system_info"))
        timestamp = Timestamp.from_dict(obj.get("timestamp"))
        connecting_to = ConnectingTo.from_dict(obj.get("connecting_to"))
        cookie = from_str(obj.get("cookie"))
        tcp_mss = from_int(obj.get("tcp_mss"))
        sock_bufsize = from_int(obj.get("sock_bufsize"))
        sndbuf_actual = from_int(obj.get("sndbuf_actual"))
        rcvbuf_actual = from_int(obj.get("rcvbuf_actual"))
        test_start = TestStart.from_dict(obj.get("test_start"))
        return Start(connected, version, system_info, timestamp, connecting_to, cookie, tcp_mss, sock_bufsize, sndbuf_actual, rcvbuf_actual, test_start)

    def to_dict(self) -> dict:
        result: dict = {}
        result["connected"] = from_list(lambda x: to_class(Connected, x), self.connected)
        result["version"] = from_str(self.version)
        result["system_info"] = from_str(self.system_info)
        result["timestamp"] = to_class(Timestamp, self.timestamp)
        result["connecting_to"] = to_class(ConnectingTo, self.connecting_to)
        result["cookie"] = from_str(self.cookie)
        result["tcp_mss"] = from_int(self.tcp_mss)
        result["sock_bufsize"] = from_int(self.sock_bufsize)
        result["sndbuf_actual"] = from_int(self.sndbuf_actual)
        result["rcvbuf_actual"] = from_int(self.rcvbuf_actual)
        result["test_start"] = to_class(TestStart, self.test_start)
        return result


@dataclass
class IPerfResult:
    start: Start
    intervals: List[Interval]
    end: End
    srcName :str
    dstName:str

    @staticmethod
    def from_dict(obj: Any) -> 'ControllerStatistics':
        assert isinstance(obj, dict)
        start = Start.from_dict(obj.get("start"))
        intervals = from_list(Interval.from_dict, obj.get("intervals"))
        end = End.from_dict(obj.get("end"))
        return IPerfResult(start, intervals, end, srcName = None, dstName = None)

    def to_dict(self) -> dict:
        result: dict = {}
        result["start"] = to_class(Start, self.start)
        result["intervals"] = from_list(lambda x: to_class(Interval, x), self.intervals)
        result["end"] = to_class(End, self.end)
        return result

    def getResultsummary(self):
        # This function will only sum up total send and rcvd data and also avg bandwidth for sending and reciving. also collect total time
        # all those information are kept in End
        return self.end

    def getEndTimeInSec(self):
        return float(self.start.timestamp.timesecs+float(self.end.sum_received.seconds))
    def getRcvrSideThroughput(self):
        return self.end.streams[0].sender.bits_per_second
    def getSenderSideThroughput(self):
        return self.start.streams[0].sender.bits_per_second
    def getLocalFCT(self):
        '''
        This gives the time required to send the data to server from sender
        :return:
        '''
        return self.end.sum_sent.end

    def getRemoteFCT(self):
        '''
        This gives the time required to send the data to server from sender. the time is from rcver side
        :return:
        '''
        return self.end.sum_received.end
    def getTotalBytesSent(self):
        return self.end.sum_sent.bytes
    def getTotalBytesRcvd(self):
        return self.end.sum_received.bytes
    def getTotalRetransmits(self):
        return self.end.sum_sent.retransmits
    def getMinRTTForEachInterval(self):
        #This function creates a list of time vs min rtt
        pass

    def getMaxRTTForEachInterval(self):
        #This function creates a list of time vs max rtt
        pass

    def getAvgRTTForEachInterval(self):
        #This function creates a list of time vs avg rtt
        pass

    def getTimeVsCumulativeBytes(self):
        #This function creates a list of time vs total data sent in cummulative  fashion
        # for example if at 1 st send m bytes and 2 nd second n bytes are transferrred. This list will contain [(1,m), (2, m+n)]
        pass
    def setSrcDestName(self, src, dst):
        self.srcName = src
        self.dstName = dst

def IPerfResult_from_dict(s: Any) -> IPerfResult:
    return IPerfResult.from_dict(s)


def IPerfResult_to_dict(x: IPerfResult) -> Any:
    return to_class(IPerfResult, x)


class IPerfResultObjectsForOneFolder():
    def __init__(self,folderPath, start_timer, iperfResults):
        self.folderPath = folderPath
        self.start_timer = start_timer
        self.iperfResults  = iperfResults

    def __str__(self):
        print("Total Iperf Result objects in the folder are "+str( len(self.iperfResults)))
        for r in self.iperfResults:
            r= r[0]
            print("sum _sent = ", r.end.sum_sent.bytes, " sum_recevied = ", r.end.sum_received.bytes, " loss = ", (r.end.sum_sent.bytes-r.end.sum_received.bytes) )




#--------------classes for parsing controller stats

# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = ControllerStatistics_from_dict(json.loads(json_string))



@dataclass
class PortStats:
    upward_port_egress_packet_counter: Dict[str, int]
    downward_port_egress_packet_counter: Dict[str, int]
    upward_port_ingress_packet_counter: Dict[str, int]
    downward_port_inress_packet_counter: Dict[str, int]
    cpu_port_ingress_packet_counter: int
    cpu_port_egress_packet_counter: int
    queue_rates: Dict[str, int]
    queue_depths: Dict[str, int]

    @staticmethod
    def from_dict(obj: Any) -> 'PortStats':
        assert isinstance(obj, dict)
        upward_port_egress_packet_counter = from_dict(from_int, obj.get("_upwardPortEgressPacketCounter"))
        # downward_port_egress_packet_counter = from_dict(from_int, obj.get("_downwardPortEgressPacketCounter"))
        # upward_port_ingress_packet_counter = from_dict(from_int, obj.get("_upwardPortIngressPacketCounter"))
        # downward_port_inress_packet_counter = from_dict(from_int, obj.get("_downwardPortInressPacketCounter"))
        # cpu_port_ingress_packet_counter = from_int(obj.get("_CPUPortIngressPacketCounter"))
        # cpu_port_egress_packet_counter = from_int(obj.get("_CPUPortEgressPacketCounter"))
        # queue_rates = from_dict(from_int, obj.get("queueRates"))
        # queue_depths = from_dict(from_int, obj.get("queueDepths"))
        return PortStats(upward_port_egress_packet_counter, None, None, None, None, None, None, None)

    def to_dict(self) -> dict:
        result: dict = {}
        result["_upwardPortEgressPacketCounter"] = from_dict(from_int, self.upward_port_egress_packet_counter)
        result["_downwardPortEgressPacketCounter"] = from_dict(from_int, self.downward_port_egress_packet_counter)
        result["_upwardPortIngressPacketCounter"] = from_dict(from_int, self.upward_port_ingress_packet_counter)
        result["_downwardPortInressPacketCounter"] = from_dict(from_int, self.downward_port_inress_packet_counter)
        result["_CPUPortIngressPacketCounter"] = from_int(self.cpu_port_ingress_packet_counter)
        result["_CPUPortEgressPacketCounter"] = from_int(self.cpu_port_egress_packet_counter)
        result["queueRates"] = from_dict(from_int, self.queue_rates)
        result["queueDepths"] = from_dict(from_int, self.queue_depths)
        return result


@dataclass
class SwitchPortStatistics:
    keys: bool
    ensure_ascii: bool
    check_circular: bool
    allow_nan: bool
    sort_keys: bool
    indent: None
    port_stats: PortStats
    time: float
    dev_name: str

    @staticmethod
    def from_dict(obj: Any) -> 'SwitchPortStatistics':
        assert isinstance(obj, dict)
        keys = from_bool(obj.get("skipkeys"))
        ensure_ascii = from_bool(obj.get("ensure_ascii"))
        check_circular = from_bool(obj.get("check_circular"))
        allow_nan = from_bool(obj.get("allow_nan"))
        sort_keys = from_bool(obj.get("sort_keys"))
        indent = from_none(obj.get("indent"))
        port_stats = PortStats.from_dict(obj.get("portStats"))
        time = from_float(obj.get("time"))
        dev_name = from_str(obj.get("devName"))
        return SwitchPortStatistics(keys, ensure_ascii, check_circular, allow_nan, sort_keys, indent, port_stats, time, dev_name)

    def to_dict(self) -> dict:
        result: dict = {}
        result["skipkeys"] = from_bool(self.keys)
        result["ensure_ascii"] = from_bool(self.ensure_ascii)
        result["check_circular"] = from_bool(self.check_circular)
        result["allow_nan"] = from_bool(self.allow_nan)
        result["sort_keys"] = from_bool(self.sort_keys)
        result["indent"] = from_none(self.indent)
        result["portStats"] = to_class(PortStats, self.port_stats)
        result["time"] = to_float(self.time)
        result["devName"] = from_str(self.dev_name)
        return result


def SwitchPortStatistics_from_dict(s: Any) -> SwitchPortStatistics:
    return SwitchPortStatistics.from_dict(s)


def SwitchPortStatistics_to_dict(x: SwitchPortStatistics) -> Any:
    return to_class(SwitchPortStatistics, x)



#==============config parser


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
        return Link(node1, node2,  port2,bw, port1)

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
    INVALID=-1
    HOST = 0
    LEAF_SWITCH=1
    SPINE_SWITCH=2
    SUPER_SPINE_SWITCH=3

    def __str__(self):
        val=self
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
        return DeviceBasic(management_address, driver, pipeconf,thirftPort)

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



@dataclass
class Device:
    devName: str
    basic: DeviceBasic
    fabric_device_config: FabricDeviceConfig

    def __init__(self,devName, basic, fabric_device_config):
        self.devName = devName
        self.basic = basic
        self.fabric_device_config = fabric_device_config
        self.portToHostMap = {}
        self.portToSpineSwitchMap = {}
        self.portToLeafSwitchMap = {}
        self.portToSuperSpineSwitchMap = {}
        self.packetOutLock = threading.Lock()
        self.cliLock = threading.Lock()
        self.portToQueueRateMap={}
        self.portToQueueDepthMap={}
        self.maxPort = CC.MAX_PORT_NUMBER

        s = self.basic.management_address.index("device_id=")+len("device_id=")
        tempString = self.basic.management_address[s:len(self.basic.management_address)]
        self.device_id = int(tempString)
        s = self.basic.management_address.index("grpc://") + len("grpc://")
        e = self.basic.management_address.index("?device_id=")
        self.grpcAddress = self.basic.management_address[s:e]
        self.election_id = (1,0)

    @staticmethod
    def from_dict(devName, obj: Any) -> 'Device':
        assert isinstance(obj, dict)
        basic = DeviceBasic.from_dict(obj.get("basic"))
        fabric_device_config = FabricDeviceConfig.from_dict(obj.get("fabricDeviceConfig"))
        return Device(devName, basic, fabric_device_config)

    def to_dict(self) -> dict:
        result: dict = {}
        result["basic"] = to_class(DeviceBasic, self.basic)
        result["fabricDeviceConfig"] = to_class(FabricDeviceConfig, self.fabric_device_config)
        return result




class ConfigLoader():
    def __init__(self, cfgFileName):
        self.nameToSwitchMap = {}
        self.nameToHostMap = {}
        self.cfgFileName = cfgFileName
        print("Starting Result Processor with config file ",cfgFileName)
        self.loadCFG(cfgFileName)

    def loadCFG(self,cfgfileName):
        cfgFile = open(cfgfileName)
        obj = json.load(fp=cfgFile)
        for devName in obj["devices"]:
            try:
                dev = Device.from_dict(devName, obj["devices"][devName])
                s = devName.index("device:") + len("device:")  #Strp from "device:" prefix from device name. this was created for onos.
                devName = devName[s:len(devName)]
                self.nameToSwitchMap[devName] = dev
                logger.info("New dev is "+str(dev))
                #dev.initialSetup()
            except:
                e = sys.exc_info()
                logger.error("Error in initializing ", devName)
                logger.error("Error is "+str( e))
        for portLoc in obj["ports"]:
            p = Port.from_dict(obj["ports"][portLoc])
            logger.info("New port is "+ str(p))
            pass
        for hostMac in obj["hosts"]:
            h = Host.from_dict( obj["hosts"][hostMac])
            self.nameToHostMap[h.basic.name] = h
            logger.info("New host is "+str(h))
        for i in range (0, len(obj["alllinks"]["links"])):
            logger.info("Link processing is not required for result processing.  So skipping... ")
            pass
        cfgFile.close()
        logger.info("Finished reading and loading cfg")
        # print(self.nameToSwitchMap)
        # print(self.nameToHostMap)


class PerTrafficClassSummaryResults:

    def __init__(self, traficClassIdentifierFlowVolume):
        '''

        :param traficClassIdentifierFlowVolume:  This filed is just to mention, what is the flow volume based on which we have decided that any flow will belong to this type
        As example, if traficClassIdentifierFlowVolume = 50 KB then all results in this class will have flow volume near to 50 KB
        '''
        self.traficClassIdentifierFlowVolume = traficClassIdentifierFlowVolume
        self.iperfResults = []  # in this filed we will keep all the iperfresults that belongs to this category
        pass

    def getTraficClassIdentifierFlowVolume(self):
        return self.traficClassIdentifierFlowVolume

    def addIperfResult(self, iperfResult):
        self.iperfResults.append(iperfResult)
    def getNthPercentilieTCPThroughputInBPS(self, n):
        throughputAsArray = []
        for r in self.iperfResults:
            throughputAsArray.append(r.end.sum_received.bits_per_second) # we are taking the recivier side time for flow completion
        return np.percentile(throughputAsArray, n)

    def getSTDOfTCPThroughputInBPS(self):
        throughputAsArray = []
        for r in self.iperfResults:
            throughputAsArray.append(r.end.sum_received.bits_per_second) # we are taking the recivier side time for flow completion
        return np.std(throughputAsArray)
    def getAVGOfTCPThroughputInBPS(self):
        throughputAsArray = []
        for r in self.iperfResults:
            throughputAsArray.append(r.end.sum_received.bits_per_second) # we are taking the recivier side time for flow completion
        return np.average(throughputAsArray)

    def getNthPercentilieFCT(self, n):
        '''

        :param n: what percentile of FCT you want . If we want 90th percentile then pass n=90
        :return:
        '''
        fctAsArray = []
        for r in self.iperfResults:
            fctAsArray.append(r.end.sum_received.seconds) # we are taking the recivier side time for flow completion
        return np.percentile(fctAsArray, n)

    def getAvgFCT(self):
        '''

        :param n: what percentile of FCT you want . If we want 90th percentile then pass n=90
        :return:
        '''
        fctAsArray = []
        for r in self.iperfResults:
            fctAsArray.append(r.end.sum_received.seconds) # we are taking the recivier side time for flow completion
        return np.average(fctAsArray)
    def getSTDOfFCT(self):
        '''

        :param n: what percentile of FCT you want . If we want 90th percentile then pass n=90
        :return:
        '''
        fctAsArray = []
        for r in self.iperfResults:
            fctAsArray.append(r.end.sum_received.seconds) # we are taking the recivier side time for flow completion
        return np.std(fctAsArray)

    def getNthPercentilieRetransmit(self, n):
        '''

        :param n: what percentile of retransmit you want . If we want 90th percentile then pass n=90
        :return:
        '''
        retrisnmitNumAsArray = []
        for r in self.iperfResults:
            # r = IPerfResult()
            retrisnmitNumAsArray.append(r.end.sum_sent.retransmits)
        return np.percentile(retrisnmitNumAsArray, n)

    def getSTDOfRetransmit(self):
        retrisnmitNumAsArray = []
        for r in self.iperfResults:
            # r = IPerfResult()
            retrisnmitNumAsArray.append(r.end.sum_sent.retransmits)
        return np.std(retrisnmitNumAsArray)
    def getAVGOfRetransmit(self):
        retrisnmitNumAsArray = []
        for r in self.iperfResults:
            # r = IPerfResult()
            retrisnmitNumAsArray.append(r.end.sum_sent.retransmits)
        return np.average(retrisnmitNumAsArray)

    def getNthPercentilieSuccessfulData(self, n):
        '''

        :param n: what percentile of data loss you want . If we want 90th percentile then pass n=90
        :return:
        '''
        succesfulDataSentAsArray = []
        for r in self.iperfResults:
            #r = IPerfResult()
            # if(r.end.sum_sent.bytes < r.end.sum_received.bytes):
            #     succesfulDataSentAsArray.append(0)
            # else:
            succesfulDataSentAsArray.append(r.end.sum_received.bytes)
        return np.percentile(succesfulDataSentAsArray, n)/1024

    def getSTDOfSuccessfulData(self):
        '''

        :param n: what percentile of data loss you want . If we want 90th percentile then pass n=90
        :return:
        '''
        succesfulDataSentAsArray = []
        for r in self.iperfResults:
            #r = IPerfResult()
            # if(r.end.sum_sent.bytes < r.end.sum_received.bytes):
            #     succesfulDataSentAsArray.append(0)
            # else:
            succesfulDataSentAsArray.append(r.end.sum_received.bytes)
        return np.std(succesfulDataSentAsArray)

    def getAVGOfSuccessfulData(self):
        '''

        :param n: what percentile of data loss you want . If we want 90th percentile then pass n=90
        :return:
        '''
        succesfulDataSentAsArray = []
        for r in self.iperfResults:
            #r = IPerfResult()
            # if(r.end.sum_sent.bytes < r.end.sum_received.bytes):
            #     succesfulDataSentAsArray.append(0)
            # else:
            succesfulDataSentAsArray.append(r.end.sum_received.bytes)
        return np.average(succesfulDataSentAsArray)

    def getNthPercentilieDataLoss(self, n):
        '''

        :param n: what percentile of data loss you want . If we want 90th percentile then pass n=90
        :return:
        '''
        dataLossAsArray = []
        for r in self.iperfResults:
            #r = IPerfResult()
            if(r.end.sum_sent.bytes < r.end.sum_received.bytes):
                dataLossAsArray.append(0)
            else:
                dataLossAsArray.append(r.end.sum_sent.bytes - r.end.sum_received.bytes)
        return np.percentile(dataLossAsArray, n)/1024

    def getSTDOfDataLoss(self):
        '''

        :param n: what percentile of data loss you want . If we want 90th percentile then pass n=90
        :return:
        '''
        dataLossAsArray = []
        for r in self.iperfResults:
            #r = IPerfResult()
            if(r.end.sum_sent.bytes < r.end.sum_received.bytes):
                dataLossAsArray.append(0)
            else:
                dataLossAsArray.append(r.end.sum_sent.bytes - r.end.sum_received.bytes)
        return np.std(dataLossAsArray)

    def getAvgDataLoss(self):
        '''

        :param n: what percentile of data loss you want . If we want 90th percentile then pass n=90
        :return:
        '''
        dataLossAsArray = []
        for r in self.iperfResults:
            #r = IPerfResult()
            if(r.end.sum_sent.bytes < r.end.sum_received.bytes):
                dataLossAsArray.append(0)
            else:
                dataLossAsArray.append(r.end.sum_sent.bytes - r.end.sum_received.bytes)
        return np.average(dataLossAsArray)
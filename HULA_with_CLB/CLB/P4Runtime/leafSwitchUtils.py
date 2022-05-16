import math

import InternalConfig
import P4Runtime.shell as sh
import logging
import logging.handlers

from P4Runtime.context import P4Type

import  ConfigConst as ConfConst
logger = logging.getLogger('LeafSwitchUtils')
logger.handlers = []
hdlr = logging.handlers.RotatingFileHandler(ConfConst.CONTROLLER_LOG_FILE_PATH, maxBytes = ConfConst.MAX_LOG_FILE_SIZE , backupCount= ConfConst.MAX_LOG_FILE_BACKUP_COUNT)
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)

def addL2TernaryEntryForMulticast(dev):
    dev.addTernaryMatchEntry(tableName="IngressPipeImpl.l2_ternary_processing_control_block.l2_ternary_table", fieldName="hdr.ethernet.dst_addr",
                             fieldValue="FF:FF:FF:FF:FF:FF", mask="FF:00:00:00:00:00",
                             actionName="IngressPipeImpl.l2_ternary_processing_control_block.set_multicast_group",
                             actionParamName="gid",
                             actionParamValue=str(InternalConfig.LEAF_SWITCH_HOST_MULTICAST_GROUP))
    dev.addTernaryMatchEntry(tableName="IngressPipeImpl.l2_ternary_processing_control_block.l2_ternary_table", fieldName="hdr.ethernet.dst_addr",
                             fieldValue="33:33:00:00:00:00", mask="FF:FF:00:00:00:00",
                             actionName="IngressPipeImpl.l2_ternary_processing_control_block.set_multicast_group",
                             actionParamName="gid",
                             actionParamValue=str(InternalConfig.LEAF_SWITCH_HOST_MULTICAST_GROUP))


def addNDPentries(dev):
    for hPort in dev.portToHostMap.keys():
        host = (dev.portToHostMap.get(hPort))
        dev.addExactMatchEntry(tableName="IngressPipeImpl.ndp_processing_control_block.ndp_reply_table", fieldName="hdr.ipv6.src_addr",
                               fieldValue=host.basic.ips[0],
                               actionName="IngressPipeImpl.ndp_processing_control_block.ndp_ns_to_na", actionParamName="target_mac",
                               actionParamValue=dev.fabric_device_config.my_station_mac)








def addDownstreamRoutingRuleForLeafSwitch(dev):
    for hPort in dev.portToHostMap.keys():
        host = (dev.portToHostMap.get(hPort))
        actionParamNameList = ["port_num", "dmac"]
        actionParamValueList = [hPort, host.fabric_host_config.mac]
        dev.addExactMatchEntryWithMultipleActionParameter(tableName="IngressPipeImpl.downstream_routing_control_clock.downstream_routing_table",
                                                          fieldName="hdr.ipv6.dst_addr", fieldValue=host.basic.ips[0],
                                                          actionName="IngressPipeImpl.downstream_routing_control_clock.set_downstream_egress_port",
                                                          actionParamNameList=actionParamNameList,
                                                          actionParamValueList=actionParamValueList)



def addUpStreamRoutingGroupForLeafSwitch(dev, upstreamPortsList):
    group = sh.ActionProfileGroup(dev, "upstream_path_selector")(
        group_id=InternalConfig.LEAF_SWITCH_UPSTREAM_PORTS_GROUP)
    group.insert()
    for i in range(0, len(upstreamPortsList)):
        member = sh.ActionProfileMember(dev, "upstream_path_selector")(member_id=i, action="set_upstream_egress_port")
        member.action["port_num"] = str(upstreamPortsList[i])
        member.insert()
        group.add(member.member_id)
    group.modify()
    #delFrmGrp(dev, 1)





def delFrmGrp(dev, port):
    group = sh.ActionProfileGroup(dev, "upstream_path_selector")(
        group_id=InternalConfig.LEAF_SWITCH_UPSTREAM_PORTS_GROUP)
    #group = dev.grp
    #print("Group is "+group)
    member = sh.ActionProfileMember(dev, "upstream_path_selector")(member_id=port, action="set_upstream_egress_port")
    member.action["port_num"] = str(port)
    group.del_member_from_group(member)
    group.modify()


class LeafConfig:

    def __init__(self):
        pass

# def setPortQueueRatesAndDepth(dev, queueRateForHostFacingPortsOfLeafSwitch, queueRateForSpineFacingPortsOfLeafSwitch, queueRateToDepthFactor):
#     cmdString = ""
#     #Setting up ratre and depth for host facing ports
#     for hPort in dev.portToHostMap.keys():
#         cmdString = cmdString+  "set_queue_rate "+str(queueRateForHostFacingPortsOfLeafSwitch)+ " "+str(hPort)+"\n"
#         dev.executeCommand(cmdString)
#         cmdString = cmdString+  "set_queue_depth "+str(int(queueRateToDepthFactor) * int(queueRateForHostFacingPortsOfLeafSwitch))+ " "+str(hPort)+"\n"
#         dev.executeCommand(cmdString)
#         dev.setPortQueueRate(hPort,queueRateForHostFacingPortsOfLeafSwitch )
#         dev.setPortQueueDepth(hPort,int(queueRateToDepthFactor) * int(queueRateForHostFacingPortsOfLeafSwitch))
#     for spineFacingPort in list(dev.portToSpineSwitchMap.keys()):
#         cmdString = cmdString+  "set_queue_rate "+str(queueRateForSpineFacingPortsOfLeafSwitch)+ " "+str(spineFacingPort)+"\n"
#         dev.executeCommand(cmdString)
#         cmdString = cmdString+  "set_queue_depth "+str(int(queueRateToDepthFactor) * int( queueRateForSpineFacingPortsOfLeafSwitch))+ " "+str(spineFacingPort)+"\n"
#         dev.executeCommand(cmdString)
#         dev.setPortQueueRate(spineFacingPort,queueRateForSpineFacingPortsOfLeafSwitch )
#         dev.setPortQueueDepth(spineFacingPort,int(queueRateToDepthFactor) * int( queueRateForSpineFacingPortsOfLeafSwitch))
#     logger.info("Executing queuerate and depth setup commmand for device "+ str(dev))
#     logger.info("command is: "+cmdString)
#     #dev.executeCommand(cmdString)

def setPortQueueRatesAndDepth(dev, queueRateForHostFacingPortsOfLeafSwitch, queueRateForSpineFacingPortsOfLeafSwitch, queueRateToDepthFactor):
    cmdString = ""
    #Setting up ratre and depth for host facing ports
    for hPort in dev.portToHostMap.keys():
        cmdString = cmdString+  "set_queue_rate "+str(queueRateForHostFacingPortsOfLeafSwitch)+ " "+str(hPort)+"\n"
        dev.executeCommand(cmdString)
        cmdString = ""
        cmdString = cmdString+  "set_queue_depth "+str(math.floor(queueRateToDepthFactor* queueRateForHostFacingPortsOfLeafSwitch))+ " "+str(hPort)+"\n"
        dev.executeCommand(cmdString)
        dev.setPortQueueRate(hPort,queueRateForHostFacingPortsOfLeafSwitch )
        dev.setPortQueueDepth(hPort,math.floor((queueRateToDepthFactor *queueRateForHostFacingPortsOfLeafSwitch)))
    for spineFacingPort in list(dev.portToSpineSwitchMap.keys()):
        cmdString = ""
        cmdString = cmdString+  "set_queue_rate "+str(queueRateForSpineFacingPortsOfLeafSwitch)+ " "+str(spineFacingPort)+"\n"
        dev.executeCommand(cmdString)
        cmdString = ""
        cmdString = cmdString+  "set_queue_depth "+str(math.floor(queueRateToDepthFactor * queueRateForSpineFacingPortsOfLeafSwitch))+ " "+str(spineFacingPort)+"\n"
        dev.executeCommand(cmdString)
        dev.setPortQueueRate(spineFacingPort,queueRateForSpineFacingPortsOfLeafSwitch )
        dev.setPortQueueDepth(spineFacingPort,math.floor(queueRateToDepthFactor *queueRateForSpineFacingPortsOfLeafSwitch))
    logger.info("Executing queuerate and depth setup commmand for device "+ str(dev))
    logger.info("command is: "+cmdString)
    #dev.executeCommand(cmdString)
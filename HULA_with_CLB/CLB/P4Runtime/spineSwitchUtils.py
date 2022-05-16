import InternalConfig
import P4Runtime.shell as sh
import P4Runtime.JsonParser as jp
import logging
import logging.handlers
import  ConfigConst as ConfConst
logger = logging.getLogger('SpineSwitchUtils')
logger.handlers = []
hdlr = logging.handlers.RotatingFileHandler(ConfConst.CONTROLLER_LOG_FILE_PATH, maxBytes = ConfConst.MAX_LOG_FILE_SIZE , backupCount= ConfConst.MAX_LOG_FILE_BACKUP_COUNT)
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)


def addDownstreamRoutingRuleForSpineSwitch(dev):
    for leafSwitchPort in dev.portToLeafSwitchMap.keys():
        lswitch = (dev.portToLeafSwitchMap.get(leafSwitchPort))
        e = lswitch.fabric_device_config.switch_host_subnet_prefix.index("/")
        leafSubnetAsIP = lswitch.fabric_device_config.switch_host_subnet_prefix[0:e]
        leafSubnetPrefixLength = lswitch.fabric_device_config.switch_host_subnet_prefix[e+1:len(lswitch.fabric_device_config.switch_host_subnet_prefix)]
        actionParamNameList = ["port_num", "dmac"]
        actionParamValueList = [leafSwitchPort, lswitch.fabric_device_config.my_station_mac]
        dev.addLPMMatchEntryMultipleActionParameter(tableName= "IngressPipeImpl.spine_downstream_routing_control_block.downstream_routing_table", fieldName="hdr.ipv6.dst_addr", fieldValue=leafSubnetAsIP,
                        prefixLength=leafSubnetPrefixLength, actionName = "IngressPipeImpl.spine_downstream_routing_control_block.set_downstream_egress_port", actionParamNameList=actionParamNameList,
                        actionParamValueList=actionParamValueList)



def addUpStreamRoutingGroupForSpineSwitch(dev, upstreamPortsList):
    group = sh.ActionProfileGroup(dev,"upstream_path_selector")(group_id=InternalConfig.SPINE_SWITCH_UPSTREAM_PORTS_GROUP)
    group.insert()
    for i in range (0, len(upstreamPortsList)):
        member = sh.ActionProfileMember(dev,"upstream_path_selector")( member_id=i,action="set_upstream_egress_port")
        member.action["port_num"] = str(upstreamPortsList[i])
        member.insert()
        group.add(member.member_id)
    group.modify()

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
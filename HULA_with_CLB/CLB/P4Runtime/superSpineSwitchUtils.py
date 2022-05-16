import InternalConfig
import P4Runtime.shell as sh
import P4Runtime.JsonParser as jp
import logging
import logging.handlers
import  ConfigConst as ConfConst
logger = logging.getLogger('SuperSpineSwitchUtils')
logger.handlers = []
hdlr = logging.handlers.RotatingFileHandler(ConfConst.CONTROLLER_LOG_FILE_PATH, maxBytes = ConfConst.MAX_LOG_FILE_SIZE , backupCount= ConfConst.MAX_LOG_FILE_BACKUP_COUNT)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setLevel(logging.INFO)
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)

def addDownstreamRoutingRuleForSuperSpineSwitch(dev):
    for spineSwitchPort in dev.portToSpineSwitchMap.keys():
        spineSwitch = (dev.portToSpineSwitchMap.get(spineSwitchPort))
        e = spineSwitch.fabric_device_config.switch_host_subnet_prefix.index("/")
        spineSubnetAsIP = spineSwitch.fabric_device_config.switch_host_subnet_prefix[0:e]
        spineSubnetPrefixLength = spineSwitch.fabric_device_config.switch_host_subnet_prefix[e+1:len(spineSwitch.fabric_device_config.switch_host_subnet_prefix)]
        actionParamNameList = ["port_num", "dmac"]
        actionParamValueList = [spineSwitchPort, spineSwitch.fabric_device_config.my_station_mac]
        dev.addLPMMatchEntryMultipleActionParameter(tableName= "IngressPipeImpl.spine_downstream_routing_control_block.downstream_routing_table", fieldName="hdr.ipv6.dst_addr", fieldValue=spineSubnetAsIP,
                                                    prefixLength=spineSubnetPrefixLength, actionName = "IngressPipeImpl.spine_downstream_routing_control_block.set_downstream_egress_port",
                                                    actionParamNameList=actionParamNameList,
                                                    actionParamValueList=actionParamValueList)




def setPortQueueRatesAndDepth(dev, queueRateForSpineSwitchFacingPortsOfSuperSpineSwitch, queueRateForExternalInternetFacingPortsOfSuperSpineSwitch, queueRateToDepthFactor):
    cmdString = ""
    #Setting up ratre and depth for host facing ports
    for spineSwitchPort in dev.portToSpineSwitchMap.keys():
        cmdString = ""
        cmdString = cmdString+  "set_queue_rate "+str(queueRateForSpineSwitchFacingPortsOfSuperSpineSwitch)+ " "+str(spineSwitchPort)+"\n"
        dev.executeCommand(cmdString)
        cmdString = ""
        cmdString = cmdString+  "set_queue_depth "+str(int(queueRateToDepthFactor) * int( queueRateForSpineSwitchFacingPortsOfSuperSpineSwitch))+ " "+str(spineSwitchPort)+"\n"
        dev.executeCommand(cmdString)
        dev.setPortQueueRate(spineSwitchPort,queueRateForSpineSwitchFacingPortsOfSuperSpineSwitch )
        dev.setPortQueueDepth(spineSwitchPort,(int(queueRateToDepthFactor) * int( queueRateForSpineSwitchFacingPortsOfSuperSpineSwitch)))

    #In future we may use the data rate to external internet
    logger.info("Executing queue rate and depth setup commmand for device "+ str(dev))
    logger.info("command is: "+cmdString)
    #dev.executeCommand(cmdString)
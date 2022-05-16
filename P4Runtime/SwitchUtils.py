
#import CentralizedAlgorithms as centrAlgo
import DistributedAlgorithms.CPAssistedMultiCriteriaPolicyRouting as multiCritPolicyRouting
import DistributedAlgorithms.ECMPRouting as ecmpRouting
import math

import InternalConfig
import P4Runtime.shell as sh
import ConfigConst as ConfConst
import  P4Runtime.JsonParser as jp
import P4Runtime.shell as sh
import logging
# logger = logging.getLogger('DCNTEController')
# hdlr = logging.FileHandler('./log/controller.log')
# formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
# hdlr.setFormatter(formatter)
# logger.addHandler(hdlr) \n  logging.StreamHandler(stream=None)
# logger.setLevel(logging.INFO)

import logging
import logging.handlers
logger = logging.getLogger('SwitchUtils')
logger.handlers = []

hdlr = logging.handlers.RotatingFileHandler(ConfConst.CONTROLLER_LOG_FILE_PATH, maxBytes = ConfConst.MAX_LOG_FILE_SIZE , backupCount= ConfConst.MAX_LOG_FILE_BACKUP_COUNT)
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)

def setupFlowtypeBasedIngressRateMonitoring(dev):
    '''
    We have setup the port queue rates earlier and ther are stored in portToQueueRateMap. But the problem in they are setup for single port.
    In case of if we have multiple queue per port, we may have to setup the rates separately for each of the queue of each of the ports. Same is true for queue depths also.
    Currently bmv2 sets the rate for each queue in same quantity/ but if we do not use the scheduler programmability then it doesn't directly impacts the rate. because
    By default all packets are passed through queue 0. so a specific rate is applied to that queue. and the ultimate rate given by the swithc is that rate. but if our machine supports, and
    we can use the schedulers correctly, we should get 8* rate number pf packets per second. Now the question arrises, about the ingress port rates. Here most probably bmv2 do not applies any rate
    . So we have to use our own meter here and set the rate according to our environment.

    For ingress ports, bmv2 keeps 1K buffer, but there is no specific queue rate mechanism here. so we have to keep the rate record our own self. also same logic applicable for queue depth.
    After completion we have to start a all-to-all test. from that we have to decide about what is the average rate all ports can sustain. That will be the queue rate for all ports.
    :param dev:
    :return:
    '''

    #sum total processing rate of all the host facing ports. among the total rate keep a percent reserve for one kinf of flow. rest for other kind of flow.
    # if switch is leaf type -- find sum of total packet processing rates for host facing ports
    # else if switch is spine type  -- find sum of total packet processing rates for leaf facing ports
    # if switch is super spine type  -- find sum of total packet processing rates for spine facing ports
    # if (dev.dpAlgorithm != ConfConst.DataplnaeAlgorithm.DP_ALGO_BASIC_ECMP) :
    #     return


    downwardPortList = []
    upwardPortList = []
    if (dev.fabric_device_config.switch_type == jp.SwitchType.LEAF ):
        totalRateOfDownWardPorts = getTotalPacketProcessingRatesForPortList(dev, list(dev.portToHostMap.keys()))
        downwardPortList= list(dev.portToHostMap.keys())
        totalRateOfUpwordPorts = getTotalPacketProcessingRatesForPortList(dev, list(dev.portToSpineSwitchMap.keys()))
        upwardPortList = list(dev.portToSpineSwitchMap.keys())
    elif (dev.fabric_device_config.switch_type == jp.SwitchType.SPINE ):
        totalRateOfDownWardPorts = getTotalPacketProcessingRatesForPortList(dev, list(dev.portToLeafSwitchMap.keys()))
        downwardPortList = list(dev.portToLeafSwitchMap.keys())
        upwardPortList =list(dev.portToSuperSpineSwitchMap.keys())
        totalRateOfUpwordPorts = getTotalPacketProcessingRatesForPortList(dev, list(dev.portToSuperSpineSwitchMap.keys()))
    elif (dev.fabric_device_config.switch_type == jp.SwitchType.SUPER_SPINE ):
        totalRateOfDownWardPorts = getTotalPacketProcessingRatesForPortList(dev, list(dev.portToSpineSwitchMap.keys()))
        downwardPortList = list(dev.portToSpineSwitchMap.keys())
        upwardPortList = []   #For super spine we are not working for connectivity toward internet
        totalRateOfUpwordPorts = getTotalPacketProcessingRatesForPortList(dev, list(dev.portToSpineSwitchMap.keys()))

        #port x traffic_class --> action (traffic_class) --> rate of meter[traffic_class] = rate_array[traffic_class_index]
    for p in downwardPortList:
        for i in range (0, len(ConfConst.TRAFFIC_CLASS_AS_LIST)):
            tClass = ConfConst.TRAFFIC_CLASS_AS_LIST[i]
            dev.addExactMatchEntryWithMultipleField( tableName = "IngressPipeImpl.ingress_rate_monitor_control_block.flow_type_based_ingress_stats_table",
                fieldNameList = ["standard_metadata.ingress_port", "hdr.ipv6.traffic_class"], fieldValueList = [p, tClass],
                actionName="IngressPipeImpl.ingress_rate_monitor_control_block.monitor_incoming_flow_based_on_flow_type_for_pkts_rcvd_from_downstream",
                 actionParamName = "flow_type_based_meter_idx", actionParamValue = str(tClass))
            me = sh.MeterEntry(dev,"IngressPipeImpl.ingress_rate_monitor_control_block.flow_type_based_ingress_meter_for_downstream")
            me.index = i
            me.cir = int((totalRateOfDownWardPorts * ConfConst.PERCENTAGE_OF_TOTAL_UPWARD_TRAFFIC_FOR_TRAFFIC_CLASS[i])/100)
            #me.cburst = int(math.ceil((totalRateOfDownWardPorts - int((totalRateOfDownWardPorts * ConfConst.PERCENTAGE_OF_TOTAL_UPWARD_TRAFFIC_FOR_TRAFFIC_CLASS[i]))/100)/5))  # 1/5 th of the rest of the bandwidth
            me.cburst =  math.ceil(int((totalRateOfDownWardPorts * ConfConst.PERCENTAGE_OF_TOTAL_UPWARD_TRAFFIC_FOR_TRAFFIC_CLASS[i])/(100*5)))  # 1/5 th of the rest of the bandwidth
            me.pir = int(totalRateOfDownWardPorts * 0.95)   # 95 %of the total traffic
            me.pburst = int(math.ceil((totalRateOfDownWardPorts * 0.05)))
            me.modify()
            print(dev.devName+"Rate config of meter for port -- "+str(p)+" traffic class "+str(tClass)+" cir "+str(int((totalRateOfDownWardPorts * ConfConst.PERCENTAGE_OF_TOTAL_UPWARD_TRAFFIC_FOR_TRAFFIC_CLASS[i])/100))
                  +" cburst "+str(math.ceil(int((totalRateOfDownWardPorts * ConfConst.PERCENTAGE_OF_TOTAL_UPWARD_TRAFFIC_FOR_TRAFFIC_CLASS[i])/(100*5))))+
                  " pir "+str(int(totalRateOfDownWardPorts * 0.95) )+
                  " pbirst "+str(int(math.ceil((totalRateOfDownWardPorts * 0.05)))))
    for p in upwardPortList:
        for i in range (0, len(ConfConst.TRAFFIC_CLASS_AS_LIST)):


            tClass = ConfConst.TRAFFIC_CLASS_AS_LIST[i]
            dev.addExactMatchEntryWithMultipleField( tableName = "IngressPipeImpl.ingress_rate_monitor_control_block.flow_type_based_ingress_stats_table",
                                                     fieldNameList = ["standard_metadata.ingress_port", "hdr.ipv6.traffic_class"], fieldValueList = [p, tClass],
                                                     actionName="IngressPipeImpl.ingress_rate_monitor_control_block.monitor_incoming_flow_based_on_flow_type_for_pkts_rcvd_from_upstream",
                                                     actionParamName = "flow_type_based_meter_idx", actionParamValue = str(tClass))
            me = sh.MeterEntry(dev,"IngressPipeImpl.ingress_rate_monitor_control_block.flow_type_based_ingress_meter_for_upstream")
            me.index = i
            me.cir = int((totalRateOfDownWardPorts * ConfConst.PERCENTAGE_OF_TOTAL_UPWARD_TRAFFIC_FOR_TRAFFIC_CLASS[i])/100)
            me.cburst = int(math.ceil((totalRateOfDownWardPorts - int((totalRateOfDownWardPorts * ConfConst.PERCENTAGE_OF_TOTAL_UPWARD_TRAFFIC_FOR_TRAFFIC_CLASS[i]))/100)/5))  # 1/5 th of the rest of the bandwidth
            me.pir = int(totalRateOfDownWardPorts * 0.95)   # 95 %of the total traffic
            me.pburst = int(math.ceil((totalRateOfDownWardPorts * 0.05)))
            me.modify()
            print(dev.devName+"Rate config of meter for port -- "+str(p)+" traffic class "+str(tClass)+" cir "+str(int((totalRateOfDownWardPorts * ConfConst.PERCENTAGE_OF_TOTAL_UPWARD_TRAFFIC_FOR_TRAFFIC_CLASS[i])/100))
                  +" cburst "+str(int(math.ceil((totalRateOfDownWardPorts - int((totalRateOfDownWardPorts * ConfConst.PERCENTAGE_OF_TOTAL_UPWARD_TRAFFIC_FOR_TRAFFIC_CLASS[i]))/100)/5)))+
                  " pir "+str(int(totalRateOfDownWardPorts * 0.95) )+
                  " pbirst "+str(int(math.ceil((totalRateOfDownWardPorts * 0.05)))))



def getTotalPacketProcessingRatesForPortList(dev, portList):
    '''This method returns the totoal packet processing rate of the ports for downward ports.
    '''
    totalRate = 0
    for p in portList:
        if dev.portToQueueRateMap[str(p)] != None:
            # totalRate = totalRate + int(dev.portToQueueRateMap[str(p)] )
            totalRate =  int(dev.portToQueueRateMap[str(p)] )
    return totalRate

def portBasedEgressRateMonitoring(dev):
    if (dev.dpAlgorithm == ConfConst.DataplnaeAlgorithm.DP_ALGO_BASIC_ECMP) :
        return
    for portIndex in dev.portToQueueRateMap:
        if (not( (str(portIndex)=="1") or (str(portIndex)=="2") or (str(portIndex)=="3") or (str(portIndex)=="4"))):
            dev.addExactMatchEntryWithoutActionParam(tableName="EgressPipeImpl.egress_rate_monitor_control_block.egress_rate_monitor_table",fieldName="standard_metadata.egress_port", fieldValue=portIndex,
                                                     actionName="EgressPipeImpl.egress_rate_monitor_control_block.monitor_outgoing_flow")
            portQueueRate = dev.portToQueueRateMap.get(portIndex)
            cir = portQueueRate * ConfConst.EGRESS_STATS_METER_CIR_THRESHOLD_FACTOR
            cburst = portQueueRate * ConfConst.EGRESS_STATS_METER_CBURST_FACTOR
            pir = portQueueRate*ConfConst.EGRESS_STATS_METER_PIR_FACTOR
            pburst = portQueueRate * ConfConst.EGRESS_STATS_METER_PBURST_FACTOR
            ce = sh.DirectMeterEntry(dev, "EgressPipeImpl.egress_rate_monitor_control_block.egress_meter")
            ce.table_entry.match["standard_metadata.egress_port"] = portIndex
            ce.cir = int(cir)
            ce.cburst = int(cburst)
            ce.pir = int(pir)
            ce.pburst = int(pburst)
            ce.modify()
            logging.info("Modified meter entry in device: "+str(dev))

def setupEgressQueueDepthMetricsLevelCalculatorTables(dev, egressQueueDepthMetricsLevels):
    for metricsLevel in egressQueueDepthMetricsLevels:
        te = sh.TableEntry(dev,"IngressPipeImpl.egress_queue_depth_metrics_level_calculator_control_block.queue_depth_metrics_level_calculator_table")(action="IngressPipeImpl.egress_queue_depth_metrics_level_calculator_control_block.set_queue_depth_metrics_level")
        te.match["hdr.p2p_feedback.delay_event_data"] = str(metricsLevel.low)+".."+str(metricsLevel.hi)
        #te.match[matachField2] = str(low)+".."+str(high)    # "0..1024"
        te.action["delay_level"] = str(metricsLevel.level)
        te.action["weight"] = str(metricsLevel.weight)
        te.priority = int(InternalConfig.DEFAULT_PRIORITY)
        te.insert()
    return

def setupPortToPortDelayMetricsLevelCalculatorTables(dev, egressQueueDepthMetricsLevels):
    for metricsLevel in egressQueueDepthMetricsLevels:
        te = sh.TableEntry(dev,"IngressPipeImpl.path_delay_metrics_level_calculator_control_block.path_delay_metrics_level_calculator_table")(action="IngressPipeImpl.path_delay_metrics_level_calculator_control_block.set_delay_metrics_level")
        te.match["hdr.p2p_feedback.delay_event_data"] = str(metricsLevel.low)+".."+str(metricsLevel.hi)
        #te.match[matachField2] = str(low)+".."+str(high)    # "0..1024"
        te.action["delay_level"] = str(metricsLevel.level)
        te.action["weight"] = str(metricsLevel.weight)
        te.priority = int(InternalConfig.DEFAULT_PRIORITY)
        te.insert()
    return

def portBasedIngressRateMonitoring(dev):
    #dev = Device()
    '''
    This method was written for port based rate monitoring for ingresws. which we are not using at this momnent
    :param dev:
    :return:
    '''

    for portIndex in dev.portToQueueRateMap:
        portQueueRate = dev.portToQueueRateMap.get(portIndex)
        cir = portQueueRate * ConfConst.INGRESS_STATS_METER_CIR_THRESHOLD_FACTOR
        cburst = portQueueRate * ConfConst.INGRESS_STATS_METER_CBURST_FACTOR
        pir = portQueueRate*ConfConst.INGRESS_STATS_METER_PIR_FACTOR
        pburst = portQueueRate * ConfConst.INGRESS_STATS_METER_PBURST_FACTOR
        dev.addExactMatchEntryWithoutActionParam(tableName="IngressPipeImpl.ingress_rate_monitor_control_block.ingress_stats",fieldName="standard_metadata.ingress_port", fieldValue=portIndex,
                                                 actionName="IngressPipeImpl.ingress_rate_monitor_control_block.monitor_incoming_flow")
        ce = sh.DirectMeterEntry(dev, "IngressPipeImpl.ingress_rate_monitor_control_block.ingress_meter")
        ce.table_entry.match["standard_metadata.ingress_port"] = portIndex
        ce.cir = int(cir)
        ce.cburst = int(cburst)
        ce.pir = int(pir)
        ce.pburst = int(pburst)
        ce.modify()
        logging.info("Modified meter entry in device: "+str(dev))


# def addCloneSessionForEachPort(dev, maxPort):
#     '''
#     This function will create a session entry for each port and add that port to that session. this will help us to clone a paclet to specific port
#     :param dev:
#     :param maxPort:
#     :return:
#     '''
#     cmdString = ""
#     for i in range(1 , maxPort+1):
#         # cloneSessionEntry = sh.CloneSessionEntry(dev,i)
#         # cloneSessionEntry.add(i, int(i))
#         # val = cloneSessionEntry.insert()
#         # print(val)
#         # this was supposed to work but not works. So we are forced to use the cli
#         # cli format is : Add mirroring session to unicast port: mirroring_add <mirror_id> <egress_port>
#         cmdString = cmdString+  "mirroring_add "+ str(i)+" "+str(i)+" \n"
#         if(i!= InternalConfig.CPU_PORT):   # no need to add CPU port twice
#             cmdString = cmdString+  "mirroring_add "+ str(i+ConfConst.MAX_PORT_NUMBER)+" "+str(i)+" \n"
#             cmdString = cmdString+  "mirroring_add "+ str(i+ConfConst.MAX_PORT_NUMBER)+" "+str(InternalConfig.CPU_PORT)+" \n"
#         if(i!= InternalConfig.CPU_PORT):   # no need to add CPU port twice
#             cmdString = cmdString+  "mirroring_add "+ str(i+ (2* ConfConst.MAX_PORT_NUMBER))+" "+str(i)+" \n"
#             cmdString = cmdString+  "mirroring_add "+ str(i+ (2* ConfConst.MAX_PORT_NUMBER))+" "+str(InternalConfig.CPU_PORT)+" \n"
#             cmdString = cmdString+  "mirroring_add "+ str(i+ (2* ConfConst.MAX_PORT_NUMBER))+" "+str(9999)+" \n"   # Special clone for recirculation
#     dev.executeCommand(cmdString)

def addCloneSessionForEachPort(dev, maxPort):
    '''
    This function will create a session entry for each port and add that port to that session. this will help us to clone a paclet to specific port
    :param dev:
    :param maxPort:
    :return:
    '''
    cmdString = ""
    for i in range(1 , maxPort+1):
        #print("Adding multicast group for "+dev.devName+" port "+str(i))
        dev.addMultiCastGroup(listOfPorts= [i], mcastGroupId= i)

        cmdString = cmdString+  "mirroring_add_mc "+ str(i)+" "+str(i)+" \n"
        if(i!= InternalConfig.CPU_PORT):   # no need to add CPU port twice
            dev.addMultiCastGroup(listOfPorts= [i,InternalConfig.CPU_PORT], mcastGroupId= i+ConfConst.MAX_PORT_NUMBER)
            cmdString = cmdString+  "mirroring_add_mc "+ str(i+ConfConst.MAX_PORT_NUMBER)+" "+str(i+ConfConst.MAX_PORT_NUMBER)+" \n"
            # cmdString = cmdString+  "mirroring_add "+ str(i+ConfConst.MAX_PORT_NUMBER)+" "+str(i)+" \n"
            # cmdString = cmdString+  "mirroring_add "+ str(i+ConfConst.MAX_PORT_NUMBER)+" "+str(InternalConfig.CPU_PORT)+" \n"
        if(i!= InternalConfig.CPU_PORT):   # no need to add CPU port twice
            dev.addMultiCastGroup(listOfPorts= [i,InternalConfig.CPU_PORT, 0], mcastGroupId= i+ (2 * ConfConst.MAX_PORT_NUMBER))
            cmdString = cmdString+  "mirroring_add_mc "+ str(i+ (2 * ConfConst.MAX_PORT_NUMBER))+" "+str(i+ (2 * ConfConst.MAX_PORT_NUMBER))+" \n"
            # cmdString = cmdString+  "mirroring_add "+ str(i+ (2* ConfConst.MAX_PORT_NUMBER))+" "+str(i)+" \n"
            # cmdString = cmdString+  "mirroring_add "+ str(i+ (2* ConfConst.MAX_PORT_NUMBER))+" "+str(InternalConfig.CPU_PORT)+" \n"
            # cmdString = cmdString+  "mirroring_add "+ str(i+ (2* ConfConst.MAX_PORT_NUMBER))+" "+str(9999)+" \n"   # Special clone for recirculation
    dev.executeCommand(cmdString)

def readPacketCounter(dev, counterName, counterIndex):
    ce = sh.CounterEntry(dev,counterName)
    ce.index = counterIndex
    for c in ce.read():
        return int(c.data.packet_count)


def collectPacketCounterForAllPort(dev, counterName):
    statMap = {}
    for i in range(0, dev.maxPort):
        val = readPacketCounter(dev, counterName,i)
        # if(val>0):
        #     statMap[i] = val
        statMap[i] = val
    return statMap

def resetPacketCounterForAllPort(dev, counterName):
    for i in range(0, dev.maxPort):
        modifyPacketCounter(dev, counterName,i, 0)


def modifyPacketCounter(dev, counterName, counterIndex, valueTobeWritten):
    ce = sh.CounterEntry(dev,counterName)
    ce.index = counterIndex
    ce.packet_count = valueTobeWritten
    ce.modify()

def readAllCounters(dev):
    COUNTER_NAMES = {"egressPortCounter", "ingressPortCounter", "ctrlPktToCPCounter", "p2pFeedbackCounter"}

    egressPortStats = collectPacketCounterForAllPort(dev, "egressPortCounter")
    ingressPortStats = collectPacketCounterForAllPort(dev, "ingressPortCounter")
    ctrlPkttoCPStats = collectPacketCounterForAllPort(dev, "ctrlPktToCPCounter")
    p2pFeedbackStats = collectPacketCounterForAllPort(dev, "p2pFeedbackCounter")

    return egressPortStats, ingressPortStats , ctrlPkttoCPStats,  p2pFeedbackStats


def resetAllCounters(dev):
    COUNTER_NAMES = {"egressPortCounter", "ingressPortCounter", "ctrlPktToCPCounter", "p2pFeedbackCounter"}
    resetPacketCounterForAllPort(dev, "egressPortCounter")
    resetPacketCounterForAllPort(dev, "ingressPortCounter")
    resetPacketCounterForAllPort(dev, "ctrlPktToCPCounter")
    resetPacketCounterForAllPort(dev, "p2pFeedbackCounter")


def getAlgo(dev, dpAlgo):
    '''
    This function returns the algorithm implementation for each device. For distributed algo this is simple name to object mapping.
    For centralized algo, we may need to implement a singletone pattern
    '''
    # TODO : Can we make an array in config and write them there. This function will only read the arrray and load relevant classses??
    if (dpAlgo == ConfConst.DataplnaeAlgorithm.DP_ALGO_BASIC_ECMP) :
        return ecmpRouting.ECMPRouting(dev = dev)
    elif (dpAlgo == ConfConst.DataplnaeAlgorithm.DP_ALGO_CP_ASSISTED_POLICY_ROUTING) :
        return multiCritPolicyRouting.CPAssistedMultiCriteriaPolicyRoutingAlgorithm(dev = dev)
    pass

# def getLinearMetricsLevels(startingValue, interval, endingValue):
#     '''
#     This functions generates metrics LEvel in linear scale
#     :param startingValue: for which value to start. As example for range 0-100, starting value will be 0
#     :param interval: difference between subsequent levels
#     :param endingValue: where to stop . for example 0-100, endingValue will be 100
#     :return:
#     '''
#     totalLevels = (endingValue-startingValue) / interval
#     for i in range(0, )
#     return

def getMetricsLevelFromTuppleList(tuppleList):
    metricLevelList = []
    for t in tuppleList:
        temp = jp.MetricsLevel(t[0],t[1],t[2],t[3])
        metricLevelList.append(temp)
    return metricLevelList
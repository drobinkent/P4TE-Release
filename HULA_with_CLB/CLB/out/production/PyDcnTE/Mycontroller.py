#from p4.v1 import p4runtime_pb2
from P4Runtime import JsonParser as jp
import sys
import P4Runtime.leafSwitchUtils
from P4Runtime.JsonParser import DeviceType, Device, Host
from P4Runtime.utils import getDeviceTypeFromName, reverseAndCreateNewLink
import ConfigConst as ConfConst
import sys, paramiko
import P4Runtime.SwitchUtils as swUtils
import P4Runtime.StatisticsPuller
import testAndMeasurement.ResultProcessor as rp
#sys.path.append("./P4Runtime/JsonParser")
import json
import logging
logger = logging.getLogger('DCNTEController')
hdlr = logging.FileHandler(ConfConst.CONTROLLER_LOG_FILE_PATH)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)


class MyP4Controller():
    def __init__(self, cfgFileName):
        self.nameToSwitchMap = {}
        self.nameToHostMap = {}
        self.cfgFileName = cfgFileName
        print("Starting MyP4Controller with config file ",cfgFileName)
        self.loadCFG(cfgFileName)

    def loadCFG(self,cfgfileName):
        cfgFile = open(cfgfileName)
        obj = json.load(fp=cfgFile)
        for devName in obj["devices"]:
            try:
                dev = jp.Device.from_dict(devName, obj["devices"][devName])
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
            p = jp.Port.from_dict(obj["ports"][portLoc])
            logger.info("New port is "+ str(p))
            pass
        for hostMac in obj["hosts"]:
            h = jp.Host.from_dict( obj["hosts"][hostMac])
            self.nameToHostMap[h.basic.name] = h
            logger.info("New host is "+str(h))
        for i in range (0, len(obj["alllinks"]["links"])):
            l = jp.Link.from_dict(obj["alllinks"]["links"][i])
            logger.info("Attching :Link is "+str(l))
            self.attachLink(l)
            logger.info("Attching link from reverse direction:Link is "+str(l))
            self.attachLink(reverseAndCreateNewLink(l))
        cfgFile.close()
        logger.info("Finished reading and loading cfg")

    def attachLink(self, l):
        #logger.debug("Processing link:"+str(l))
        #logger.debug("link Start node "+str(l.node1)+" is of type "+str(getDeviceTypeFromName(l.node1)))
        #logger.debug("link end node "+str(l.node2)+" is of type "+str(getDeviceTypeFromName(l.node2)))
        if(getDeviceTypeFromName(l.node1) == DeviceType.INVALID) :
            logger.error("Node 1 of link: "+l+" is of type INVALID. Exiting")
            exit(-1)
        if(getDeviceTypeFromName(l.node2) == DeviceType.INVALID) :
            logger.error("Node 2 of link: "+l+" is of type INVALID. Exiting")
            exit(-1)
        # From here it means both end of the link is valid.
        if((getDeviceTypeFromName(l.node1) == DeviceType.LEAF_SWITCH) or
        (getDeviceTypeFromName(l.node1) == DeviceType.SPINE_SWITCH) or
        (getDeviceTypeFromName(l.node1) == DeviceType.SUPER_SPINE_SWITCH)):
            srcSwitch = self.nameToSwitchMap.get(l.node1)
            if (srcSwitch == None):
                logger.critical("Node 1 of link"+str(l)+"Not found in nameToSwitchMap")
                exit(-1)
            else:
                if((getDeviceTypeFromName(l.node2) == DeviceType.LEAF_SWITCH) or
                (getDeviceTypeFromName(l.node2) == DeviceType.SPINE_SWITCH) or
                (getDeviceTypeFromName(l.node2) == DeviceType.SUPER_SPINE_SWITCH)):
                    destSwitch = self.nameToSwitchMap.get(l.node2)
                    if (destSwitch == None):
                        logger.critical("Node 2 of link"+str(l)+"Not found in nameToSwitchMap")
                        exit(-1)
                    else:
                        if (getDeviceTypeFromName(l.node2) == DeviceType.LEAF_SWITCH):
                            srcSwitch.portToLeafSwitchMap[l.port1] = destSwitch
                        elif (getDeviceTypeFromName(l.node2) == DeviceType.SPINE_SWITCH):
                            srcSwitch.portToSpineSwitchMap[l.port1] = destSwitch
                        elif (getDeviceTypeFromName(l.node2) == DeviceType.SUPER_SPINE_SWITCH):
                            srcSwitch.portToSuperSpineSwitchMap[l.port1] = destSwitch
                elif(getDeviceTypeFromName(l.node2) == DeviceType.HOST):
                    destHost = self.nameToHostMap.get(l.node2)
                    if (destHost == None):
                        logger.critical("Node 2 of link"+str(l)+"Not found in nametoHostMap")
                        exit(-1)
                    else:
                        srcSwitch.portToHostMap[l.port1] = destHost
        elif (getDeviceTypeFromName(l.node1) == DeviceType.HOST):
            srcHost = self.nameToHostMap.get(l.node1)
            if (srcHost == None):
                logger.critical("Node 1 of link"+str(l)+"Not found in nameToHostMap")
                exit(-1)
            else:
                if (getDeviceTypeFromName(l.node2) == DeviceType.LEAF_SWITCH):
                    destSwitch = self.nameToSwitchMap.get(l.node2)
                    if (destSwitch == None):
                        logger.critical("Node 2 of link"+str(l)+"Not found in nameToSwitchMap")
                        exit(-1)
                    else:
                        srcHost.portToLeafSwitchMap[l.port1] = destSwitch

        pass

    # For leaf switches, incoming ports from leaf switches will have queue rate " hostToLeafMaxQueueRate =  baseQueueRate*hosttoLeafOverSupscriptionRatio" and
    # outgoing ports toward spine switches will have queue rate of leafToSpineMaxQueueRate =  baseQueueRate. This queue rate setup is equivalent to link speed for bmv2 simpleSwitch.
    # Same way, in spine switches, incoming ports from leaf switches will have queue rate of baseQuerate
    def initialDeviceRouteAndRateSetup(self, queueRateForHostFacingPortsOfLeafSwitch, queueRateForSpineFacingPortsOfLeafSwitch,
                                       queueRateForLeafSwitchFacingPortsOfSpineSwitch, queueRateForSuperSpineSwitchFacingPortsOfSpineSwitch,
                                       queueRateForSpineSwitchFacingPortsOfSuperSpineSwitch, queueRateForExternalInternetFacingPortsOfSuperSpineSwitch,
                                       testScenario = ConfConst.TestScenario.BASIC_ECMP):
        #------------Usually  buffer size should be Delay *  bandwidth . for bmv2 based testing this have to be represented and configured through Queue depth.
        # ------ So we will multiply port bandwidth by a factor to estimate the Delay *  BW . So by this factor we are actually estimating the Delay factor.
        queueRateToDepthFactor = ConfConst.QUEUE_RATE_TO_QUEUE_DEPTH_FACTOR

        for sName in self.nameToSwitchMap.keys():
            s = (self.nameToSwitchMap.get(sName))
            logger.info("Setting up Queue rate for all switch. This is equavalent to setup line rate setup in bmv2 devices")

            #s = Device()
            if (s.fabric_device_config.switch_type == jp.SwitchType.LEAF ):
                s.queueRateSetupForLeafSwitch(queueRateForHostFacingPortsOfLeafSwitch, queueRateForSpineFacingPortsOfLeafSwitch,queueRateToDepthFactor)
            if (s.fabric_device_config.switch_type == jp.SwitchType.SPINE ):
                s.queueRateSetupForSpineSwitch(queueRateForLeafSwitchFacingPortsOfSpineSwitch, queueRateForSuperSpineSwitchFacingPortsOfSpineSwitch, queueRateToDepthFactor)
            if (s.fabric_device_config.switch_type == jp.SwitchType.SUPER_SPINE ):
                s.queueRateSetupForSuperspineSwitch(queueRateForSpineSwitchFacingPortsOfSuperSpineSwitch, queueRateForExternalInternetFacingPortsOfSuperSpineSwitch, queueRateToDepthFactor)
            swUtils.addCloneSessionForEachPort(s, s.maxPort)
            swUtils.setupIngressEgressStats(s)
            #====================
            if (testScenario == ConfConst.TestScenario.BASIC_ECMP):
                print("This call is for baseline setup and should only work if in P4 file we have enabled Baseline flag.")
                s.initialBaseLineSetup()
            else:
                print("Setting Data plane programs for our medianet dcn solution")

                # this section will have code for evaluation that are special to our solution. For example how many times a table entry habe been updated and other.
                pass

            # This section will contain code for evaluation report of both the solution

    def startMonitoringFromController(self):
        # this method will pull various counter and register values from the switches and plot data accordingly.
        #Also save the collected statitstics for each device in corresponding data structure.
        self.statisticsPuller = P4Runtime.StatisticsPuller.StatisticsPuller(self.nameToSwitchMap)


# you can omit the config argument if the switch is already configured with the
# correct P4 dataplane.

p4ctrlr = MyP4Controller("./MininetSimulator/Build/Internalnetcfg.json")
print(p4ctrlr)
# p4ctrlr.initialDeviceRouteAndRateSetup( queueRateForHostFacingPortsOfLeafSwitch = 10 , queueRateForSpineFacingPortsOfLeafSwitch = 10,
#                                        queueRateForLeafSwitchFacingPortsOfSpineSwitch= 10, queueRateForSuperSpineSwitchFacingPortsOfSpineSwitch=10,
#                                        queueRateForSpineSwitchFacingPortsOfSuperSpineSwitch=10, queueRateForExternalInternetFacingPortsOfSuperSpineSwitch=100,
#                                         #testScenario = None
#                                        )


# p4ctrlr.initialDeviceRouteAndRateSetup( queueRateForHostFacingPortsOfLeafSwitch = 1 , queueRateForSpineFacingPortsOfLeafSwitch = 1,
#                                         queueRateForLeafSwitchFacingPortsOfSpineSwitch= 1, queueRateForSuperSpineSwitchFacingPortsOfSpineSwitch=1,
#                                         queueRateForSpineSwitchFacingPortsOfSuperSpineSwitch=1, queueRateForExternalInternetFacingPortsOfSuperSpineSwitch=1000,
#                                         #testScenario = None
#                                         )


p4ctrlr.initialDeviceRouteAndRateSetup( queueRateForHostFacingPortsOfLeafSwitch = 1000 , queueRateForSpineFacingPortsOfLeafSwitch = 1000,
                                        queueRateForLeafSwitchFacingPortsOfSpineSwitch= 1000, queueRateForSuperSpineSwitchFacingPortsOfSpineSwitch=1000,
                                        queueRateForSpineSwitchFacingPortsOfSuperSpineSwitch=1000, queueRateForExternalInternetFacingPortsOfSuperSpineSwitch=1000,
                                        #testScenario = None
                                        )

p4ctrlr.startMonitoringFromController()




#
# clnt, context = sh.setup(
#     device_id=1,
#     grpc_addr='0.0.0.0:62003',
#     election_id=(0, 1), # (high, low)
#     config=sh.FwdPipeConfig('./Build/spine_p4info.txt', './Build/spine.json')
# )
#
# b = DeviceBasic(management_address= "grpc://127.0.0.1:62000?device_id=1", driver = None, pipeconf=None  )
# fb = FabricDeviceConfig(my_station_mac= None, switch_type= SwitchType.SPINE, switch_host_subnet_prefix= "testSubnet")
# dev = Device("testDev",b, fb )
# dev.client=clnt
# dev.context = context
# #see p4runtime_sh/test.py for more examples
# # te = sh.TableEntry('<table_name>')(action='<action_name>')
# # te.match['<name>'] = '<value>'
# # te.action['<name>'] = '<value>'
# # te.insert()
#
# # ...
#
# ce = sh.MeterEntry(dev=dev,meter_name="my_meter_indirect")
# ce.index = 99
# ce.cir = 1
# ce.cburst = 2
# ce.pir = 3
# ce.pburst = 4
# ce.modify()
#
# ce = sh.MeterEntry(dev=dev,meter_name="my_meter_indirect")
# ce.index = 4
# val = ce.read()
# #print(str(val._entity))
# ce = sh.MeterEntry(dev=dev,meter_name="my_meter_indirect")
# ce.index = 99
# for c in ce.read():
#     print(c)
#
# te = sh.TableEntry(dev=dev,table_name='downstream_routing_table')(action='set_downstream_egress_port')
# te.match['hdr.ipv6.dst_addr'] = '2000101010100101'
# te.action['port_num'] = '3'
# te.action['dmac'] = '0xa0a0a0a0a'
# te.insert()
#
# #vals= te.read()
# print("Printing")
# for v in te.read():
#     print(v)
#
# # connection = sh.client
# # while True:
# #     packet = "Hello world"
# #     send_packet_out(packet, 255, sh.client)
# #
# #     print("Waiting for recive something")
# #     packet = connection.stream_in_q.get()
# #
# #     print("Packet received!:" + str(packet))
# #     connection.stream_out_q.put(packet)
# #
# #
# #
# #
# sh.teardown()
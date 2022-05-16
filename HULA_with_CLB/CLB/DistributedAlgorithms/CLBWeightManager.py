import logging
import logging.handlers
import P4Runtime.JsonParser as jp
import P4Runtime.leafSwitchUtils as leafUtils
import P4Runtime.spineSwitchUtils as  spineUtils
import P4Runtime.superSpineSwitchUtils as  superSpineUtils
import P4Runtime.SwitchUtils as swUtils
import InternalConfig
import P4Runtime.shell as sh
from DistributedAlgorithms.RoutingInfo import RoutingInfo
import DistributedAlgorithms.LoadBalancer as lb
import ConfigConst as ConfConst
logger = logging.getLogger('Shell')
logger.handlers = []
hdlr = logging.handlers.RotatingFileHandler(ConfConst.CONTROLLER_LOG_FILE_PATH, maxBytes = ConfConst.MAX_LOG_FILE_SIZE , backupCount= ConfConst.MAX_LOG_FILE_BACKUP_COUNT)
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)

class CLBWeightManager:

    def __init__(self, dev):
        self.p4dev = dev
        self.torID = -1
        self.torIDToCLB={}

        pass

    def setup(self,nameToSwitchMap):

        self.nameToSwitchMap = nameToSwitchMap
        if self.p4dev.fabric_device_config.switch_type == jp.SwitchType.LEAF:
            lb.initMAT(self.p4dev, ConfConst.BITMASK_LENGTH)
            self.upwardPortList = list(self.p4dev.portToSpineSwitchMap.keys())
            self.calculateCapacityOfUpwardLinksAndInitialDistribution()
            e = self.p4dev.fabric_device_config.switch_host_subnet_prefix.index("/")
            # leafSubnetAsIP = self.p4dev.fabric_device_config.switch_host_subnet_prefix[0:e]
            r1 = self.p4dev.fabric_device_config.switch_host_subnet_prefix.rindex(":")
            r2 = self.p4dev.fabric_device_config.switch_host_subnet_prefix[0:r1].rindex(":")
            self.torID = int(self.p4dev.fabric_device_config.switch_host_subnet_prefix[r2+1:r1])
            logger.info("CLB Initial setup  for "+str(self.p4dev.devName) + " is complete. It's ip prefix is "+str(self.p4dev.fabric_device_config.switch_host_subnet_prefix)+" and tor id is "+str(self.torID))
            # now calculate what should be the initial weight config of the ports.
            # find wha tis the total capacity of the upword ports. Through tpotal tor switches. the bitmasklenght and precision will be fixed. ]
            for i in range (0, ConfConst.MAX_TOR_SUBNET):
                clbObejct = lb.LoadBalanacer(torID = i,  allLinksAsList=self.upwardPortList, bitMaskLength=ConfConst.BITMASK_LENGTH, nameToSwitchMap=self.nameToSwitchMap)
                self.torIDToCLB[i] = clbObejct
                clbObejct.getAccumulatedDistribution(self.initialAccumulatedWeightDistribution)
                pktOutlist = clbObejct.installDistributionInCPAndGeneratePacketOutMessages(self.initialAccumulatedWeightDistribution, firstTimeFlag = True)
                for p in pktOutlist:
                    self.p4dev.send_already_built_control_packet_for_load_balancer(p)
        return

    def calculateCapacityOfUpwardLinksAndInitialDistribution(self):
        '''
        This function calculates the full total capacit of the upward links and assign intiial equal weight to each link
        :return:
        '''
        self.totalUpwordCapacity = 0
        totoalNumberOfPorts = len(self.upwardPortList)
        self.initialAccumulatedWeightDistribution = []
        for p in self.upwardPortList:
            self.totalUpwordCapacity = self.totalUpwordCapacity + int(self.p4dev.portToQueueRateMap[str(p)])
        if(self.totalUpwordCapacity> ConfConst.BITMASK_LENGTH * ConfConst.PRECISION_OF_LOAD_BALANCING):
            logger.error("You have configured total capacity of the upword ports as "+str(self.totalUpwordCapacity) + " packets per second. And the BITMASK length for CLB is "+str(ConfConst.BITMASK_LENGTH))
            logger.error("And the PRecisoin of load balancing as "+str(ConfConst.PRECISION_OF_LOAD_BALANCING))
            logger.error("But if self.totalUpwordCapacity> ConfConst.BITMASK_LENGTH * ConfConst.PRECISION_OF_LOAD_BALANCING then the scheme can not handle the load balancing correctly.so exiting")
            exit(1)
        perPortWeight=0
        for p in self.upwardPortList:
            perPortWeight = perPortWeight + int(int(self.p4dev.portToQueueRateMap[str(p)])/ConfConst.PRECISION_OF_LOAD_BALANCING)
            self.initialAccumulatedWeightDistribution.append((p, perPortWeight))
        # do a check here to make sure that someone not configuring a precision and wight of the links such that the bitmask can no handle it.
        #simply check whther the load and precision range can be supported by the speificed bitmaks length or not.





    def processFeedbackPacket(self, parsedPkt, dev):
        #print("Called the algo")
        #TODO: for each of the different types of the packet, we have to write a separate function to process them
        # self.ingress_port= packet.metadata[0];
        # self._pad= packet.metadata[1];
        # self.ingress_queue_event= packet.metadata[2];   -- type 1
        # self.ingress_queue_event_data= packet.metadata[3];
        # self.egress_queue_event= packet.metadata[4];  -- type 2
        # self.egress_queue_event_data= packet.metadata[5];
        # self.ingress_traffic_color= packet.metadata[6];  --   -- type 3 . if color is 0 then green, then we may not need to do anything. Here color itself shows the event
        # self.ingress_rate_event_data= packet.metadata[7];
        # self.egress_traffic_color= packet.metadata[8];   -- same as ingress traffic color
        # self.egress_rate_event_data= packet.metadata[9];
        # self.path_delay_event_type= packet.metadata[11];  # -- type 4 delay event
        # self.delay_event_src_type= packet.metadata[10];
        # self.path_delay_event_data= packet.metadata[12];
        # self.dest_IPv6_address= packet.metadata[13];
        # if parsedPkt.ingress_queue_event >0:
        #     print("Valid ingress_queue_event :"+str(parsedPkt.ingress_queue_event))
        # if parsedPkt.egress_queue_event >0:
        #     print("Valid egress_queue_event"+str(parsedPkt.egress_queue_event))
        # if parsedPkt.ingress_traffic_color >0:
        #     print("Valid ingress_traffic_color :"+ str(parsedPkt.ingress_traffic_color))
        # if parsedPkt.egress_traffic_color >0:
        #     print("Valid ingress_traffic_color :"+str(parsedPkt.egress_traffic_color))
        # if parsedPkt.path_delay_event_type >0:
        #     print("Valid path_delay_event_type :"+str(parsedPkt.path_delay_event_type))
        pass

    def processStatisticsPulledFromSwitch(self,torID, accumulatedWeightDistribution):
        clbForTOR = self.torIDToCLB.get(torID)
        clbForTOR.installDistributionInCPAndGeneratePacketOutMessages(accumulatedWeightDistribution, firstTimeFlag = False)


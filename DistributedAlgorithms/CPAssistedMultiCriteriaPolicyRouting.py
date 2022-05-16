import logging
import logging.handlers
import P4Runtime.JsonParser as jp

import InternalConfig
import P4Runtime.shell as sh
from DistributedAlgorithms.RoutingInfo import RoutingInfo
import ConfigConst as ConfConst
logger = logging.getLogger('CPAssistedMultiCriteriaPolicyRoutingAlgorithm')
logger.handlers = []
hdlr = logging.handlers.RotatingFileHandler(ConfConst.CONTROLLER_LOG_FILE_PATH, maxBytes = ConfConst.MAX_LOG_FILE_SIZE , backupCount= ConfConst.MAX_LOG_FILE_BACKUP_COUNT)
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)

class CPAssistedMultiCriteriaPolicyRoutingAlgorithm:

    def __init__(self, dev):
        self.p4dev = dev
        self.delayBasedRoutingInfo = RoutingInfo(name = "Delay Based Routing Info Store-"+self.p4dev.devName) # In both of this routing group, for each port there will be a group member. Port number and group memeber_id are same
        self.egressQueueDepthBasedRoutingInfo = RoutingInfo(name = "Egress queue Depth Based Routing Info Store-"+self.p4dev.devName)
        self.egressPortRateBasedRoutingInfo = RoutingInfo(name = "Egress port traffic rate Based Routing Info Store-"+self.p4dev.devName)
        pass

    def setup(self):
        '''
        This function setup all the relevant stuffs for running the algorithm
        '''
        self.p4dev.ctrlPlaneLogic.addGroupsForStepBasedRouting()
        self.emptyGroupHandlerMemberForEgressQueueDepthBasedRoutingTable, \
                self.emptyGroupHandlerMemberForEgressRateBasedRoutingTable= self.addDummyActionProfileMemberForHandlingEmptyRoutingGroup()
        self.p4dev.ctrlPlaneLogic.initializeUpstreamRouting()

        return None

    def processFeedbackPacket(self, parsedPkt, dev):
        #print("Called the algo")
        #self.ingress_port= int.from_bytes(packet.metadata[0].value, byteorder='big', signed=True)
        # self._pad= packet.metadata[1].value
        # self.ingress_queue_event= int.from_bytes(packet.metadata[2].value, byteorder='big', signed=True)
        # self.ingress_queue_event_data= int.from_bytes(packet.metadata[3].value, byteorder='big', signed=True)
        # self.ingress_queue_event_port=int.from_bytes(packet.metadata[4].value, byteorder='big', signed=True)

        # self.egress_queue_event= int.from_bytes(packet.metadata[5].value, byteorder='big', signed=True)
        # self.egress_queue_event_data= int.from_bytes(packet.metadata[6].value, byteorder='big', signed=True) #----- Event handling  for this is done
        # self.egress_queue_event_port = int.from_bytes(packet.metadata[7].value, byteorder='big', signed=True)

        # self.ingress_traffic_color= int.from_bytes(packet.metadata[8].value, byteorder='big', signed=True)
        # self.ingress_rate_event_data= int.from_bytes(packet.metadata[9].value, byteorder='big', signed=True)
        # self.ingress_rate_event_port=int.from_bytes(packet.metadata[10].value, byteorder='big', signed=True)

        # self.egress_traffic_color= int.from_bytes(packet.metadata[11].value, byteorder='big', signed=True)
        # self.egress_rate_event_data= int.from_bytes(packet.metadata[12].value, byteorder='big', signed=True)
        # self.egress_rate_event_port=int.from_bytes(packet.metadata[13].value, byteorder='big', signed=True)

        # self.delay_event_src_type= int.from_bytes(packet.metadata[14].value, byteorder='big', signed=True)
        # self.path_delay_event_type= int.from_bytes(packet.metadata[15].value, byteorder='big', signed=True)  #---------Event handling  for this is done
        # self.path_delay_event_data= int.from_bytes(packet.metadata[16].value, byteorder='big', signed=True)
        # self.dest_IPv6_address= ipaddress.IPv6Address( packet.metadata[17].value ) # eed to convert this to ipv6 address
        # self.path_delay_event_port=int.from_bytes(packet.metadata[18].value, byteorder='big', signed=True)
        try:
            self.processEgressQueueDepthEvent(parsedPkt=parsedPkt)
            self.processPathDelayEvent(parsedPkt=parsedPkt)
            self.processEgressRateEvent(parsedPkt=parsedPkt)
        except Exception:
            logger.exception("Exception in Processing contrl Packet")
            exit(1)
        # if egress queue depth/path delay/ egress rate -- increase event found decrease it's level aand priority
        # if egress queue depth/path delay/ egress rate -- decrease event found increase it's level aand priority
        #
        # egress rate is too instantanous. so only once update found is may be not a very good measure. if we find same evenet in a row it may be a better thing. also implement that

        return

    def processIngressQueueEvent(self,parsedPkt):
    #     EVENT_ING_QUEUE_UNCHANGED = 10
    #     EVENT_ING_QUEUE_INCREASED = 11  #These 3 events notifies if a packet has seen change in delay by threshold
    #     EVENT_ING_QUEUE_DECREASED = 12
        ingPort = parsedPkt.ingress_queue_event_port
        if(parsedPkt.ingress_queue_event == InternalConfig.EVENT_ING_QUEUE_INCREASED):
            logger.info("EVENT_ING_QUEUE_INCREASED event found")
        elif (parsedPkt.ingress_queue_event == InternalConfig.EVENT_ING_QUEUE_DECREASED):
            logger.info("EVENT_ING_QUEUE_DECREASED event found")
        else:
            #logger.info("Unhandled Inress Queue Event: "+parsedPkt.egress_queue_event)
            return
        return


    def processEgressQueueDepthEvent(self, parsedPkt):
            # EVENT_EGR_QUEUE_UNCHANGED = 10
            # EVENT_EGR_QUEUE_INCREASED = 11  #These 3 events notifies if a packet has seen change in delay by threshold
            # EVENT_EGR_QUEUE_DECREASED = 12
        out1 = ""
        out2 = ""
        out3 = ""
        try:
            egPort = parsedPkt.egress_queue_event_port
            # out1 , err = self.p4dev.executeCommand("table_dump "+ "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_queue_depth_based_upstream_path_table"+"\n")
            # logger.info("table condition at start of function"+str(out))
            oldActionProfileGroup = self.egressQueueDepthBasedRoutingInfo.getGroupByPortNumber(egPort)
            if(oldActionProfileGroup == None):
                # logger.info("Egress Queue Event found for unnecessary port where no path diversity exists. So returning")
                return
            actionProfileMemberObject = self.egressQueueDepthBasedRoutingInfo.getMemberFromPortToActionProfileMemberMap(port=egPort)
            if actionProfileMemberObject == None:
                logger.info("Action Profile member object for port "+str(egPort)+" not exists in "+self.egressQueueDepthBasedRoutingInfo.name+". Severe Problem. Debug. Exiting")
                exit(1)

            #Find new group to which nnede tp attach
            newActionProfileGroup = None
            priorityOfNewActionProfileGroup = None
            if(parsedPkt.egress_queue_event == InternalConfig.EVENT_EGR_QUEUE_INCREASED):
                #logger.info("EVENT_EGR_QUEUE_INCREASED event found")
                newActionProfileGroup, priorityOfNewActionProfileGroup = self.findActionProfileGroupForEgressQueueDepthIncreaseEvent(currentGroup=oldActionProfileGroup)
            elif (parsedPkt.egress_queue_event == InternalConfig.EVENT_EGR_QUEUE_DECREASED):
                #logger.info("EVENT_EGR_QUEUE_DECREASED event found")
                newActionProfileGroup, priorityOfNewActionProfileGroup =self.findActionPrfileGroupForEgressQueueDepthDecreaseEvent(currentGroup=oldActionProfileGroup)
            else:
                #logger.info("Unhandled Egress Queue Event: "+str(parsedPkt.egress_queue_event))
                return
            if(oldActionProfileGroup.group_id == newActionProfileGroup.group_id):
                # logger.info("No need to do group moving bcz old and new action profile group are same")
                return
            if ( (len(oldActionProfileGroup.members)==1)) :
                if (InternalConfig.EMPTY_GROUP_MEMBER_ID_FOR_EGRESS_QUEUE_DEPTH_BASED_ROUTING_TABLE == oldActionProfileGroup.members[0].member_id):
                    logger.debug("Ideally this should not happen. Debug and exiting")
                    exit(1)
                else:
                    #logger.info("Only one member is in group. But that is not the empty member handler group. Hence before deleting  this member we need to enter the empty member handler in this group ")
                    oldActionProfileGroup.add(self.emptyGroupHandlerMemberForEgressQueueDepthBasedRoutingTable.member_id)
                    oldActionProfileGroup.del_member_from_group(member = actionProfileMemberObject)
                    oldActionProfileGroup.modify()
                    #oldActionProfileGroup._update_msg()
                    self.egressQueueDepthBasedRoutingInfo.deletePortNumToGroupMapping(egPort)
                    # TODO: keep a data strucuture for each group id to lower and higher value of the range
                    # logger.info("Printing values in old group: local_metadata.egr_queue_depth_value_range-- rangeField1LowerValue="+str(self.egressQueueDepthBasedRoutingInfo.getMetricsLevelRangeLowerValueMap(oldActionProfileGroup.group_id))
                    #             +"rangefield1HigherValue ="+str(self.egressQueueDepthBasedRoutingInfo.getMetricsLevelRangeHigherValueMap(oldActionProfileGroup.group_id))+
                    #             "rangeField2Name = local_metadata.minimum_group_members_requirement--rangeField2LowerValue=0, rangefield2HigherValue =0"
                    #             +" rangeField2ModifedLowerValue = 1, rangefield2ModifiedHigherValue = "+str(InternalConfig.DUMMY_MAX_MINIMUM_GROUP_MEMBERS_REQUIREMENT)
                    #             +" groupID = "+str(oldActionProfileGroup.group_id)+ " priority="+str(self.egressQueueDepthBasedRoutingInfo.getTernaryTableEntryPriorityValueForTheGroup(oldActionProfileGroup.group_id)))
                    self.p4dev.modifyLPMMatchEntryWithGroupActionWith2RangeField(tableName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_queue_depth_based_upstream_path_table",
                         fieldName = "hdr.ipv6.dst_addr", fieldValue= InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength = InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
                         rangeField1Name = "local_metadata.egr_queue_depth_value_range",
                         rangeField1LowerValue=self.egressQueueDepthBasedRoutingInfo.getMetricsLevelRangeLowerValueMap(oldActionProfileGroup.group_id),
                         rangefield1HigherValue =self.egressQueueDepthBasedRoutingInfo.getMetricsLevelRangeHigherValueMap(oldActionProfileGroup.group_id),
                         rangeField2Name = "local_metadata.minimum_group_members_requirement", rangeField2LowerValue=1, rangefield2HigherValue =InternalConfig.DUMMY_MAX_MINIMUM_GROUP_MEMBERS_REQUIREMENT,
                         rangeField2ModifedLowerValue = 0, rangefield2ModifiedHigherValue = 0,
                         actionName= None, actionParamName=None, actionParamValue=None,
                         groupID = oldActionProfileGroup.group_id, priority=self.egressQueueDepthBasedRoutingInfo.getTernaryTableEntryPriorityValueForTheGroup(oldActionProfileGroup.group_id))
                    #logger.info("Deleted port from old group in egress queue event handler")
            else:

                # out1 , err = self.p4dev.executeCommand("table_dump "+ "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_queue_depth_based_upstream_path_table"+"\n")
                # logger.info(self.p4dev.devName+"There are more than one action profile members in this group. So required actrion profile member can be removed safely.Before deleting"+str(out1))
                oldActionProfileGroup.del_member_from_group(member = actionProfileMemberObject)
                oldActionProfileGroup.modify()
                self.egressQueueDepthBasedRoutingInfo.deletePortNumToGroupMapping(egPort)
                # out1 , err = self.p4dev.executeCommand("table_dump "+ "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_queue_depth_based_upstream_path_table"+"\n")
                # logger.info(self.p4dev.devName+"There are more than one action profile members in this group. So required actrion profile member can be removed safely.After deleting"+str(out1))
                #logger.info("Deleted port from old group in egress queue event handler")
            #add to that oldActionProfileGroup
            # out2 , err = self.p4dev.executeCommand("table_dump "+ "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_queue_depth_based_upstream_path_table"+"\n")
            #logger.info("table condition after old group modification "+str(out))
            if(newActionProfileGroup != None) :
                logger.debug("Entering the port to new group in egress queue depth event handling")
                if ( (len(newActionProfileGroup.members)==1) and   (InternalConfig.EMPTY_GROUP_MEMBER_ID_FOR_EGRESS_QUEUE_DEPTH_BASED_ROUTING_TABLE == newActionProfileGroup.members[0].member_id) ):
                    newActionProfileGroup.add(actionProfileMemberObject.member_id)
                    newActionProfileGroup.del_member_from_group(member = self.emptyGroupHandlerMemberForEgressQueueDepthBasedRoutingTable)
                    newActionProfileGroup.modify()
                    #newActionProfileGroup._update_msg()
                    # logger.info("Printing values in new group : local_metadata.egr_queue_depth_value_range-- rangeField1LowerValue="+str(self.egressQueueDepthBasedRoutingInfo.getMetricsLevelRangeLowerValueMap(newActionProfileGroup.group_id))
                    #     +"rangefield1HigherValue ="+str(self.egressQueueDepthBasedRoutingInfo.getMetricsLevelRangeHigherValueMap(newActionProfileGroup.group_id))+
                    #     "rangeField2Name = local_metadata.minimum_group_members_requirement--rangeField2LowerValue=0, rangefield2HigherValue =0"
                    #     +" rangeField2ModifedLowerValue = 1, rangefield2ModifiedHigherValue = "+str(InternalConfig.DUMMY_MAX_MINIMUM_GROUP_MEMBERS_REQUIREMENT)
                    #     +" groupID = "+str(newActionProfileGroup.group_id)+ " priority="+str(self.egressQueueDepthBasedRoutingInfo.getTernaryTableEntryPriorityValueForTheGroup(newActionProfileGroup.group_id)))
                    self.p4dev.modifyLPMMatchEntryWithGroupActionWith2RangeField(tableName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_queue_depth_based_upstream_path_table",
                         fieldName = "hdr.ipv6.dst_addr", fieldValue= InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength = InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
                         rangeField1Name = "local_metadata.egr_queue_depth_value_range",
                         rangeField1LowerValue=self.egressQueueDepthBasedRoutingInfo.getMetricsLevelRangeLowerValueMap(newActionProfileGroup.group_id),
                         rangefield1HigherValue =self.egressQueueDepthBasedRoutingInfo.getMetricsLevelRangeHigherValueMap(newActionProfileGroup.group_id),
                         rangeField2Name = "local_metadata.minimum_group_members_requirement", rangeField2LowerValue=0, rangefield2HigherValue =0,
                         rangeField2ModifedLowerValue = 1, rangefield2ModifiedHigherValue = InternalConfig.DUMMY_MAX_MINIMUM_GROUP_MEMBERS_REQUIREMENT,
                         actionName= None, actionParamName=None, actionParamValue=None,
                         groupID = newActionProfileGroup.group_id, priority=self.egressQueueDepthBasedRoutingInfo.getTernaryTableEntryPriorityValueForTheGroup(newActionProfileGroup.group_id))
                else:
                    # out1 , err = self.p4dev.executeCommand("table_dump "+ "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_queue_depth_based_upstream_path_table"+"\n")
                    # logger.info(self.p4dev.devName+"There are more than one action profile members in this new group. .Before inserting"+str(out1))
                    newActionProfileGroup.add(actionProfileMemberObject.member_id)
                    newActionProfileGroup.modify()
                    # out1 , err = self.p4dev.executeCommand("table_dump "+ "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_queue_depth_based_upstream_path_table"+"\n")
                    # logger.info(self.p4dev.devName+"There are more than one action profile members in this new group. .After inserting"+str(out1))
                    #newActionProfileGroup._update_msg()
                self.egressQueueDepthBasedRoutingInfo.addPortNumToGroupMapping(port = egPort, actionProfileGroupObject=newActionProfileGroup)
                #out3 , err = self.p4dev.executeCommand("table_dump "+ "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_queue_depth_based_upstream_path_table"+"\n")
                #logger.info("table condition after completion"+str(out))
                # logger.info("Inside processEgressQueueDepthEvent of device "+str(self.p4dev.devName)+" for port "+str(egPort)+ "Pre: "+out1)
                # logger.info("Inside processEgressQueueDepthEvent of device "+str(self.p4dev.devName)+" for port "+str(egPort)+ "After Processing old grpup "+out2)
                # logger.info("Inside processEgressQueueDepthEvent of device "+str(self.p4dev.devName)+" for port "+str(egPort)+ "After Processing new grpup "+out3)
            else:
                logger.info("Failed to find new group for port member while processing egress wueue event. Severe Error. Exiting !!")
                exit(1)
        except Exception:
            logger.exception(str(self.p4dev.devName)+"Exception occured in egress queue depth evenet processing")
            logger.info("Inside processEgressQueueDepthEvent of device "+str(self.p4dev.devName)+" for port "+str(egPort)+ "Pre: "+out1)
            logger.info("Inside processEgressQueueDepthEvent of device "+str(self.p4dev.devName)+" for port "+str(egPort)+ "After Processing old grpup "+out2)
            logger.info("Inside processEgressQueueDepthEvent of device "+str(self.p4dev.devName)+" for port "+str(egPort)+ "After Processing new grpup "+out3)
            exit(1)





    def findActionPrfileGroupForEgressQueueDepthDecreaseEvent(self, currentGroup):
        newActionProfileGroup = None
        priorityOfNewActionProfileGroup = None
        if(currentGroup.group_id == InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4):
            #this means already in highest priority group. Further decrase in queue depth doesn;t change anything
            newActionProfileGroup = self.egressQueueDepthBasedRoutingInfo.getGroup(InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4)
            priorityOfNewActionProfileGroup = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4_PRIORITY
        elif(currentGroup.group_id == InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_3):
            #this means queue depth have decreased and we are going to move the port to a higher priotiy group. earlier it was 1_3 now it will be moved to 1_4
            newActionProfileGroup = self.egressQueueDepthBasedRoutingInfo.getGroup(InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4)
            priorityOfNewActionProfileGroup = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4_PRIORITY
        elif(currentGroup.group_id == InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_2):
            #this means queue depth have decreased and we are going to move the port to a higher priotiy group. earlier it was 1_3 now it will be moved to 1_4
            newActionProfileGroup = self.egressQueueDepthBasedRoutingInfo.getGroup(InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_3)
            priorityOfNewActionProfileGroup = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_3_PRIORITY
        elif(currentGroup.group_id == InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_1):
            #this means queue depth have decreased and we are going to move the port to a higher priotiy group. earlier it was 1_3 now it will be moved to 1_4
            newActionProfileGroup = self.egressQueueDepthBasedRoutingInfo.getGroup(InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_2)
            priorityOfNewActionProfileGroup = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_2_PRIORITY
        return newActionProfileGroup, priorityOfNewActionProfileGroup

    def findActionProfileGroupForEgressQueueDepthIncreaseEvent(self, currentGroup):
        newActionProfileGroup = None
        priorityOfNewActionProfileGroup = None
        if(currentGroup.group_id == InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4):
            #this means queue depth have increased and we are going to move the port to a lower priotiy group. earlier it was 1_4 now it will be moved to 1_3
            newActionProfileGroup = self.egressQueueDepthBasedRoutingInfo.getGroup(InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_3)
            priorityOfNewActionProfileGroup = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_3_PRIORITY
        elif(currentGroup.group_id == InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_3):
            #this means queue depth have decreased and we are going to move the port to a higher priotiy group. earlier it was 1_3 now it will be moved to 1_4
            newActionProfileGroup = self.egressQueueDepthBasedRoutingInfo.getGroup(InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_2)
            priorityOfNewActionProfileGroup = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_2_PRIORITY
        elif(currentGroup.group_id == InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_2):
            #this means queue depth have decreased and we are going to move the port to a higher priotiy group. earlier it was 1_3 now it will be moved to 1_4
            newActionProfileGroup = self.egressQueueDepthBasedRoutingInfo.getGroup(InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_1)
            priorityOfNewActionProfileGroup = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_1_PRIORITY
        elif(currentGroup.group_id == InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_1):
            #this means queue depth have decreased and we are going to move the port to a higher priotiy group. But as it is already in lowest prioty group we can not reduce the prioty further
            newActionProfileGroup = self.egressQueueDepthBasedRoutingInfo.getGroup(InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_1)
            priorityOfNewActionProfileGroup = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_1_PRIORITY
        return newActionProfileGroup, priorityOfNewActionProfileGroup



    def processEgressRateEvent(self, parsedPkt):
        # Only change between 3 colors. Grren, Yellow, Red. DP will only report , if the color is YELLOW or RED.

        egPort = parsedPkt.egress_rate_event_port
        oldActionProfileGroup = self.egressPortRateBasedRoutingInfo.getGroupByPortNumber(egPort)
        if(oldActionProfileGroup == None):
            #logger.info(self.p4dev.devName+"Egress Rate Event found for unnecessary port where no path diversity exists. So returning. port is "+str(egPort))
            return
        actionProfileMemberObject = self.egressPortRateBasedRoutingInfo.getMemberFromPortToActionProfileMemberMap(port=egPort)
        if actionProfileMemberObject == None:
            logger.info("Action Profile member object for port "+str(egPort)+" not exists in "+self.egressPortRateBasedRoutingInfo.name+". Severe Problem. Debug. Exiting")
            exit(1)

        #Find new group to which nnede tp attach
        newActionProfileGroup = None
        priorityOfNewActionProfileGroup = None
        if (parsedPkt.egress_rate_event_data == InternalConfig.EVENT_EGR_RATE_CHANGED) and (parsedPkt.egress_traffic_color == InternalConfig.GREEN ):
            #logger.info("EGRESS_RATE event found. Traffic color is : GREEN")
            newActionProfileGroupID, priorityOfNewActionProfileGroup = InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_GREEN, InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_GREEN_PRIORITY
            newActionProfileGroup = self.egressPortRateBasedRoutingInfo.getGroup(newActionProfileGroupID)
        elif (parsedPkt.egress_rate_event_data == InternalConfig.EVENT_EGR_RATE_CHANGED) and (parsedPkt.egress_traffic_color == InternalConfig.YELLOW ):
            #logger.info("EGRESS_RATE event found. Traffic color is : YELLOW")
            newActionProfileGroupID, priorityOfNewActionProfileGroup = InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_YELLOW, InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_YELLOW_PRIORITY
            newActionProfileGroup = self.egressPortRateBasedRoutingInfo.getGroup(newActionProfileGroupID)
        elif  (parsedPkt.egress_rate_event_data == InternalConfig.EVENT_EGR_RATE_CHANGED) and (parsedPkt.egress_traffic_color == InternalConfig.RED):
            #logger.info("EGRESS_RATE event found. Traffic color is : RED")
            newActionProfileGroupID, priorityOfNewActionProfileGroup = InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_RED, InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_RED_PRIORITY
            newActionProfileGroup = self.egressPortRateBasedRoutingInfo.getGroup(newActionProfileGroupID)
        else:
            #logger.info("Unhandled Egress rate Event: "+str(parsedPkt.egress_traffic_color))
            return
        if ( (len(oldActionProfileGroup.members)==1)) :
            if (InternalConfig.EMPTY_GROUP_MEMBER_ID_FOR_EGRESS_RATE_BASED_ROUTING_TABLE == oldActionProfileGroup.members[0].member_id):
                logger.debug("Ideally this should not happen. Debug and exiting")
                exit(1)
            else:
                #logger.info("Only one member is in group. But that is not the empty member handler group. Hence before deleting  this member we need to enter the empty member handler in this group ")
                oldActionProfileGroup.add(self.emptyGroupHandlerMemberForEgressRateBasedRoutingTable.member_id)
                oldActionProfileGroup.del_member_from_group(member = actionProfileMemberObject)


                self.p4dev.modifyLPMMatchEntryWithGroupActionWith2RangeField(tableName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_port_rate_based_upstream_path_table",
                     fieldName = "hdr.ipv6.dst_addr", fieldValue= InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength = InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
                     rangeField1Name = "local_metadata.egr_port_rate_value_range",
                     rangeField1LowerValue=self.egressPortRateBasedRoutingInfo.getMetricsLevelRangeLowerValueMap(oldActionProfileGroup.group_id),
                     rangefield1HigherValue =self.egressPortRateBasedRoutingInfo.getMetricsLevelRangeHigherValueMap(oldActionProfileGroup.group_id),
                     rangeField2Name = "local_metadata.minimum_group_members_requirement", rangeField2LowerValue=1, rangefield2HigherValue =InternalConfig.DUMMY_MAX_MINIMUM_GROUP_MEMBERS_REQUIREMENT,
                     rangeField2ModifedLowerValue = 0, rangefield2ModifiedHigherValue = 0,
                     actionName= None, actionParamName=None, actionParamValue=None,
                     groupID = oldActionProfileGroup.group_id, priority=self.egressPortRateBasedRoutingInfo.getTernaryTableEntryPriorityValueForTheGroup(oldActionProfileGroup.group_id))
                oldActionProfileGroup.modify()
                self.egressPortRateBasedRoutingInfo.deletePortNumToGroupMapping(egPort)
                #logger.info("Deleted port from old group in egress rate event handler")
        else:
            #logger.debug("There are more than one action profile members in this group. So required actrion profile member can be removed safely")
            oldActionProfileGroup.del_member_from_group(member = actionProfileMemberObject)
            oldActionProfileGroup.modify()
            self.egressPortRateBasedRoutingInfo.deletePortNumToGroupMapping(egPort)
            #logger.info("Deleted port from old group in egress rate event handler")
        #add to that oldActionProfileGroup
        if(newActionProfileGroup != None) :
            logger.debug("Entering the port to new group in egress rate  event handling")
            if ( (len(newActionProfileGroup.members)==1) and   (InternalConfig.EMPTY_GROUP_MEMBER_ID_FOR_EGRESS_RATE_BASED_ROUTING_TABLE == newActionProfileGroup.members[0].member_id) ):
                newActionProfileGroup.add(actionProfileMemberObject.member_id)
                newActionProfileGroup.modify()
                newActionProfileGroup.del_member_from_group(member = self.emptyGroupHandlerMemberForEgressRateBasedRoutingTable)
                newActionProfileGroup.modify()
                self.p4dev.modifyLPMMatchEntryWithGroupActionWith2RangeField(tableName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_port_rate_based_upstream_path_table",
                     fieldName = "hdr.ipv6.dst_addr", fieldValue= InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength = InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
                     rangeField1Name = "local_metadata.egr_port_rate_value_range",
                     rangeField1LowerValue=self.egressPortRateBasedRoutingInfo.getMetricsLevelRangeLowerValueMap(newActionProfileGroup.group_id),
                     rangefield1HigherValue =self.egressPortRateBasedRoutingInfo.getMetricsLevelRangeHigherValueMap(newActionProfileGroup.group_id),
                     rangeField2Name = "local_metadata.minimum_group_members_requirement", rangeField2LowerValue=0, rangefield2HigherValue =0,
                     rangeField2ModifedLowerValue = 1, rangefield2ModifiedHigherValue = InternalConfig.DUMMY_MAX_MINIMUM_GROUP_MEMBERS_REQUIREMENT,
                     actionName= None, actionParamName=None, actionParamValue=None,
                     groupID = newActionProfileGroup.group_id, priority=self.egressPortRateBasedRoutingInfo.getTernaryTableEntryPriorityValueForTheGroup(newActionProfileGroup.group_id))
            else:
                newActionProfileGroup.add(actionProfileMemberObject.member_id)
                newActionProfileGroup.modify()
            self.egressPortRateBasedRoutingInfo.addPortNumToGroupMapping(port = egPort, actionProfileGroupObject=newActionProfileGroup)
        else:
            logger.info("Failed to find new group for port member while processing egress rate event. Severe Error. Exiting !!")
            exit(1)


    def processIngressRateEvent(self,parsedPkt):
        inPort = parsedPkt.ingress_rate_event_port
        if(parsedPkt.ingress_traffic_color == InternalConfig.GREEN):
            logger.info("Ingress Rate Green. No op needed")
        elif(parsedPkt.ingress_traffic_color == InternalConfig.YELLOW):
            logger.info("Ingress Rate YELLOW. Op needed")
        elif(parsedPkt.ingress_traffic_color == InternalConfig.RED):
            logger.info("Ingress Rate RED.  Op needed")
        return

    #========================= Processing of path delay events=================
    def processPathDelayEvent(self, parsedPkt):
        # EVENT_PATH_DELAY_UNCHANGED = 0
        # EVENT_PATH_DELAY_INCREASED = 1   #These 3 events notifies if a packet has seen change in delay by threshold
        # EVENT_PATH_DELAY_DECREASED = 2

        port = parsedPkt.path_delay_event_port
        oldActionProfileGroup = self.delayBasedRoutingInfo.getGroupByPortNumber(port)
        if(oldActionProfileGroup == None):
            #logger.info("Path Delay Event found for unnecessary port ("+str(port)+") where no path diversity exists. So returning")
            return
        actionProfileMemberObject = self.delayBasedRoutingInfo.getMemberFromPortToActionProfileMemberMap(port=port)
        if actionProfileMemberObject == None:
            logger.info("Action Profile member object for port "+str(port)+" not exists in "+self.delayBasedRoutingInfo.name+". Severe Problem. Debug. Exiting")
            exit(1)

        #Find new group to which nnede tp attach
        newActionProfileGroup = None
        priorityOfNewActionProfileGroup = None
        if(parsedPkt.path_delay_event_type == InternalConfig.EVENT_PATH_DELAY_INCREASED):
            #logger.info("EVENT_PATH_DELAY_INCREASED event found")
            newActionProfileGroup, priorityOfNewActionProfileGroup = self.findActionPrfileGroupForPathDelayIncreaseEvent(currentGroup=oldActionProfileGroup)
        elif (parsedPkt.path_delay_event_type == InternalConfig.EVENT_PATH_DELAY_DECREASED):
            newActionProfileGroup, priorityOfNewActionProfileGroup =self.findActionPrfileGroupForPathDelayDecreaseEvent(currentGroup=oldActionProfileGroup)
            #logger.info("EVENT_PATH_DELAY_DECREASED event found")
        else:
            # logger.info("Unhandled Path delay change Event: "+str(parsedPkt.path_delay_event_type))
            return
        #add to that oldActionProfileGroup
        #logger.info("oldActionProfileGroup is "+str(oldActionProfileGroup.group_id)+" and newActionProfileGroup is "+str(newActionProfileGroup.group_id))
        #logger.info("oldActionProfileGroup members are "+str(oldActionProfileGroup.members) + " and newActionProfileGroup members are "+str(newActionProfileGroup.members))
        if ( (len(oldActionProfileGroup.members)==1)) :
            if (InternalConfig.EMPTY_GROUP_MEMBER_ID_FOR_DELAY_BASED_ROUTING_TABLE == oldActionProfileGroup.members[0].member_id):
                logger.debug("Ideally this should not happen. Debug and exiting")
                exit(1)
            else:
                #logger.info("Only one member is in group. But that is not the empty member handler group. Hence before deleting  this member we need to enter the empty member handler in this group ")
                oldActionProfileGroup.add(self.emptyGroupHandlerMemberForDelayBasedRoutingTable.member_id)
                oldActionProfileGroup.del_member_from_group(member = actionProfileMemberObject)
                oldActionProfileGroup.modify()
                self.delayBasedRoutingInfo.deletePortNumToGroupMapping(port)
                #logger.info("Deleted port from old group")
                self.p4dev.modifyLPMMatchEntryWithGroupActionWith2RangeField(tableName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.delay_based_upstream_path_table",
                     fieldName = "hdr.ipv6.dst_addr", fieldValue= InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength = InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
                     rangeField1Name = "local_metadata.delay_value_range",
                     rangeField1LowerValue=self.delayBasedRoutingInfo.getMetricsLevelRangeLowerValueMap(oldActionProfileGroup.group_id),
                     rangefield1HigherValue =self.delayBasedRoutingInfo.getMetricsLevelRangeHigherValueMap(oldActionProfileGroup.group_id),
                     rangeField2Name = "local_metadata.minimum_group_members_requirement", rangeField2LowerValue=1, rangefield2HigherValue =InternalConfig.DUMMY_MAX_MINIMUM_GROUP_MEMBERS_REQUIREMENT,
                     rangeField2ModifedLowerValue = 0, rangefield2ModifiedHigherValue = 0,
                     actionName= None, actionParamName=None, actionParamValue=None,
                     groupID = oldActionProfileGroup.group_id, priority=self.delayBasedRoutingInfo.getTernaryTableEntryPriorityValueForTheGroup(oldActionProfileGroup.group_id))
        else:
            #logger.debug("There are more than one action profile members in this group. So required actrion profile member can be removed safely")
            oldActionProfileGroup.del_member_from_group(member = actionProfileMemberObject)
            oldActionProfileGroup.modify()
            self.delayBasedRoutingInfo.deletePortNumToGroupMapping(port)
            #logger.info("Deleted port from old group")
        if(newActionProfileGroup != None) :
            logger.debug("Entering the port to new group in delay event handling")
            if ( (len(newActionProfileGroup.members)==1) and   (InternalConfig.EMPTY_GROUP_MEMBER_ID_FOR_DELAY_BASED_ROUTING_TABLE == newActionProfileGroup.members[0].member_id) ):
                newActionProfileGroup.add(actionProfileMemberObject.member_id)
                newActionProfileGroup.modify()
                newActionProfileGroup.del_member_from_group(member = self.emptyGroupHandlerMemberForDelayBasedRoutingTable)
                newActionProfileGroup.modify()
                self.p4dev.modifyLPMMatchEntryWithGroupActionWith2RangeField(tableName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.delay_based_upstream_path_table",
                     fieldName = "hdr.ipv6.dst_addr", fieldValue= InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength = InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
                     rangeField1Name = "local_metadata.delay_value_range",
                     rangeField1LowerValue=self.delayBasedRoutingInfo.getMetricsLevelRangeLowerValueMap(newActionProfileGroup.group_id),
                     rangefield1HigherValue =self.delayBasedRoutingInfo.getMetricsLevelRangeHigherValueMap(newActionProfileGroup.group_id),
                     rangeField2Name = "local_metadata.minimum_group_members_requirement", rangeField2LowerValue=0, rangefield2HigherValue =0,
                     rangeField2ModifedLowerValue = 1, rangefield2ModifiedHigherValue = InternalConfig.DUMMY_MAX_MINIMUM_GROUP_MEMBERS_REQUIREMENT,
                     actionName= None, actionParamName=None, actionParamValue=None,
                     groupID = newActionProfileGroup.group_id, priority=self.delayBasedRoutingInfo.getTernaryTableEntryPriorityValueForTheGroup(newActionProfileGroup.group_id))
            else:
                newActionProfileGroup.add(actionProfileMemberObject.member_id)
                newActionProfileGroup.modify()
            self.delayBasedRoutingInfo.addPortNumToGroupMapping(port = port, actionProfileGroupObject=newActionProfileGroup)
        else:
            logger.info("Failed to find new group for port member while processing path delay event. Severe Error. Exiting !!")
            exit(1)



    def findActionPrfileGroupForPathDelayDecreaseEvent(self, currentGroup):
        newActionProfileGroup = None
        priorityOfNewActionProfileGroup = None
        if(currentGroup.group_id == InternalConfig.DELAY_BASED_ROUTING_GROUP_1_4):
            #this means already in highest priority group. Further decrase in queue depth doesn;t change anything
            newActionProfileGroup = self.delayBasedRoutingInfo.getGroup(InternalConfig.DELAY_BASED_ROUTING_GROUP_1_4)
            priorityOfNewActionProfileGroup = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_4_PRIORITY
        elif(currentGroup.group_id == InternalConfig.DELAY_BASED_ROUTING_GROUP_1_3):
            #this means queue depth have decreased and we are going to move the port to a higher priotiy group. earlier it was 1_3 now it will be moved to 1_4
            newActionProfileGroup = self.delayBasedRoutingInfo.getGroup(InternalConfig.DELAY_BASED_ROUTING_GROUP_1_4)
            priorityOfNewActionProfileGroup = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_4_PRIORITY
        elif(currentGroup.group_id == InternalConfig.DELAY_BASED_ROUTING_GROUP_1_2):
            #this means queue depth have decreased and we are going to move the port to a higher priotiy group. earlier it was 1_3 now it will be moved to 1_4
            newActionProfileGroup = self.delayBasedRoutingInfo.getGroup(InternalConfig.DELAY_BASED_ROUTING_GROUP_1_3)
            priorityOfNewActionProfileGroup = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_3_PRIORITY
        elif(currentGroup.group_id == InternalConfig.DELAY_BASED_ROUTING_GROUP_1_1):
            #this means queue depth have decreased and we are going to move the port to a higher priotiy group. earlier it was 1_3 now it will be moved to 1_4
            newActionProfileGroup = self.delayBasedRoutingInfo.getGroup(InternalConfig.DELAY_BASED_ROUTING_GROUP_1_2)
            priorityOfNewActionProfileGroup = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_2_PRIORITY
        return newActionProfileGroup, priorityOfNewActionProfileGroup

    def findActionPrfileGroupForPathDelayIncreaseEvent(self, currentGroup):
        newActionProfileGroup = None
        priorityOfNewActionProfileGroup = None
        if(currentGroup.group_id == InternalConfig.DELAY_BASED_ROUTING_GROUP_1_4):
            #this means queue depth have increased and we are going to move the port to a lower priotiy group. earlier it was 1_4 now it will be moved to 1_3
            newActionProfileGroup = self.delayBasedRoutingInfo.getGroup(InternalConfig.DELAY_BASED_ROUTING_GROUP_1_3)
            priorityOfNewActionProfileGroup = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_3_PRIORITY
        elif(currentGroup.group_id == InternalConfig.DELAY_BASED_ROUTING_GROUP_1_3):
            #this means queue depth have decreased and we are going to move the port to a higher priotiy group. earlier it was 1_3 now it will be moved to 1_4
            newActionProfileGroup = self.delayBasedRoutingInfo.getGroup(InternalConfig.DELAY_BASED_ROUTING_GROUP_1_2)
            priorityOfNewActionProfileGroup = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_2_PRIORITY
        elif(currentGroup.group_id == InternalConfig.DELAY_BASED_ROUTING_GROUP_1_2):
            #this means queue depth have decreased and we are going to move the port to a higher priotiy group. earlier it was 1_3 now it will be moved to 1_4
            newActionProfileGroup = self.delayBasedRoutingInfo.getGroup(InternalConfig.DELAY_BASED_ROUTING_GROUP_1_1)
            priorityOfNewActionProfileGroup = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_1_PRIORITY
        elif(currentGroup.group_id == InternalConfig.DELAY_BASED_ROUTING_GROUP_1_1):
            #this means queue depth have decreased and we are going to move the port to a higher priotiy group. But as it is already in lowest prioty group we can not reduce the prioty further
            newActionProfileGroup = self.delayBasedRoutingInfo.getGroup(InternalConfig.DELAY_BASED_ROUTING_GROUP_1_1)
            priorityOfNewActionProfileGroup = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_1_PRIORITY
        return newActionProfileGroup, priorityOfNewActionProfileGroup

# ===========================================End path delay event procesing ============================
    def addGroupsForStepBasedRouting(self):
        print(self.p4dev.devName)
        # try:
        #     group4 = sh.ActionProfileGroup(self.p4dev,  "delay_based_upstream_path_selector")(group_id=InternalConfig.DELAY_BASED_ROUTING_GROUP_1_4)
        #     group3 = sh.ActionProfileGroup(self.p4dev,  "delay_based_upstream_path_selector")(group_id=InternalConfig.DELAY_BASED_ROUTING_GROUP_1_3)
        #     group2 = sh.ActionProfileGroup(self.p4dev,  "delay_based_upstream_path_selector")(group_id=InternalConfig.DELAY_BASED_ROUTING_GROUP_1_2)
        #     group1 = sh.ActionProfileGroup(self.p4dev,  "delay_based_upstream_path_selector")(group_id=InternalConfig.DELAY_BASED_ROUTING_GROUP_1_1)
        #
        #     group4.insert()
        #     self.delayBasedRoutingInfo.addGroup(InternalConfig.DELAY_BASED_ROUTING_GROUP_1_4, group4, metricsLevelRangeLowerValue= InternalConfig.COMMON_PRIORITY_LOWEST_VALUE,
        #         metricsRangeHigherValue=InternalConfig.DELAY_BASED_ROUTING_GROUP_1_4_PRIORITY, ternaryMatchPriority=InternalConfig.DELAY_BASED_ROUTING_GROUP_1_4_PRIORITY)
        #     group3.insert()
        #     self.delayBasedRoutingInfo.addGroup(InternalConfig.DELAY_BASED_ROUTING_GROUP_1_3, group3, metricsLevelRangeLowerValue= InternalConfig.COMMON_PRIORITY_LOWEST_VALUE,
        #         metricsRangeHigherValue=InternalConfig.DELAY_BASED_ROUTING_GROUP_1_3_PRIORITY, ternaryMatchPriority=InternalConfig.DELAY_BASED_ROUTING_GROUP_1_3_PRIORITY)
        #     group2.insert()
        #     self.delayBasedRoutingInfo.addGroup(InternalConfig.DELAY_BASED_ROUTING_GROUP_1_2, group2, metricsLevelRangeLowerValue= InternalConfig.COMMON_PRIORITY_LOWEST_VALUE,
        #         metricsRangeHigherValue=InternalConfig.DELAY_BASED_ROUTING_GROUP_1_2_PRIORITY, ternaryMatchPriority=InternalConfig.DELAY_BASED_ROUTING_GROUP_1_2_PRIORITY)
        #     group1.insert()
        #     self.delayBasedRoutingInfo.addGroup(InternalConfig.DELAY_BASED_ROUTING_GROUP_1_1, group1, metricsLevelRangeLowerValue= InternalConfig.COMMON_PRIORITY_LOWEST_VALUE,
        #         metricsRangeHigherValue=InternalConfig.DELAY_BASED_ROUTING_GROUP_1_1_PRIORITY, ternaryMatchPriority=InternalConfig.DELAY_BASED_ROUTING_GROUP_1_1_PRIORITY)
        # except Exception as e:
        #     logger.info("Exceptionm in creating routing groups for StepBased Routings (Delay). Exception is "+e)
        #     logger.info("Exiting")
        #     exit(1)


        try:
            group4 = sh.ActionProfileGroup(self.p4dev,  "egr_queue_depth_based_upstream_path_selector")(group_id=InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4)
            group3 = sh.ActionProfileGroup(self.p4dev,  "egr_queue_depth_based_upstream_path_selector")(group_id=InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_3)
            group2 = sh.ActionProfileGroup(self.p4dev,  "egr_queue_depth_based_upstream_path_selector")(group_id=InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_2)
            group1 = sh.ActionProfileGroup(self.p4dev,  "egr_queue_depth_based_upstream_path_selector")(group_id=InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_1)

            group4.insert()
            self.egressQueueDepthBasedRoutingInfo.addGroup(InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4, group4, metricsLevelRangeLowerValue= InternalConfig.COMMON_PRIORITY_LOWEST_VALUE,
                metricsRangeHigherValue=InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4_PRIORITY, ternaryMatchPriority=InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4_PRIORITY)
            group3.insert()
            self.egressQueueDepthBasedRoutingInfo.addGroup(InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_3, group3, metricsLevelRangeLowerValue= InternalConfig.COMMON_PRIORITY_LOWEST_VALUE,
                metricsRangeHigherValue=InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_3_PRIORITY, ternaryMatchPriority=InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_3_PRIORITY)
            group2.insert()
            self.egressQueueDepthBasedRoutingInfo.addGroup(InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_2, group2, metricsLevelRangeLowerValue= InternalConfig.COMMON_PRIORITY_LOWEST_VALUE,
                metricsRangeHigherValue=InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_2_PRIORITY, ternaryMatchPriority=InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_2_PRIORITY)
            group1.insert()
            self.egressQueueDepthBasedRoutingInfo.addGroup(InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_1, group1, metricsLevelRangeLowerValue= InternalConfig.COMMON_PRIORITY_LOWEST_VALUE,
                metricsRangeHigherValue=InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_1_PRIORITY, ternaryMatchPriority=InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_1_PRIORITY)

        except Exception as e:
            logger.info("Exceptionm in creating routing groups for StepBased Routings (Egress queue Depth). Exception is "+e)
            logger.info("Exiting")
            exit(1)

        try:
            group4 = sh.ActionProfileGroup(self.p4dev,  "egr_port_rate_based_upstream_path_selector")(group_id=InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_GREEN)
            group3 = sh.ActionProfileGroup(self.p4dev,  "egr_port_rate_based_upstream_path_selector")(group_id=InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_YELLOW)
            group2 = sh.ActionProfileGroup(self.p4dev,  "egr_port_rate_based_upstream_path_selector")(group_id=InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_RED)

            group4.insert()
            self.egressPortRateBasedRoutingInfo.addGroup(InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_GREEN, group4,
                    metricsLevelRangeLowerValue= InternalConfig.COMMON_PRIORITY_LOWEST_VALUE,
                   metricsRangeHigherValue=InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_GREEN_PRIORITY,
                   ternaryMatchPriority=InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_GREEN_PRIORITY)
            group3.insert()
            self.egressPortRateBasedRoutingInfo.addGroup(InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_YELLOW, group3,
                 metricsLevelRangeLowerValue= InternalConfig.COMMON_PRIORITY_LOWEST_VALUE,
                 metricsRangeHigherValue=InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_YELLOW_PRIORITY,
                 ternaryMatchPriority=InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_YELLOW_PRIORITY)
            group2.insert()
            self.egressPortRateBasedRoutingInfo.addGroup(InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_RED, group2,
              metricsLevelRangeLowerValue= InternalConfig.COMMON_PRIORITY_LOWEST_VALUE,
              metricsRangeHigherValue=InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_RED_PRIORITY,
              ternaryMatchPriority=InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_RED_PRIORITY)

        except Exception as e:
            logger.info("Exceptionm in creating routing groups for StepBased Routings (Egress queue Depth). Exception is "+e)
            logger.info("Exiting")
            exit(1)

        return

    def initializeUpstreamRouting(self):  # This function have to be atomic. # We have kept the leaf ans spine switch works in different block. though they are basically same. Because. in future we may want
    # implement seprate strategy for leaf spine and superSpine
        upwardPortList = []

        if (self.p4dev.fabric_device_config.switch_type == jp.SwitchType.LEAF ):
            # foreach port in upstream group add them to group with priority 4 and save them to some data astrcuture. so that it is easy to manage them in case of rearranging when running the algo
            upwardPortList = list(self.p4dev.portToSpineSwitchMap.keys())
            self.setupUpstreamRoutingGroups(upwardPortList= upwardPortList)
        elif (self.p4dev.fabric_device_config.switch_type == jp.SwitchType.SPINE ):
            upwardPortList =list(self.p4dev.portToSuperSpineSwitchMap.keys())
            self.setupUpstreamRoutingGroups(upwardPortList= upwardPortList)
        elif (self.p4dev.fabric_device_config.switch_type == jp.SwitchType.SUPER_SPINE ):
            logger.info("For super spine switches upstream routing is not supported yet")


    def setupUpstreamRoutingGroups(self, upwardPortList):
        '''
        This function setup highest priority groups for upward ports and then add empty group handler for ither groups
        :param upwardPortList:
        :return:
        '''
        for p in upwardPortList:
            # member = self.p4dev.createAndAddMemeberToActionProfileGroup( actionProfileGroupObject =self.delayBasedRoutingInfo.getGroup(id = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_4),
            #      selectorName = "delay_based_upstream_path_selector",
            #      memebrId = InternalConfig.DELAY_BASED_ROUTING_GROUP_MEMBER_ID_START+int(p),
            #      actionName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.delay_based_upstream_path_selector_action_with_param",
            #      actionParamName="port_num",actionParamValue = p)
            # self.delayBasedRoutingInfo.addPortNumToGroupMapping(port = p, actionProfileGroupObject=
            # self.delayBasedRoutingInfo.getGroup(id = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_4), prevMetricsValue=0)
            # self.delayBasedRoutingInfo.addPortToActionProfileMemberMap(p,member )
            member = self.p4dev.createAndAddMemeberToActionProfileGroup( actionProfileGroupObject =self.egressQueueDepthBasedRoutingInfo.getGroup(id = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4),
                         selectorName = "egr_queue_depth_based_upstream_path_selector",
                         memebrId = (InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_MEMBER_ID_START+int(p)),
                         actionName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_queue_depth_based_upstream_path_selector_action_with_param",
                         actionParamName="port_num",actionParamValue = p)
            self.egressQueueDepthBasedRoutingInfo.addPortNumToGroupMapping(port = p, actionProfileGroupObject=
            self.egressQueueDepthBasedRoutingInfo.getGroup(id = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4), prevMetricsValue=0)
            self.egressQueueDepthBasedRoutingInfo.addPortToActionProfileMemberMap(p,member )
            member = self.p4dev.createAndAddMemeberToActionProfileGroup( actionProfileGroupObject =self.egressPortRateBasedRoutingInfo.getGroup(id = InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_GREEN),
                 selectorName = "egr_port_rate_based_upstream_path_selector",
                 memebrId = (InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_MEMBER_ID_START+int(p)),
                 actionName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_port_rate_based_upstream_path_selector_action_with_param",
                 actionParamName="port_num",actionParamValue = p)
            self.egressPortRateBasedRoutingInfo.addPortNumToGroupMapping(port = p, actionProfileGroupObject=
                self.egressPortRateBasedRoutingInfo.getGroup(id = InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_GREEN), prevMetricsValue=0)
            self.egressPortRateBasedRoutingInfo.addPortToActionProfileMemberMap(p,member )

        if(len(upwardPortList) <=0):
            logger.info("There is no port in upward list of device "+self.p4dev.devName)
            logger.info("If you are working with layer 2 DCN then it is fuine. Otherwise There is something wrong fix it")
            return
        # self.p4dev.addLPMMatchEntryWithGroupActionWith2RangeField( tableName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.delay_based_upstream_path_table",
        #        fieldName = "hdr.ipv6.dst_addr", fieldValue= InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength = InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
        #        rangeField1Name = "local_metadata.delay_value_range", rangeField1LowerValue=1,rangefield1HigherValue =4,
        #         rangeField2Name = "local_metadata.minimum_group_members_requirement",
        #         rangeField2LowerValue=1,rangefield2HigherValue =InternalConfig.DUMMY_MAX_MINIMUM_GROUP_MEMBERS_REQUIREMENT,
        #        actionName= "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.delay_based_upstream_path_selector_action_with_param",
        #        actionParamName=None, actionParamValue=None,
        #        groupID = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_4, priority = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_4_PRIORITY)
        #=================================== for DELAY_BASED_ROUTING_GROUP_1_3
        # actionProfileGroupObject = self.delayBasedRoutingInfo.getGroup(id = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_3)
        # actionProfileGroupObject.add(self.emptyGroupHandlerMemberForDelayBasedRoutingTable.member_id)
        # actionProfileGroupObject.modify()
        # self.p4dev.addLPMMatchEntryWithGroupActionWith2RangeField( tableName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.delay_based_upstream_path_table",
        #            fieldName = "hdr.ipv6.dst_addr", fieldValue= InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength = InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH ,
        #            rangeField1Name = "local_metadata.delay_value_range", rangeField1LowerValue=1,rangefield1HigherValue =3,
        #            rangeField2Name = "local_metadata.minimum_group_members_requirement", rangeField2LowerValue=0,rangefield2HigherValue =0,
        #            actionName= "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.delay_based_upstream_path_selector_action_with_param",
        #            actionParamName=None, actionParamValue=None,
        #            groupID = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_3, priority = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_3_PRIORITY)
        #=================================== for DELAY_BASED_ROUTING_GROUP_1_2
        # actionProfileGroupObject = self.delayBasedRoutingInfo.getGroup(id = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_2)
        # actionProfileGroupObject.add(self.emptyGroupHandlerMemberForDelayBasedRoutingTable.member_id)
        # actionProfileGroupObject.modify()
        # self.p4dev.addLPMMatchEntryWithGroupActionWith2RangeField( tableName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.delay_based_upstream_path_table",
        #            fieldName = "hdr.ipv6.dst_addr", fieldValue= InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength = InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
        #            rangeField1Name = "local_metadata.delay_value_range", rangeField1LowerValue=1,rangefield1HigherValue =2,
        #            rangeField2Name = "local_metadata.minimum_group_members_requirement", rangeField2LowerValue=0,rangefield2HigherValue =0,
        #            actionName= "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.delay_based_upstream_path_selector_action_with_param",
        #            actionParamName=None, actionParamValue=None,
        #            groupID = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_2, priority = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_2_PRIORITY)
        #=================================== for DELAY_BASED_ROUTING_GROUP_1_1
        # actionProfileGroupObject = self.delayBasedRoutingInfo.getGroup(id = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_1)
        # actionProfileGroupObject.add(self.emptyGroupHandlerMemberForDelayBasedRoutingTable.member_id)
        # actionProfileGroupObject.modify()
        # self.p4dev.addLPMMatchEntryWithGroupActionWith2RangeField( tableName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.delay_based_upstream_path_table",
        #            fieldName = "hdr.ipv6.dst_addr", fieldValue= InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength = InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
        #            rangeField1Name = "local_metadata.delay_value_range", rangeField1LowerValue=1,rangefield1HigherValue =1,
        #            rangeField2Name = "local_metadata.minimum_group_members_requirement", rangeField2LowerValue=0,rangefield2HigherValue =0,
        #            actionName= "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.delay_based_upstream_path_selector_action_with_param",
        #            actionParamName=None, actionParamValue=None,
        #            groupID = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_1, priority = InternalConfig.DELAY_BASED_ROUTING_GROUP_1_1_PRIORITY)

        #**************************************************************************************************************************************
        #=================================== for EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4
        # actionProfileGroupObject = self.egressQueueDepthBasedRoutingInfo.getGroup(id = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4)
        # actionProfileGroupObject.add(self.emptyGroupHandlerMemberForEgressQueueDepthBasedRoutingTable.member_id)
        # actionProfileGroupObject.modify()
        self.p4dev.addLPMMatchEntryWithGroupActionWith2RangeField( tableName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_queue_depth_based_upstream_path_table",
               fieldName = "hdr.ipv6.dst_addr", fieldValue= InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength = InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
               rangeField1Name = "local_metadata.egr_queue_depth_value_range", rangeField1LowerValue=1,rangefield1HigherValue =4,
               rangeField2Name = "local_metadata.minimum_group_members_requirement", rangeField2LowerValue=1,rangefield2HigherValue =InternalConfig.DUMMY_MAX_MINIMUM_GROUP_MEMBERS_REQUIREMENT,
               actionName= None,
               actionParamName=None, actionParamValue=None,
               groupID = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4, priority = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4_PRIORITY)
        #=================================== for EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_3
        actionProfileGroupObject = self.egressQueueDepthBasedRoutingInfo.getGroup(id = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_3)
        actionProfileGroupObject.add(self.emptyGroupHandlerMemberForEgressQueueDepthBasedRoutingTable.member_id)
        actionProfileGroupObject.modify()
        self.p4dev.addLPMMatchEntryWithGroupActionWith2RangeField( tableName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_queue_depth_based_upstream_path_table",
               fieldName = "hdr.ipv6.dst_addr", fieldValue= InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength = InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
               rangeField1Name = "local_metadata.egr_queue_depth_value_range", rangeField1LowerValue=1,rangefield1HigherValue =3,
               rangeField2Name = "local_metadata.minimum_group_members_requirement", rangeField2LowerValue=0,rangefield2HigherValue =0,
               actionName= None,
               actionParamName=None, actionParamValue=None,
               groupID = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_3, priority = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_3_PRIORITY)

        #=================================== for EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_2
        actionProfileGroupObject = self.egressQueueDepthBasedRoutingInfo.getGroup(id = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_2)
        actionProfileGroupObject.add(self.emptyGroupHandlerMemberForEgressQueueDepthBasedRoutingTable.member_id)
        actionProfileGroupObject.modify()
        self.p4dev.addLPMMatchEntryWithGroupActionWith2RangeField( tableName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_queue_depth_based_upstream_path_table",
               fieldName = "hdr.ipv6.dst_addr", fieldValue= InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength = InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
               rangeField1Name = "local_metadata.egr_queue_depth_value_range", rangeField1LowerValue=1,rangefield1HigherValue =2,
               rangeField2Name = "local_metadata.minimum_group_members_requirement", rangeField2LowerValue=0,rangefield2HigherValue =0,
               actionName= None,
               actionParamName=None, actionParamValue=None,
               groupID = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_2, priority = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_2_PRIORITY)
        #=================================== for EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_1
        actionProfileGroupObject = self.egressQueueDepthBasedRoutingInfo.getGroup(id = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_1)
        actionProfileGroupObject.add(self.emptyGroupHandlerMemberForEgressQueueDepthBasedRoutingTable.member_id)
        actionProfileGroupObject.modify()
        self.p4dev.addLPMMatchEntryWithGroupActionWith2RangeField( tableName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_queue_depth_based_upstream_path_table",
               fieldName = "hdr.ipv6.dst_addr", fieldValue= InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength = InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
               rangeField1Name = "local_metadata.egr_queue_depth_value_range", rangeField1LowerValue=1,rangefield1HigherValue =1,
               rangeField2Name = "local_metadata.minimum_group_members_requirement", rangeField2LowerValue=0,rangefield2HigherValue =0,
               actionName= None,
               actionParamName=None, actionParamValue=None,
               groupID = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_1, priority = InternalConfig.EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_1_PRIORITY)


        #**************************************************************************************************************************************
        #=================================== for EGRESS_PORT_RATE_BASED_ROUTING_GROUP_GREEN
        self.p4dev.addLPMMatchEntryWithGroupActionWith2RangeField( tableName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_port_rate_based_upstream_path_table",
           fieldName = "hdr.ipv6.dst_addr", fieldValue= InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength = InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
           rangeField1Name = "local_metadata.egr_port_rate_value_range", rangeField1LowerValue=1,rangefield1HigherValue =3,
           rangeField2Name = "local_metadata.minimum_group_members_requirement", rangeField2LowerValue=1,rangefield2HigherValue =InternalConfig.DUMMY_MAX_MINIMUM_GROUP_MEMBERS_REQUIREMENT,
           actionName= None,
           actionParamName=None, actionParamValue=None,
           groupID = InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_GREEN, priority = InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_GREEN_PRIORITY)
        #=================================== for EGRESS_PORT_RATE_BASED_ROUTING_GROUP_YELLOW
        actionProfileGroupObject = self.egressPortRateBasedRoutingInfo.getGroup(id = InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_YELLOW)
        actionProfileGroupObject.add(self.emptyGroupHandlerMemberForEgressRateBasedRoutingTable.member_id)
        actionProfileGroupObject.modify()
        self.p4dev.addLPMMatchEntryWithGroupActionWith2RangeField( tableName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_port_rate_based_upstream_path_table",
           fieldName = "hdr.ipv6.dst_addr", fieldValue= InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength = InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
           rangeField1Name = "local_metadata.egr_port_rate_value_range", rangeField1LowerValue=1,rangefield1HigherValue =2,
           rangeField2Name = "local_metadata.minimum_group_members_requirement", rangeField2LowerValue=0,rangefield2HigherValue =0,
           actionName= None,
           actionParamName=None, actionParamValue=None,
           groupID = InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_YELLOW, priority = InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_YELLOW_PRIORITY)
        #=================================== for EGRESS_PORT_RATE_BASED_ROUTING_GROUP_RED
        actionProfileGroupObject = self.egressPortRateBasedRoutingInfo.getGroup(id = InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_RED)
        actionProfileGroupObject.add(self.emptyGroupHandlerMemberForEgressRateBasedRoutingTable.member_id)
        actionProfileGroupObject.modify()
        self.p4dev.addLPMMatchEntryWithGroupActionWith2RangeField( tableName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_routing_control_block.egr_port_rate_based_upstream_path_table",
           fieldName = "hdr.ipv6.dst_addr", fieldValue= InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength = InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
           rangeField1Name = "local_metadata.egr_port_rate_value_range", rangeField1LowerValue=1,rangefield1HigherValue =1,
           rangeField2Name = "local_metadata.minimum_group_members_requirement", rangeField2LowerValue=0,rangefield2HigherValue =0,
           actionName= None,
           actionParamName=None, actionParamValue=None,
           groupID = InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_RED, priority = InternalConfig.EGRESS_PORT_RATE_BASED_ROUTING_GROUP_RED_PRIORITY)

        return


# For a specific dstributed algo , there can be some initial route setup and some data structure. the algorithm interface will have facility for doing those things
# relevant data structures will be initialized from this onterface


# groupID to group map
# portID which in fact is an unique route ) to old metric map . example the DP reported value of delay for the port.
# If we implement this way, we do not need to modify the actioprofilegroup and we also can keep the metrics
# But when we remove




    def addDummyActionProfileMemberForHandlingEmptyRoutingGroup(self):
        #===============for delay based routing table
        # emptyGroupHandlerMemberForDelayBasedRoutingTable = sh.ActionProfileMember(self.p4dev, "delay_based_upstream_path_selector")(member_id= InternalConfig.EMPTY_GROUP_MEMBER_ID_FOR_DELAY_BASED_ROUTING_TABLE, action="delay_based_upstream_path_selector_action_without_param")
        # emptyGroupHandlerMemberForDelayBasedRoutingTable.insert()

        #===============for egress queue depth based routing table
        emptyGroupHandlerMemberForEgressQueueDepthBasedRoutingTable = sh.ActionProfileMember(self.p4dev, "egr_queue_depth_based_upstream_path_selector")(member_id= InternalConfig.EMPTY_GROUP_MEMBER_ID_FOR_EGRESS_QUEUE_DEPTH_BASED_ROUTING_TABLE, action="egr_queue_depth_based_upstream_path_selector_action_without_param")
        emptyGroupHandlerMemberForEgressQueueDepthBasedRoutingTable.insert()

        #===============for egress  rate based routing table
        emptyGroupHandlerMemberForEgressRateBasedRoutingTable = sh.ActionProfileMember(self.p4dev, "egr_port_rate_based_upstream_path_selector")(member_id= InternalConfig.EMPTY_GROUP_MEMBER_ID_FOR_EGRESS_RATE_BASED_ROUTING_TABLE, action="egr_port_rate_based_upstream_path_selector_action_without_param")
        emptyGroupHandlerMemberForEgressRateBasedRoutingTable.insert()

        return  emptyGroupHandlerMemberForEgressQueueDepthBasedRoutingTable, emptyGroupHandlerMemberForEgressRateBasedRoutingTable


    def setupPolicyRoutingTable(self):
        # These 2 are common for all rules
        policyRoutingTableName = "IngressPipeImpl.cp_assisted_multicriteria_upstream_policy_routing_control_block.policy_based_upstream_routing"
        matchFieldNameTuple = ["hdr.ipv6.traffic_class", "local_metadata.ingress_queue_event_hdr.ingress_queue_event",
                        "local_metadata.ingress_rate_event_hdr.ingress_traffic_color","local_metadata.ingress_queue_event_hdr.ingress_queue_event"]
        #Rule Format  --
        # matchFieldTupple = (Flow_type, ingress_rate_gradient, ingres_queue_depth_gradient)
        # actionName = this is variable depending on the matchField values
        # actionParamNameList = At this mment there are not action params so it will be []
        # actionParamValueList  = At this mment there are not action params so it will be []
        # self.p4dev.addExactMatchEntryWithMultipleFieldMultipleActionParam(tableName, fieldNameList, fieldValueList, actionName, actionParamNameList, actionParamValueList)

        # Rule 1
        #matchFieldValueTuple = [ConfConst.TRAFFIC_CLASS_LOW_DELAY, InternalConfig.GREEN, InternalConfig.EVENT_ING_QUEUE_INCREASED

        return
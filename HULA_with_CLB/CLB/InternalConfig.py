DCN_CORE_IPv6_PREFIX = "2001:1:1:1:0:0:0:0"
DCN_CORE_IPv6_PREFIX_LENGTH = 80
DCN_CORE_IPv6_PREFIX_TEST0 = "1:0:0:0:0:0:0:0"
DCN_CORE_IPv6_PREFIX_TEST1 = "0100:15:0:0:0:0:0:0"
DCN_CORE_IPv6_PREFIX_TEST2 = "0200:0:0:0:0:0:0:0"
CPU_PORT = 255

#***********************************************MultiCast Session Id start*******************************************************



#***********************************************Flow rule Priorities End**********************************************************

#***********************************************Flow rule Priorities Start*******************************************************
DEFAULT_PRIORITY = 100
#For Leaf switch

#For Spine Switch


#For SUper SPine Switch

#***********************************************Flow rule Priorities End**********************************************************


#***********************************************Routing Group param Start*******************************************************

# === For handling empty groups required member Id's are following ======================
EMPTY_GROUP_MEMBER_ID_FOR_DELAY_BASED_ROUTING_TABLE = 1
EMPTY_GROUP_MEMBER_ID_FOR_EGRESS_QUEUE_DEPTH_BASED_ROUTING_TABLE = 2
EMPTY_GROUP_MEMBER_ID_FOR_EGRESS_RATE_BASED_ROUTING_TABLE = 3
#Common group id's
COMMON_PRIORITY_LOWEST_VALUE =1

DELAY_BASED_ROUTING_GROUP_1_4 = 1004
DELAY_BASED_ROUTING_GROUP_1_3 = 1003
DELAY_BASED_ROUTING_GROUP_1_2 = 1002
DELAY_BASED_ROUTING_GROUP_1_1 = 1001
DELAY_BASED_ROUTING_GROUP_MEMBER_ID_START = 1000
DELAY_BASED_ROUTING_GROUP_1_4_PRIORITY = 4
DELAY_BASED_ROUTING_GROUP_1_3_PRIORITY = 3
DELAY_BASED_ROUTING_GROUP_1_2_PRIORITY = 2
DELAY_BASED_ROUTING_GROUP_1_1_PRIORITY = 1

INGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4 = 2004
INGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_3 = 2003
INGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_2 = 2002
INGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_1 = 2001
INGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_MEMBER_ID_START = 2000
INGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4_PRIORITY = 4
INGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_3_PRIORITY = 3
INGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_2_PRIORITY = 2
INGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_1_PRIORITY = 1

EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4 = 3004
EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_3 = 3003
EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_2 = 3002
EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_1 = 3001
EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_MEMBER_ID_START = 3000
EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_4_PRIORITY  = 4
EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_3_PRIORITY  = 3
EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_2_PRIORITY  = 2
EGRESS_QUEUE_DEPTH_BASED_ROUTING_GROUP_1_1_PRIORITY  = 1


EGRESS_PORT_RATE_BASED_ROUTING_GROUP_RED = 4003
EGRESS_PORT_RATE_BASED_ROUTING_GROUP_YELLOW = 4001
EGRESS_PORT_RATE_BASED_ROUTING_GROUP_GREEN = 4000
EGRESS_PORT_RATE_BASED_ROUTING_GROUP_MEMBER_ID_START = 4000
EGRESS_PORT_RATE_BASED_ROUTING_GROUP_RED_PRIORITY  = 1
EGRESS_PORT_RATE_BASED_ROUTING_GROUP_YELLOW_PRIORITY  = 2
EGRESS_PORT_RATE_BASED_ROUTING_GROUP_GREEN_PRIORITY  = 3

#For Leaf switch
LEAF_SWITCH_HOST_MULTICAST_GROUP = 10001 # this group contains all the host facing ports. This is used for multicasting ndp entries
LEAF_SWITCH_UPSTREAM_PORTS_GROUP = 10002 # this group contains all the spine switch facing ports. This is used for multicasting ndp entries

#For Spine Switch
SPINE_SWITCH_UPSTREAM_PORTS_GROUP = 10003 # this group contains all the spine switch facing ports. This is used for multicasting ndp entries

DUMMY_MAX_MINIMUM_GROUP_MEMBERS_REQUIREMENT = 999   # This is intentionally kept to high. as IT has not practical sigfinace of value. This is just a flag.
#For Super SPine Switch

#***********************************************Routing Group  param End**********************************************************


#***********************************************Evaluation related start*******************************************************

COUNTER_NAMES = {"egressPortCounter", "ingressPortCounter", "ctrlPktToCPCounter", "p2pFeedbackCounter"}
#For Leaf switch

#For Spine Switch


#For Super SPine Switch

#***********************************************Evaluation related start param End**********************************************************


#***********************************************P4 Config param Start*******************************************************
#common Section

#//=========================INVALID BIT: for everything -1 means invalid
INVALID = 15 #8s0xF;
GREEN = 0
YELLOW = 1
RED = 2

#//============================EVENT ORIGINATION_TYPE
EVENT_ORIGINATOR_LOCAL_SWITCH = 1  #Indicates the event is being reported by this switch itself
EVENT_ORIGINATOR_NEIGHBOUR_SWITCH = 2 #Indicates the event is being reported by a switch connected to switch who is reporting
EVENT_ORIGINATOR_DISTANT_SWITCH = 3 #Indicates the event is being reported by a switch neither the switch itself not a any switch who is  connected



#//=====================EVENT_TYPE------Constant to mean some event occured ..... They will be used to mark a packet
EVENT_PATH_DELAY_UNCHANGED = 0
EVENT_PATH_DELAY_INCREASED = 1   #These 3 events notifies if a packet has seen change in delay by threshold
EVENT_PATH_DELAY_DECREASED = 2



EVENT_ING_QUEUE_UNCHANGED = 10
EVENT_ING_QUEUE_INCREASED = 11  #These 3 events notifies if a packet has seen change in delay by threshold
EVENT_ING_QUEUE_DECREASED = 12


EVENT_EGR_QUEUE_UNCHANGED = 10
EVENT_EGR_QUEUE_INCREASED = 11  #These 3 events notifies if a packet has seen change in delay by threshold
EVENT_EGR_QUEUE_DECREASED = 12

EVENT_EGR_RATE_UNCHANGED = 20
EVENT_EGR_RATE_CHANGED = 21
#//======================== Static vlaues for our system-- We need to change them for our experimentations
PATH_DELAY_THRESHOLD = 1000   #//1 ms


INGRESS_QUEUE_DEPTH_THRESHOLD = 3
EGRESS_QUEUE_DEPTH_THRESHOLD = 3

#For Leaf switch

#For Spine Switch


#For Super SPine Switch

#***********************************************P4 Config param End**********************************************************





#***********************************************Template Config param Start*******************************************************

#Common section


#For Leaf switch

#For Spine Switch


#For Super SPine Switch

#***********************************************Template Config param End**********************************************************
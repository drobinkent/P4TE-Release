DCN_CORE_IPv6_PREFIX = "2001:1:1:1:0:0:0:0"
DCN_CORE_IPv6_PREFIX_LENGTH = 80
DCN_CORE_IPv6_PREFIX_TEST0 = "1:0:0:0:0:0:0:0"
DCN_CORE_IPv6_PREFIX_TEST1 = "0100:0:0:0:0:0:0:0"
DCN_CORE_IPv6_PREFIX_TEST2 = "0200:0:0:0:0:0:0:0"
CPU_PORT = 255

#***********************************************Flow rule Priorities Start*******************************************************
DEFAULT_PRIORITY = 100
#For Leaf switch

#For Spine Switch


#For SUper SPine Switch

#***********************************************Flow rule Priorities End**********************************************************


#***********************************************Routing Group param Start*******************************************************
#For Leaf switch
LEAF_SWITCH_HOST_MULTICAST_GROUP = 1 # this group contains all the host facing ports. This is used for multicasting ndp entries
LEAF_SWITCH_UPSTREAM_PORTS_GROUP = 2 # this group contains all the spine switch facing ports. This is used for multicasting ndp entries

#For Spine Switch
SPINE_SWITCH_UPSTREAM_PORTS_GROUP = 2 # this group contains all the spine switch facing ports. This is used for multicasting ndp entries


#For Super SPine Switch

#***********************************************Routing Group  param End**********************************************************


#***********************************************Evaluation related start*******************************************************

COUNTER_NAMES = {"egressPortCounter", "ingressPortCounter", "ctrlPktToCPCounter", "p2pFeedbackCounter"}
#For Leaf switch

#For Spine Switch


#For Super SPine Switch

#***********************************************Evaluation related start param End**********************************************************


#***********************************************Template Config param Start*******************************************************
#For Leaf switch

#For Spine Switch


#For Super SPine Switch

#***********************************************Template Config param End**********************************************************

#========= configure This field. This fields defines what are the maximum number of ports in the switch we are using
CLOS_MAX_PORT_NUMBER = 8
DCN_TYPE  = 2

#=============
SWITCH_TYPE_LEAF =        1
SWITCH_TYPE_SPINE =       2
SWITCH_TYPE_SUPER_SPINE = 3

SWITCH_TYPE_LEAF_AS_NAME =        "Leaf"
SWITCH_TYPE_SPINE_AS_NAME =       "Spine"
SWITCH_TYPE_SUPER_SPINE_AS_NAME = "SuperSpine"


PORT_NAME_PREFIX = "PORT"
LEAF_SWITCH_NAME_PREFIX = "l"
SPINE_SWITCH_NAME_PREFIX = "s"
SUPER_SPINE_SWITCH_NAME_PREFIX = "ss"
HOST_NAME_PREFIX = "h"
POD_NAME_PREFIX = "p"





#==================


LEAF_SWITCH_GRPC_PORT_START = 60000 # 50000+i
SPINE_SWITCH_GRPC_PORT_START = 61000 # 50500+i
SUPER_SPINE_SWITCH_GRPC_PORT_START = 62000 # 50500+i
CPU_PORT = 255 # we hope that we will never use 256 port of a device


LEAF_SWITCH_THRIFT_PORT_START = 48000 # 50000+i
SPINE_SWITCH_THRIFT_PORT_START = 52000 # 50500+i
SUPER_SPINE_SWITCH_THRIFT_PORT_START = 50000 # 50500+i



DRIVER_STRATUM_BMV2 = "bmv2"
PIPECONF_DCN_TE_LEAF="org.medianet.dcn-te-leaf"
PIPECONF_DCN_TE_SPINE="org.medianet.dcn-te-spine"
PIPECONF_DCN_TE_SUPER_SPINE="org.medianet.dcn-te-spine"

STRATUM_LEAF_PIPELINE = './p4src/build/leaf.json'
STRATUM_SPINE_PIPELINE = './p4src/build/spine.json'
STRATUM_SUPER_SPINE_PIPELINE = './p4src/build/spine.json'




LEAF_SWITCH_MAC_PREFIX =   "00:bb:00:00:" #next octet will formed from pod id and then next octet from leaf switch index in that pod
SPINE_SWITCH_MAC_PREFIX =  "00:cc:00:00:" #next octet will formed from pod id and then next octet from spine switch index in that pod
SUPER_SPINE_SWITCH_MAC_PREFIX =  "00:dd:00:00:00:" # Next octect is formed from super spine index
HOST_MAC_PREFIX = "00:00:aa:" #first of the next octect will be formed from pod id, then one octet from connected leaf switch index, then last octet from host index



DCN_CORE_IPv6_PREFIX = "2001:1:1:1:0:"
LEAF_IP_IDENTIFIER = "11"
SPINE_IP_IDENTIFIER = "22"
SUPER_SPINE_IP_IDENTIFIER = "33"



IP_PREFIX_128= "/128"
IP_PREFIX_112= "/112"
IP_PREFIX_96= "/96"
IP_PREFIX_80= "/80"
IP_PREFIX_64= "/64"
IP_PREFIX_48= "/48"
FLAT_IPV6_PREFIX = IP_PREFIX_80  #Whenever we want to change we will only change here

LEAF_SWITCH_SUBNET_PREFIX_LEN = IP_PREFIX_112



#=================== Basically We do not need to touch these fields. Because here we are just setting the link speed to maximum capacity of mininet.
#=================== If you need to configure the link capacity in your emulation then you can change them according to your requirement=================
# Each Time we need to change the oversubscription ration we neeed to recalculate it
# Assuming 4 port switch, 2 * 10 Mbps for host to leaf. 2*10 for leaf to spine. Each po have 2 spine switch, each spine connects to 2 super spine. therefor 4 connection. 4*5 = 20
HOST_TO_LEAF_BW_10Mbps = 100000   #We are intentionally setting them too high. Because we do not want any bottleneck through mininet  link. We have to create bottleneck link through queue rate
LEAF_TO_SPINE_BW_10Mbps = 100000
SPINE_TO_SUPER_SPINE_BW_10Mbps = 100000  #1000 is maximum for mininet


HOST_TO_LEAF_BW= HOST_TO_LEAF_BW_10Mbps
LEAF_TO_SPINE_BW = LEAF_TO_SPINE_BW_10Mbps
SPINE_TO_SUPER_SPINE_BW = SPINE_TO_SUPER_SPINE_BW_10Mbps



#=========================All configurations related to execute the test cases

HOST_COMMAND_FOLDER  = "./MininetSimulator/PER_HOST_COMMANDS/"
HOST_COMMAND_LOGS = "./MininetSimulator/TEST_LOG/"



TEST_START_DELAY= 60   #After starting the hosts. after 125 secsonds the client and host for simulatiing the traffic load will start


TCP_SERVER_COMAND_FILE = "/home/p4/P4TE/testAndMeasurement/TestConfigs/WebSearchWorkLoad_load_factor_0.8.serverdat"
TCP_CLIENT_COMAND_FILE = "/home/p4/P4TE/testAndMeasurement/TestConfigs/WebSearchWorkLoad_load_factor_0.8.clientdat"

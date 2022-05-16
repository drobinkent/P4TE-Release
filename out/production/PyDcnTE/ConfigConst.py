########Bootstrap config constants
from enum import Enum

LEAF_P4_INFO_FILE_PATH = "./p4src/Build/leaf_p4info.txt"
LEAF_BMV2_JSON_FILE_PATH = "./p4src/Build/leaf.json"

SPINE_P4_INFO_FILE_PATH = "./p4src/Build/spine_p4info.txt"
SPINE_BMV2_JSON_FILE_PATH = "./p4src/Build/spine.json"

SUPER_SPINE_P4_INFO_FILE_PATH = "./p4src/Build/spine_p4info.txt"
SUPER_SPINE_BMV2_JSON_FILE_PATH = "./p4src/Build/spine.json"

#This is the file, that contains the topology details. This file is generated from mininet simuator. After starting mininet simulator, this file is used by the
#controller and result processor
TOPOLOGY_CONFIG_FILE = "/home/deba/Desktop/PyDcnTE/MininetSimulator/Build/Internalnetcfg.json"

# This is the file where all controller logs wil be written
CONTROLLER_LOG_FILE_PATH = "./log/CONTROLLER.log"
#This is the path where all the counter values from devices will be written. Or we can directly show some data in live view of gnuplot
CONTROLLER_STATISTICS_RESULT_FILE_PATH = "./result/"
#This is the path where all logs while processing the results willl be written
RESULT_PROCESSOR_LOG_FILE_PATH = "./log/RESULT_PROCESSOR_LOG.log"

# Each Time we need to change the oversubscription ration we need to recalculate it
# Assuming 4 port switch, 2 * 10 Mbps for host to leaf. 2*10 for leaf to spine. Each po have 2 spine switch, each spine connects to 2 super spine. therefor 4 connection. 4*5 = 20
# Currently These are unused
HOST_TO_LEAF_BW_10Mbps = 10
LEAF_TO_SPINE_BW_10Mbps = 10
SPINE_TO_SUPER_SPINE_BW_10Mbps = 5


HOST_TO_LEAF_BW= HOST_TO_LEAF_BW_10Mbps
LEAF_TO_SPINE_BW = LEAF_TO_SPINE_BW_10Mbps
SPINE_TO_SUPER_SPINE_BW = SPINE_TO_SUPER_SPINE_BW_10Mbps



# these are required for changing the testing behavior
QUEUE_RATE_10 = 10
QUEUE_RATE_25 = 25
QUEUE_RATE_40 = 40
QUEUE_RATE_50 = 50
LEAF_SWITCH_QUEUE_RATE = QUEUE_RATE_10
SPINE_SWITCH_QUEUE_RATE = QUEUE_RATE_10
SUPER_SPINE_SWITCH_QUEUE_RATE = QUEUE_RATE_10


QUEUE_DEPTH_10 = 10
QUEUE_DEPTH_25 = 25
QUEUE_DEPTH_40 = 40
QUEUE_DEPTH_50 = 50
LEAF_SWITCH_QUEUE_DEPTH = QUEUE_DEPTH_10
SPINE_SWITCH_QUEUE_DEPTH = QUEUE_DEPTH_10
SUPER_SPINE_SWITCH_QUEUE_DEPTH = QUEUE_DEPTH_10


#------------Usually  buffer size should be Delay *  bandwidth . for bmv2 based testing this have to be represented and configured through Queue depth.
# ------ So we will multiply port bandwidth by a factor to estimate the Delay *  BW . So by this factor we are actually estimating the Delay factor.
QUEUE_RATE_TO_QUEUE_DEPTH_FACTOR = 5  # this means if for a port queu rate is x it's queue deth will be 5x
MAX_PORT_NUMBER = 256 # This field means each switch will have maximum 1024 ports. Corresponding value (MAX_PORTS_IN_SWITCH=1024) also needed to be set in P4 constant.p4 file

#=======this parameter is required for meters of each port. We have, setup queue rate for each ports. So the CIR will be queue_rate * CIR threshold factor and PIR will be queue rate
INGRESS_STATS_METER_CIR_THRESHOLD_FACTOR = 0.5  # This means each port will color packet yellow when it reaches 70% of the queu rate and red when. These are initial rate. In runtime we will set them dynamically
INGRESS_STATS_METER_CBURST_FACTOR = 0.1
INGRESS_STATS_METER_PIR_FACTOR = 0.90
INGRESS_STATS_METER_PBURST_FACTOR = 0.1


EGRESS_STATS_METER_CIR_THRESHOLD_FACTOR = 0.7  # This means each port will color packet yellow when it reaches 70% of the queu rate and red when
EGRESS_STATS_METER_CBURST_FACTOR = 0.1
EGRESS_STATS_METER_PIR_FACTOR = 0.90
EGRESS_STATS_METER_PBURST_FACTOR = 0.1


#======================thread control and timer related
STATISTICS_PULLING_INTERVAL = 1 # This meand after each .001 second controller will wake up the StatisticsPuller thread and collect stats from the switches
PORT_STATISTICS_HISTORY_LENGTH = 1000 # this means the history will be
#======================= Different Test Scenarios
class TestScenario(Enum):
    BASIC_ECMP = "ecmp"
    MEDIANET_DCN_TE = "medianet-dcn-te"



#============================= Security access
USER_NAME = "deba"
PASSWORD = "ppa05060"
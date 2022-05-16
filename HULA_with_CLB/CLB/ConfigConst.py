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
TOPOLOGY_CONFIG_FILE = "./MininetSimulator/Build/Internalnetcfg.json"
HOST_COMMAND_FOLDER = "./MininetSimulator/PER_HOST_COMMANDS/"

# This is the file where all controller logs wil be written
CONTROLLER_LOG_FILE_PATH = "./log/CONTROLLER.log"
STATISTICS_LOG_FILE_PATH = "./log/STATISTICS.log"
MAX_LOG_FILE_SIZE  =  52428800 #50 MB
MAX_LOG_FILE_BACKUP_COUNT = 250  # MAximum 25 files will be kept
IPERF_MAX_FLOW_RATE_FOR_SERVER = "48K"  #Iperf flow rate is made maximum to 64K. if we keep ubnlimited it swamps the buffer and experiemnts doesn't work really good
IPERF_DEFAULT_WINDOW_SIZE_FOR_SERVER = "1.4K"
IPERF_PACING_TIMER = 32
#This is the path where all the counter values from devices will be written. Or we can directly show some data in live view of gnuplot
LAMBDA = 25
CONTROLLER_STATISTICS_RESULT_FILE_PATH = "./result/"
#This is the path where all logs while processing the results willl be written
RESULT_PROCESSOR_LOG_FILE_PATH = "./log/RESULT_PROCESSOR_LOG.log"





#------------Usually  buffer size should be Delay *  bandwidth . for bmv2 based testing this have to be represented and configured through Queue depth.
# ------ So we will multiply port bandwidth by a factor to estimate the Delay *  BW . So by this factor we are actually estimating the Delay factor.
QUEUE_RATE_TO_QUEUE_DEPTH_FACTOR = .5 # this means if for a port queu rate is x it's queue deth will be 5x
MAX_PORT_NUMBER = 256 # This field means each switch will have maximum 1024 ports. Corresponding value (MAX_PORTS_IN_SWITCH=1024) also needed to be set in P4 constant.p4 file
MAX_PORT_NUMBER_PLUS_ONE = MAX_PORT_NUMBER+1  # This special number is used for creating multicast sessions

#=======this parameter is required for meters of each port. We have, setup queue rate for each ports. So the CIR will be queue_rate * CIR threshold factor and PIR will be queue rate
#===== This parameter is not used at this moment
INGRESS_STATS_METER_CIR_THRESHOLD_FACTOR = 0.6  # This means each port will color packet yellow when it reaches 70% of the queu rate and red when. These are initial rate. In runtime we will set them dynamically
INGRESS_STATS_METER_CBURST_FACTOR = 0.1
INGRESS_STATS_METER_PIR_FACTOR = 0.8
INGRESS_STATS_METER_PBURST_FACTOR = 0.2 #--- This 4 parameters are not used at this moment

#==== This is one of our major parameter and used
EGRESS_STATS_METER_CIR_THRESHOLD_FACTOR = 0.70  # This means each port will color packet yellow when it reaches 70% of the queu rate and red when
EGRESS_STATS_METER_CBURST_FACTOR = 0.1
EGRESS_STATS_METER_PIR_FACTOR = 0.9
EGRESS_STATS_METER_PBURST_FACTOR = 0.1

# === These 2 arrays defines, what portion of total upward traffic processing capcicyt is reserved for which class of trffic
#========= First array lists the accepted traffic classes, 2 nd array defines corresponding percentage to be configred in meter for ingress rate monitoring
# ==== at this moment we are setting equal percentage for all 3 types of switches. But may need to make 3 different types of percentage for different types of switches
# IPTOS_LOWDELAY     minimize delay        0x10
# IPTOS_THROUGHPUT   maximize throughput   0x08
# IPTOS_RELIABILITY  maximize reliability  0x04
# IPTOS_LOWCOST      minimize cost         0x02
TRAFFIC_CLASS_LOW_DELAY           = 0x04
TRAFFIC_CLASS_MAXIMIZE_THROUGHPUT = 0x02
TRAFFIC_CLASS_MAXIMIZE_PROFIT     = 0x08  # LOW cost .. if we want to present our low cost that means profit is maximized. but that will require dvisiion. so we are taking direct maximize profit
TRAFFIC_CLASS_AS_LIST = [TRAFFIC_CLASS_LOW_DELAY, TRAFFIC_CLASS_MAXIMIZE_THROUGHPUT , TRAFFIC_CLASS_MAXIMIZE_PROFIT]
#-- for only one category of flow if we prioritize rate for that we can get better perofrmance.
#here for large flow giving 70%- gives better peprformance compare to ECMP
#PERCENTAGE_OF_TOTAL_UPWARD_TRAFFIC_FOR_TRAFFIC_CLASS = [40, 70, 10]
PERCENTAGE_OF_TOTAL_UPWARD_TRAFFIC_FOR_TRAFFIC_CLASS = [10,40, 5] # How much of the link capacity should a traffic class get.
#======================thread control and timer related
STATISTICS_PULLING_INTERVAL = .75 # This meand after each 1 second controller will wake up the StatisticsPuller thread and collect stats from the switches
PORT_STATISTICS_HISTORY_LENGTH = 1000 # this means the history will be
#======================= Different Test Scenarios
class DataplnaeAlgorithm(Enum):
    DP_ALGO_BASIC_ECMP = "ecmp"
    DP_ALGO_BASIC_HULA = "hula"
    DP_ALGO_BASIC_CLB = "clb"

ALGORITHM_IN_USE = DataplnaeAlgorithm.DP_ALGO_BASIC_HULA #For CLB it will be always ECMP


queueRateForHostFacingPortsOfLeafSwitch = 40
queueRateForSpineFacingPortsOfLeafSwitch = 20
queueRateForLeafSwitchFacingPortsOfSpineSwitch= 20
queueRateForSuperSpineSwitchFacingPortsOfSpineSwitch=10
queueRateForSpineSwitchFacingPortsOfSuperSpineSwitch=10
queueRateForExternalInternetFacingPortsOfSuperSpineSwitch=100



# #============================= Security access==========================


#========================= Metrics Level Related configuration-- these are not uused at this moment=======================

#=============================Port to Port delay levels: each tuple are of format (low, hi, level,weight)================


PORT_TO_PORT_DELAY_LEVELS_LINEAR = [(0, 1000, 0, 0),(1001,5000,1,0), (5001, 75000,2,00)]
EGRESS_QUEUE_DEPTH_DELAY_LEVELS_LINEAR = [(0, 2, 0, 0),(3,5,1,0), (6, 10,2,00)]




#######################################################################################################################################################################################
#######################################################################################################################################################################################
#######################################################################################################################################################################################
############################################################  All CONFIGURATIONS RELATED TO RESULT PROCESSING  ########################################################################
#############################################################             Starts from Here               ##########################################################################
#######################################################################################################################################################################################
#######################################################################################################################################################################################
#######################################################################################################################################################################################

FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB = [ 50, 128,  256,1024]  # These means in our experiments we will consider 2 types of traffic . one with 50 KB size another 1 MB or 1024 KB
FLOW_TYPE_LOAD_RATIO = [ 10,5, 5, 80]  # This means 80% flows are short and 20# are large
FLOW_VOLUME_IDENTIFIER_VARIATION_LIMIT_IN_PERCENTAGE = 80 # this means any flow size within range of 15% defined in previous array will be categorized as flow of same type. 80 percent is configured to acoomdate both 10kb and 50 kb flow
PACKET_SIZE = 1024 # Each packet will be 1200 Byte size











#######################################################################################################################################################################################
#######################################################################################################################################################################################
#######################################################################################################################################################################################
############################################################  All CONFIGURATIONS RELATED TO TEST EXECUTION  ########################################################################
#############################################################             Starts from Here               ##########################################################################
#######################################################################################################################################################################################
#######################################################################################################################################################################################
#######################################################################################################################################################################################





IPERF3_SERVER_PORT_START = 42000
IPERF3_CLIENT_PORT_START = 32000
#We are forced to pass the absolute path because the Iperf tests are ctually run from mininet hosts. which do not understand
#the relative path. so please use the absolute path where you want to store your result
TEST_RESULT_FOLDER = "/home/p4/Desktop/CLB/testAndMeasurement/TEST_RESULTS"
TEST_RESULT_FOLDER_SERVER = "/server-logs"
TEST_RESULT_FOLDER_CLIENT = "/client-logs"
TEST_START_TIME_FILE_NAME ="/test_start_timer.txt"

MAX_PORT_COUNT = 4


SSH_USER_NAME = "YOUR user name"
SSH_PASSWORD = "Your pass word" # These access are not required. we are not using them
SSH_PORT = 22

LINUX_CC_ALGORITHM_DCTCP = "dctcp"
LINUX_CC_ALGORITHM_CUBIC = "cubic"



#=======================configurations for CLB
CPU_PORT = 255
CLB_TESTER_DEVICE_NAME = "p0l0" # As out target is only testing algorithm we will only run the CLB from one switch.
#This parameter defines that name. The algorithm will be only run with that device
LOAD_DISTRIBUTION_1 = [(5,2),(6,10),(7,1),(8,3)]
LOAD_DISTRIBUTION_2 = [(5,7),(6,1),(7,6),(8,2)]

DISTRO1_INSTALL_DELAY = 0   # Weight distribution 1 will be installed after 50 second of the controller thread starts
DISTRO2_INSTALL_DELAY = 110  # Weight distribution 2 will be installed after 50 second of the controller thread starts





#======================= Must match with the P4 program for CLB
MAX_PORTS_IN_SWITCH = 8; #Maximum Supported ports in a switch to reflect the dataplane configuration
MAX_TOR_SUBNET = 4;  #Maximum ToR supported by our simulation
BITMASK_LENGTH = 16
PRECISION_OF_LOAD_BALANCING = 8

STRIDE_COUNT = 8
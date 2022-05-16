//OUR assumptions here is that, no switch will cross
#ifndef GLOBAL_DP_CONSTANTS
#define GLOBAL_DP_CONSTANTS

//------------------------------------------------------------------------------
// PRE-PROCESSOR constants
// Can be defined at compile time.
//------------------------------------------------------------------------------

// CPU_PORT specifies the P4 port number associated to packet-in and packet-out.
// All packets forwarded via this port will be delivered to the controller as
// PacketIn messages. Similarly, PacketOut messages from the controller will be
// seen by the P4 pipeline as coming from the CPU_PORT.
#define CPU_PORT 255
//this is a special port to indicate this packet is meant for recurculation
#define PORT_ZERO 0

// CPU_CLONE_SESSION_ID specifies the mirroring session for packets to be cloned
// to the CPU port. Packets associated with this session ID will be cloned to
// the CPU_PORT as well as being transmitted via their egress port as set by the
// bridging/routing/acl table. For cloning to work, the P4Runtime controller
// needs first to insert a CloneSessionEntry that maps this session ID to the
// CPU_PORT.
#define CPU_CLONE_SESSION_ID 255



//------------------------------------------------------------------------------
// TYPEDEF DECLARATIONS
// To favor readability.
//------------------------------------------------------------------------------
typedef bit<9>   port_num_t;
typedef bit<48>  mac_addr_t;
typedef bit<16>  mcast_group_id_t;
typedef bit<32>  ipv4_addr_t;
typedef bit<128> ipv6_addr_t;
typedef bit<16>  l4_port_t;
typedef bit<48>  timestamp_t;

//------------------------------------------------------------------------------
// ==============================================CONSTANT VALUES
//------------------------------------------------------------------------------
const bit<16> ETHERTYPE_IPV6 = 0x86dd;
const bit<16> ETHERTYPE_IPV4 = 0x0800;
const bit<1> FLAG_1 = 1;
const bit<8> IP_PROTO_TCP = 6;
const bit<8> IP_PROTO_UDP = 17;
const bit<8> IP_PROTO_ICMPV6 = 58;
const bit<8> MDN_INT = 0xFD; //this is the header tag for mdn_int header
const bit<8> CONTROL_PACKET = 0xFE;  //this is the header for p2p feedback

const mac_addr_t IPV6_MCAST_01 = 0x33_33_00_00_00_01;

const bit<8> ICMP6_TYPE_NS = 135;
const bit<8> ICMP6_TYPE_NA = 136;
const bit<8> NDP_OPT_TARGET_LL_ADDR = 2;
const bit<32> NDP_FLAG_ROUTER = 0x80000000;
const bit<32> NDP_FLAG_SOLICITED = 0x40000000;
const bit<32> NDP_FLAG_OVERRIDE = 0x20000000;


//============= traffic class constants
const bit<6> TRAFFIC_CLASS_LOW_DELAY = 0x04; //0x10 becomes 0x04
const bit<6> TRAFFIC_CLASS_HIGH_THROUGHPUT= 0x02;  //in iperf3 0x08 turns into 0x02 bcz of last 2 bit is ecn

// These definitions are derived from the numerical values of the enum
// named "PktInstanceType" in the p4lang/behavioral-model source file
// targets/simple_switch/simple_switch.h

// https://github.com/p4lang/behavioral-model/blob/master/targets/simple_switch/simple_switch.h#L126-L134
//Source -p4-guide
const bit<32> BMV2_V1MODEL_INSTANCE_TYPE_NORMAL        = 0;
const bit<32> BMV2_V1MODEL_INSTANCE_TYPE_INGRESS_CLONE = 1;
const bit<32> BMV2_V1MODEL_INSTANCE_TYPE_EGRESS_CLONE  = 2;
const bit<32> BMV2_V1MODEL_INSTANCE_TYPE_COALESCED     = 3;
const bit<32> BMV2_V1MODEL_INSTANCE_TYPE_RECIRC        = 4;
const bit<32> BMV2_V1MODEL_INSTANCE_TYPE_REPLICATION   = 5;
const bit<32> BMV2_V1MODEL_INSTANCE_TYPE_RESUBMIT      = 6;

#define IS_NORMAL(std_meta) (std_meta.instance_type == BMV2_V1MODEL_INSTANCE_TYPE_NORMAL)
#define IS_RESUBMITTED(std_meta) (std_meta.instance_type == BMV2_V1MODEL_INSTANCE_TYPE_RESUBMIT)
#define IS_RECIRCULATED(std_meta) (std_meta.instance_type == BMV2_V1MODEL_INSTANCE_TYPE_RECIRC)
#define IS_RECIRCULATED(std_meta) (std_meta.instance_type == BMV2_V1MODEL_INSTANCE_TYPE_RECIRC)
#define IS_I2E_CLONE(std_meta) (std_meta.instance_type == BMV2_V1MODEL_INSTANCE_TYPE_INGRESS_CLONE)
#define IS_E2E_CLONE(std_meta) (std_meta.instance_type == BMV2_V1MODEL_INSTANCE_TYPE_EGRESS_CLONE)
#define IS_REPLICATED(std_meta) (std_meta.instance_type == BMV2_V1MODEL_INSTANCE_TYPE_REPLICATION)

const bit<32> I2E_CLONE_SESSION_ID = 5;
const bit<32> E2E_CLONE_SESSION_ID = 11;

//================================= Our own macros
#define IS_CONTROL_PKT_TO_NEIGHBOUR(local_metadata) (local_metadata.flag_hdr.is_control_pkt_from_delay_proc || (hdr.mdn_int.rate_control_event ==RATE_DECREASE_EVENT_NEED_TO_BE_APPLIED_IN_THIS_SWITCH) || (hdr.mdn_int.rate_control_event ==RATE_INCREASE_EVENT_NEED_TO_BE_APPLIED_IN_THIS_SWITCH) )
//#define IS_CONTROL_PKT_TO_NEIGHBOUR(local_metadata) (local_metadata.flag_hdr.is_control_pkt_from_delay_proc  )
#define IS_CONTROL_PKT_TO_CP(local_metadata) (local_metadata.flag_hdr.is_control_pkt_from_ing_queue_rate ||  local_metadata.flag_hdr.is_control_pkt_from_ing_queue_depth || local_metadata.flag_hdr.is_control_pkt_from_egr_queue_depth || local_metadata.flag_hdr.is_control_pkt_from_egr_queue_rate || local_metadata.flag_hdr.is_control_pkt_from_delay_proc)
#define IS_CONTROL_PKT_TO_CP_FOR_INGRESS_EVENTS(local_metadata) (local_metadata.flag_hdr.is_control_pkt_from_ing_queue_rate ||  local_metadata.flag_hdr.is_control_pkt_from_ing_queue_depth  )
#define IS_CONTROL_PKT_TO_CP_FOR_EGRESS_EVENTS(local_metadata) (local_metadata.flag_hdr.is_control_pkt_from_egr_queue_depth || local_metadata.flag_hdr.is_control_pkt_from_egr_queue_rate   )
#define IS_RECIRC_NEEDED(local_metadata) (local_metadata.flag_hdr.is_control_pkt_from_egr_queue_depth || local_metadata.flag_hdr.is_control_pkt_from_egr_queue_rate   )
//#define IS_CONTROL_PKT(local_metadata) (local_metadata.flag_hdr.is_control_pkt_from_delay_proc || local_metadata.flag_hdr.is_control_pkt_from_ing_queue_rate ||  local_metadata.flag_hdr.is_control_pkt_from_ing_queue_depth || local_metadata.flag_hdr.is_control_pkt_from_egr_queue_depth  )
//#define HAS_VALID_CONTROL_HDR(hdr) ( local_metadata.delay_info_hdr.isValid() ||  local_metadata.ingress_queue_event_hdr.isValid() || hdr.egress_queue_event_hdr.isValid() || local_metadata.ingress_rate_event_hdr.isValid() || local_metadata.egress_rate_event_hdr.isValid() )  // unused

//=========================INVALID BIT: for everything -1 means invalid
const bit<8> INVALID = 0xF;
const bit<8> GREEN = 0x0;
const bit<8> YELLOW = 0x1;
const bit<8> RED = 0x2;

//============================EVENT ORIGINATION_TYPE
const bit<8> EVENT_ORIGINATOR_LOCAL_SWITCH = 1;   //Indicates the event is being reported by this switch itself
const bit<8> EVENT_ORIGINATOR_NEIGHBOUR_SWITCH = 2; //Indicates the event is being reported by a switch connected to switch who is reporting
const bit<8> EVENT_ORIGINATOR_DISTANT_SWITCH = 3; //Indicates the event is being reported by a switch neither the switch itself not a any switch who is  connected



//=====================EVENT_TYPE------Constant to mean some event occured ..... They will be used to mark a packet
const bit<8> EVENT_PATH_DELAY_UNCHANGED = 0;
const bit<8> EVENT_PATH_DELAY_INCREASED = 1;   //These 3 events notifies if a packet has seen change in delay by threshold
const bit<8> EVENT_PATH_DELAY_DECREASED = 2;



const bit<8> EVENT_ING_QUEUE_UNCHANGED = 10;
const bit<8> EVENT_ING_QUEUE_INCREASED = 11;   //These 3 events notifies if a packet has seen change in delay by threshold
const bit<8> EVENT_ING_QUEUE_DECREASED = 12;


const bit<8> EVENT_EGR_QUEUE_UNCHANGED = 10;
const bit<8> EVENT_EGR_QUEUE_INCREASED = 11;   //These 3 events notifies if a packet has seen change in delay by threshold
const bit<8> EVENT_EGR_QUEUE_DECREASED = 12;

const bit<8> EVENT_EGR_RATE_UNCHANGED = 20;
const bit<8> EVENT_EGR_RATE_CHANGED = 21;

const bit<2> RATE_CONTROL_ALLOWED_FOR_THE_FLOW = 1;
const bit<2> RATE_CONTROL_NOT_ALLOWED_FOR_THE_FLOW = 0;

const bit<6> RATE_CONTROL_EVENT_NOT_YET_APPLIED = 0;
const bit<6> RATE_CONTROL_EVENT_ALREADY_APPLIED = 1;
const bit<6> RATE_DECREASE_EVENT_NEED_TO_BE_APPLIED_IN_THIS_SWITCH = 2;
const bit<6> RATE_INCREASE_EVENT_NEED_TO_BE_APPLIED_IN_THIS_SWITCH = 3;
const bit<6> RATE_CONTROL_EVENT_APPLIED_IN_OTHER_SWITCH = 4;  // this means thi spacket is a fake ACK and rate control event is applied from some other switch
//======================== Static vlaues for our system-- We need to change them for our experimentations
const bit<48> PATH_DELAY_THRESHOLD = 10000;   //15 ms


const bit<19> INGRESS_QUEUE_DEPTH_THRESHOLD = 2;
const bit<19> EGRESS_QUEUE_DEPTH_THRESHOLD = 4;


const bit<19> ECN_THRESHOLD_LEAF = 2;
const bit<19> ECN_THRESHOLD_SPINE = 1;
const bit<19> ECN_THRESHOLD = 2;
const bit<32> SEQ_NUMBER_THRESHOLD_FOR_RATE_CONTROL = 5000; // this means for each 10000 byte we will check for rate control. We may want to increase this

//======================================= Stateful data structures============================================================






//============================flowlet regrading constnts
const bit<48> FLOWLET_INTER_PACKET_GAP_THRESHOLD = 48w40000 ;  //40 packets per second rate means 1/40 second means 25000 microsecond
const bit<8> WINDOW_DECREASE_RATIO = 2;  // this is used when there is some congestion how mnay times ^ -1 a windows will be reduced. 2 means 2 times shift. or window size half.
const bit<8> WINDOW_INCREASE_RATIO = 8;




//===============================================CLB Related Constants
const bit<32> MAX_PORTS_IN_SWITCH = 8;
const bit<32> MAX_TOR_SUBNET = 4;  //Maximum ToR supported by our simulation
const bit<32> MAX_FLOW_TYPES = 64;  //traffic class 6 bits. so at most 64 types of flow can be there.
counter((bit<32>)MAX_PORTS_IN_SWITCH, CounterType.packets) egressPortCounter;
@name("load_counter")register<bit<32>>(MAX_TOR_SUBNET) load_counter;
@name("stored_bitmask")register<bit<BITMASK_LENGTH>>(MAX_TOR_SUBNET) stored_bitmask;
@name("level_to_link_store")register<bit<32>>(MAX_TOR_SUBNET*BITMASK_LENGTH) level_to_link_store;
const bit<32> ALL_ONE_BIT_MASK= 0b11111111111111111111111111111111;
counter((bit<32>)1, CounterType.packets) load_balancer_missed_counter;
@name("test_2d_array")register<bit<32>>(BITMASK_LENGTH*BITMASK_LENGTH) test_2d_array;

//register<bit<32>>(MAX_PORTS_IN_SWITCH*MAX_TOR_SUBNET) destination_util_counter;
counter((bit<32>)MAX_PORTS_IN_SWITCH*MAX_TOR_SUBNET, CounterType.bytes) destination_util_counter;

#endif


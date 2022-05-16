#include "CONSTANTS.p4"

#ifndef HEADERS
#define HEADERS


//------------------------------------------------------------------------------
// HEADER DEFINITIONS
//------------------------------------------------------------------------------
header ethernet_t {
    mac_addr_t  dst_addr;
    mac_addr_t  src_addr;
    bit<16>     ether_type;
}
header  mdn_int_t {
    bit<8>   next_hdr;
    bit<48>  src_enq_timestamp;
    bit<48>  src_deq_timestamp; // Thie may be also not needed. just for future reference
    //bit <8> has_ctrl_hdr;
    bit<2>  rate_control_allowed_for_the_tcp_flow;
    bit<6>  rate_control_event; // by default this will be 0. non zero value means 2 thing. a) at some point this flow have seen rate control b) las ttime when it have seen rate control.
    // only a single bit should be good enough for a single packet. Because if we do per packet rate control then single bit is enough. But if we want per flow rate control,
    //then we need to propagate the info that when a flow have last time seen rate control. Though it is not scalable, but still if someone wants to use that kind of thechnique
    // we have kept the option open.
    bit<32>  last_seq_no_with_rate_control;

}

header ipv6_t {
    bit<4>   version;
    bit<6>   traffic_class;
    bit<2>   ecn;
    bit<20>  flow_label;
    bit<16>  payload_len;
    bit<8>   next_hdr;
    bit<8>   hop_limit;
    bit<128> src_addr;
    bit<128> dst_addr;
}

header ipv4_t {
    bit<4>  version;
    bit<4>  ihl;
    bit<6>  dscp;
    bit<2>  ecn;
    bit<16> len;
    bit<16> identification;
    bit<3>  flags;
    bit<13> frag_offset;
    bit<8>  ttl;
    bit<8>  protocol;
    bit<16> hdr_checksum;
    bit<32> src_addr;
    bit<32> dst_addr;
}

header tcp_t {
    bit<16>  src_port;
    bit<16>  dst_port;
    bit<32>  seq_no;
    bit<32>  ack_no;
    bit<4>   data_offset;
    bit<3>   res;
    bit<3>   ecn;
    // bit control flags
    bit<1>   urg_control_flag;
    bit<1>   ack_control_flag;
    bit<1>   psh_control_flag;
    bit<1>   rst_control_flag;
    bit<1>   syn_control_flag;
    bit<1>   fin_control_flag;
    bit<16>  window;
    bit<16>  checksum;
    bit<16>  urgent_ptr;
}

header udp_t {
    bit<16> src_port;
    bit<16> dst_port;
    bit<16> len;
    bit<16> checksum;
}

header icmp_t {
    bit<8>   type;
    bit<8>   icmp_code;
    bit<16>  checksum;
    bit<16>  identifier;
    bit<16>  sequence_number;
    bit<64>  timestamp;
}

header icmpv6_t {
    bit<8>   type;
    bit<8>   code;
    bit<16>  checksum;
}

header ndp_t {
    bit<32>      flags;
    ipv6_addr_t  target_ipv6_addr;
    // NDP option.
    bit<8>       type;
    bit<8>       length;
    bit<48>      target_mac_addr;
}




//This header is for building conrtol packet
header delay_event_info_t{
    bit<8>      event_src_type;  //This field is for notifying whther an event is hop to hop or came from a hop more than 1 hop distance
    //Next fields are event data
    //bit<16>
    bit<8>      path_delay_event_type;
    bit<48>     path_delay_event_data;
    bit<128>    dst_addr;   //This is the address for which the switch has found increased or decreased delay
    bit<9>     path_delay_event_port;
    bit<7> padding;
}

header ingress_queue_event_info_t{
    bit<8> event_src_type;  //This field is for notifying whther an event is hop to hop or came from a hop more than 1 hop distance
    //Next fields are event data
    bit<8>     ingress_queue_event;
    bit<48>    ingress_queue_event_data;
    bit<9>     ingress_queue_event_port;
    bit<7> padding;
}
header egress_queue_event_info_t{
    bit<8> event_src_type;  //This field is for notifying whther an event is hop to hop or came from a hop more than 1 hop distance
    //Next fields are event data
    bit<8>     egress_queue_event;
    bit<48>    egress_queue_event_data;
    bit<9>     egress_queue_event_port;
    bit<7> padding;
}
header ingress_rate_event_info_t{
    bit<8> event_src_type;  //This field is for notifying whther an event is hop to hop or came from a hop more than 1 hop distance
    //Next fields are event data
    bit<32>    ingress_traffic_color;
    bit<48>    ingress_rate_event_data;
    bit<9>     ingress_rate_event_port;
    bit<7> padding;

}
header egress_rate_event_info_t{
    bit<8> event_src_type;  //This field is for notifying whther an event is hop to hop or came from a hop more than 1 hop distance
    //Next fields are event data
    bit<32>    egress_traffic_color;
    bit<48>    egress_rate_event_data;
    bit<9>     egress_rate_event_port;
    bit<7> padding;
}

struct test{
    bit<8> event_src_type;  //This field is for notifying whther an event is hop to hop or came from a hop more than 1 hop distance
    //Next fields are event data
    bit<32>    egress_traffic_color;
    bit<48>    egress_rate_event_data;

}
//this will be part of hdr. but this will only be used for carrying data betn stages. and just before deparsing it will made invalid. We are forced to do this, bcz, cloingn no saves metadata.
header flag_headers_t {

    bool       is_control_pkt_from_delay_proc;
    bool       is_control_pkt_from_ing_queue_rate;
    bool       is_control_pkt_from_ing_queue_depth;
    bool       is_control_pkt_from_egr_queue_depth;
    bool       is_control_pkt_from_egr_queue_rate;
    bool is_dp_only_multipath_algo_processing_required;
    bool is_fake_ack_for_rate_ctrl_required;
    bool do_l3_l2 ;
    bool my_station_table_hit ;
    bool downstream_routing_table_hit ;
    bool is_pkt_toward_host;
    bool found_egr_queue_depth_based_path;
    bool found_egr_queue_rate_based_path;
    bool found_path_delay_based_path;
    bool found_multi_criteria_paths;
    bool is_packet_from_downstream_port;
    bool is_packet_from_upstream_port;
    bit<7> padding;
}




//------------------------------------------------------------------------------
// USER-DEFINED METADATA
// User-defined data structures associated with each packet.
//------------------------------------------------------------------------------
struct local_metadata_t {
    l4_port_t  l4_src_port;
    l4_port_t  l4_dst_port;
    bool       is_multicast;

    bool is_pkt_rcvd_from_downstream;   //This signifies whether a packet was rcvd from upstream or downstream packet.
    delay_event_info_t delay_info_hdr;
    ingress_queue_event_info_t ingress_queue_event_hdr;
    egress_queue_event_info_t egress_queue_event_hdr;
    ingress_rate_event_info_t ingress_rate_event_hdr;
    egress_rate_event_info_t egress_rate_event_hdr;
    flag_headers_t flag_hdr;
    mdn_int_t     pkt_timestamp;
    bit<16> flowlet_map_index;
    bit<16> flowlet_id;
    bit<48> flow_inter_packet_gap;
    bit<48> flowlet_last_pkt_seen_time;
    bit<9> flowlet_last_used_path;


//    bit<10> range_val_test;
  //  bit<10> range_val_test_result;
    bit<10>  egr_port_rate_value_range ;
    bit<10>  egr_queue_depth_value_range ;
    bit<10>  delay_value_range;

    // TODO : at this moment all level requirements are 1. but in future we are planning for policy based routing on that case this will be required
    bit<10> minimum_group_members_requirement; //this is to handle the empty group problem. If there are 0 members in the high priority group then bmv2 yields. We can not allow that
    // As  a result in each group based routing table, we have to keep a flag whther the table is empty or not. this filed will so this task. we can keep it either a bool or int. we are just keeping
    // it as an int. because in future we have plan to extend this memebrship related things.
    //bit<4> path_ing_queue_level_requirement;
    //bit<4> path_egr_queue_level_requirement;

    // These are the placeholder where the egress ports will be kept after matching.
    //bit<9> delay_based_path;
    bit<9> egr_queue_based_path;
    bit<9> egr_rate_based_path;
    bit<32> temp; //This will be used for various tempporaty operation in various control blocks. But remeber we can not gues anything about it's initial data
    bit<8> temp_8_bit;
}


// *** INTRINSIC METADATA
//
// The v1model architecture also defines an intrinsic metadata structure, which
// fields are automatically populated by the target before feeding the
// packet to the parser. For convenience, we provide here its definition:
/*
struct standard_metadata_t {
    bit<9>  ingress_port;
    bit<9>  egress_spec; // Set by the ingress pipeline
    bit<9>  egress_port; // Read-only, available in the egress pipeline
    bit<32> instance_type;
    bit<32> packet_length;
    bit<48> ingress_global_timestamp;
    bit<48> egress_global_timestamp;
    bit<16> mcast_grp; // ID for the mcast replication table
    bit<1>  checksum_error; // 1 indicates that verify_checksum() method failed

    // Etc... See v1model.p4 for the complete definition.
}
*/


// Packet-in header. Prepended to packets sent to the CPU_PORT and used by the
// P4Runtime server (Stratum) to populate the PacketIn message metadata fields.
// Here we use it to carry the original ingress port where the packet was
// received.
@controller_header("packet_in")
header packet_in_t {
    port_num_t  ingress_port;
    bit<2>      _pad;

 //===
    bit<8>     ingress_queue_event;
    bit<48>    ingress_queue_event_data;
    bit<9>     ingress_queue_event_port;

    //===
    bit<8>     egress_queue_event;
    bit<48>    egress_queue_event_data;
    bit<9>     egress_queue_event_port;

    //===
    bit<32>    ingress_traffic_color;
    bit<48>    ingress_rate_event_data;
    bit<9>     ingress_rate_event_port;

    //===
    bit<32>    egress_traffic_color;
    bit<48>    egress_rate_event_data;
    bit<9>     egress_rate_event_port;

    bit<8> delay_event_src_type;  //This field is for notifying whther an event is hop to hop or came from a hop more than 1 hop distance
        //Next fields are event data
        //bit<16>
    bit<8>    path_delay_event_type;
    bit<48>     path_delay_event_data;
    bit<128> dst_addr;   //This is the address for which the switch has found increased or decreased delay
    bit<9>     path_delay_event_port;

}


header dp_to_cp_feedback_hdr_t {

    //===
    bit<8>     ingress_queue_event;
    bit<48>    ingress_queue_event_data;

    //===
    bit<8>     egress_queue_event;
    bit<48>    egress_queue_event_data;


    //===
    bit<32>    ingress_traffic_color;
    bit<48>    ingress_rate_event_data;

    //===
    bit<32>    egress_traffic_color;
    bit<48>    egress_rate_event_data;

}

// Packet-out header. Prepended to packets received from the CPU_PORT. Fields of
// this header are populated by the P4Runtime server based on the P4Runtime
// PacketOut metadata fields. Here we use it to inform the P4 pipeline on which
// port this packet-out should be transmitted.
@controller_header("packet_out")
header packet_out_t {
    port_num_t  egress_port;
    bit<7>      _pad;
}

// Header for sensing peer to peer feedback

header p2p_feedback_t {
   port_num_t port_id;  //9 bits
   bit <8> delay_event_type;
   bit <48> delay_event_data;
   bit<8> next_hdr;
   bit<7> padding;
}

// We collect all headers under the same data structure, associated with each
// packet. The goal of the parser is to populate the fields of this struct.
struct parsed_headers_t {
    packet_out_t  packet_out;
    packet_in_t   packet_in;
    //dp_to_cp_feedback_hdr_t dp_to_cp_feedback_hdr;
    ethernet_t    ethernet;
    ipv4_t        ipv4;
    ipv6_t        ipv6;
    mdn_int_t     mdn_int;   //this is for peer to peer info passing for a packet
    p2p_feedback_t p2p_feedback;
    tcp_t         tcp;
    udp_t         udp;
    icmpv6_t      icmpv6;
    ndp_t         ndp;
    //=================
    //delay_event_info_t delay_event_feedback;

    //=====
}

#endif
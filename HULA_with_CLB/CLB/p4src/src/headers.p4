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
    bool is_load_balancer_processing_required;
    bit<6> padding;
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

    flag_headers_t flag_hdr;
    bit<16> flowlet_map_index;
    bit<16> flowlet_id;
    bit<48> flow_inter_packet_gap;
    bit<48> flowlet_last_pkt_seen_time;
    bit<9> flowlet_last_used_path;
    bit<32> tor_id;




    //bit<32> temp; //This will be used for various tempporaty operation in various control blocks. But remeber we can not gues anything about it's initial data
   // bit<8> temp_8_bit;
    bit<BITMASK_POSITION_INDICATOR_BITS_LENGTH> packet_bitmask_shift_times;
    bit<BITMASK_LENGTH> packet_bitmask;
    bit<32> link_location_index; //in this location of final stateful memory block, the link will be found
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
    bit<7>      _pad;

 //===


}



// Packet-out header. Prepended to packets received from the CPU_PORT. Fields of
// this header are populated by the P4Runtime server based on the P4Runtime
// PacketOut metadata fields. Here we use it to inform the P4 pipeline on which
// port this packet-out should be transmitted.
@controller_header("packet_out")
header packet_out_t {
    port_num_t  egress_port;
    bit<7>      _pad;
    //Previous all fields are not necessary for CLB. TODO  at sometime we will trey to clean up them. But at this moment we are not focusing on that
    bit<8> clb_flags; //Here we will keep various falgs for CLB
    //--------bit-7--------|| If this bit is set then reet the counter
    //--------bit-6--------|| If this bit is set then this is a port delete packet
    //--------bit-5--------|| If this bit is set then this is a port insert packet
    //--------bit-4--------|| Other bits are ununsed at this moment
    //--------bit-3--------||
    //--------bit-2--------||
    //--------bit-1--------||
    //--------bit-0--------||


    bit<32> link_id;
    bit<32> bitmask; //Here we are keeping all 32 bit to avoid compile time configuration complexity. At apply blo0ck we will slice necesssary bits.
    bit<32> level_to_link_id_store_index;  //
    bit<32> tor_id;  //
}

// Header for sensing peer to peer feedback


// We collect all headers under the same data structure, associated with each
// packet. The goal of the parser is to populate the fields of this struct.
struct parsed_headers_t {
    packet_out_t  packet_out;
    packet_in_t   packet_in;
    //dp_to_cp_feedback_hdr_t dp_to_cp_feedback_hdr;
    ethernet_t    ethernet;
    ipv4_t        ipv4;
    ipv6_t        ipv6;
    tcp_t         tcp;
    udp_t         udp;
    icmpv6_t      icmpv6;
    ndp_t         ndp;
    //=================
    //delay_event_info_t delay_event_feedback;

    //=====
}

#endif
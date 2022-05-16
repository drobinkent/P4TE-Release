/*
 * Copyright 2019-present Open Networking Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// Any P4 program usually starts by including the P4 core library and the
// architecture definition, v1model in this case.
// https://github.com/p4lang/p4c/blob/master/p4include/core.p4
// https://github.com/p4lang/p4c/blob/master/p4include/v1model.p4
#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"
#include "debug.p4"
#include "egress_queue_depth_monitor.p4"
#include "ingress_rate_monitor.p4"
#include "egress_rate_monitor.p4"
#include "rate_control.p4"
#include "int_delay_processor.p4"
#include "upstream_routing.p4"
#include "ndp.p4"
#include "l2_ternary.p4"
#include "my_station.p4"
#include "l2_ternary.p4"
#include "leaf_downstream_routing.p4"
#include "cp_assisted_multicriteria_upstream_routing_tables.p4"
#include "cp_assisted_multicriteria_upstream_policy_routing.p4"
#include "metrics_level_calculator.p4"
control VerifyChecksumImpl(inout parsed_headers_t hdr,
                           inout local_metadata_t meta)
{
    // Not used here. We assume all packets have valid checksum, if not, we let
    // the end hosts detect errors.
    apply { /* EMPTY */ }
}


control IngressPipeImpl (inout parsed_headers_t    hdr,
                         inout local_metadata_t    local_metadata,
                         inout standard_metadata_t standard_metadata) {
     //======================= All ingress data structures

    //================================This section will contain all isolated actions=======================================

    action init_pkt(){
        local_metadata.delay_info_hdr.setValid();
        local_metadata.delay_info_hdr.event_src_type = INVALID;  //This field is for notifying whther an event is hop to hop or came from a hop more than 1 hop distance
        //Next fields are event data
        //bit<16>
        local_metadata.delay_info_hdr.path_delay_event_type = EVENT_PATH_DELAY_UNCHANGED;
        local_metadata.delay_info_hdr.path_delay_event_data=(bit<48>)INVALID;
        local_metadata.ingress_queue_event_hdr.setValid();
        local_metadata.ingress_queue_event_hdr.event_src_type= INVALID;  //This field is for notifying whther an event is hop to hop or came from a hop more than 1 hop distance
        //Next fields are event data
        local_metadata.ingress_queue_event_hdr.ingress_queue_event= INVALID;
        local_metadata.ingress_queue_event_hdr.ingress_queue_event_data = (bit<48>)INVALID;
        local_metadata.egress_queue_event_hdr.setValid();
        local_metadata.egress_queue_event_hdr.event_src_type = INVALID;   //This field is for notifying whther an event is hop to hop or came from a hop more than 1 hop distance
        //Next fields are event data
        local_metadata.egress_queue_event_hdr.egress_queue_event= INVALID;
        local_metadata.egress_queue_event_hdr.egress_queue_event_data = (bit<48>)INVALID;

        local_metadata.ingress_rate_event_hdr.setValid();
        local_metadata.ingress_rate_event_hdr.event_src_type = INVALID;    //This field is for notifying whther an event is hop to hop or came from a hop more than 1 hop distance
        //Next fields are event data
        local_metadata.ingress_rate_event_hdr.ingress_traffic_color = (bit<32>)GREEN;
        local_metadata.ingress_rate_event_hdr.ingress_rate_event_data = (bit<48>)EVENT_EGR_RATE_UNCHANGED;
        local_metadata.egress_rate_event_hdr.setValid();
        local_metadata.egress_rate_event_hdr.event_src_type = INVALID;   //This field is for notifying whther an event is hop to hop or came from a hop more than 1 hop distance
        //Next fields are event data
        local_metadata.egress_rate_event_hdr.egress_traffic_color = (bit<32>)GREEN;
        local_metadata.egress_rate_event_hdr.egress_rate_event_data = (bit<48>)INVALID;
        local_metadata.flag_hdr.setValid();
        local_metadata.pkt_timestamp.setValid();
        local_metadata.pkt_timestamp.src_enq_timestamp = standard_metadata.ingress_global_timestamp;
        local_metadata.pkt_timestamp.src_deq_timestamp = standard_metadata.ingress_global_timestamp;
        //========== Flag headers initialization part
        local_metadata.flag_hdr.do_l3_l2 = true;
        local_metadata.flag_hdr.is_control_pkt_from_delay_proc = false;  //Initially this packet is not generating a control packet. But later if this field is true, that means a
        //relevant control packet is needed to be sent to Controll plane or other switch.
        local_metadata.flag_hdr.is_control_pkt_from_ing_queue_rate = false;
        local_metadata.flag_hdr.is_control_pkt_from_ing_queue_depth = false;
        local_metadata.flag_hdr.is_control_pkt_from_egr_queue_depth = false;
        local_metadata.flag_hdr.is_control_pkt_from_egr_queue_rate = false;

        ingressPortCounter.count((bit<32>)standard_metadata.ingress_port);

        local_metadata.flag_hdr.downstream_routing_table_hit = false;
        local_metadata.flag_hdr.is_dp_only_multipath_algo_processing_required = false;
        local_metadata.flag_hdr.is_fake_ack_for_rate_ctrl_required = false;

        local_metadata.minimum_group_members_requirement=1;  //We want to select path from a routing group with non zero memebers. Because a ny group with zero memebers yields the switch processing pipeline
        local_metadata.delay_value_range = 1;
        local_metadata.egr_queue_depth_value_range  = 1;
        local_metadata.egr_port_rate_value_range  = 1;

        // We will not set these 2 values in spine switches, bcz they will be intitiated from the leaf switches.
        hdr.mdn_int.rate_control_allowed_for_the_tcp_flow = RATE_CONTROL_NOT_ALLOWED_FOR_THE_FLOW; // At start rate control is not allowed. we will not set this field in spine packet initialization part
        hdr.mdn_int.rate_control_event = RATE_CONTROL_EVENT_NOT_YET_APPLIED ; // Means no rate contrl happned yet
    }
    // Drop action definition, shared by many tables. Hence we define it on top.
   action drop() {
       // Sets an architecture-specific metadata field to signal that the
       // packet should be dropped at the end of this pipeline.
       mark_to_drop(standard_metadata);
   }
    //===Instantiation of control blocks from other p4 files

    #ifdef ENABLE_DEBUG_TABLES
    debug_std_meta() debug_std_meta_ingress_start;
    debug_std_meta() ingress_end_debug;
    #endif  // ENABLE_DEBUG_TABLES

    int_delay_processor() ingress_delay_processor_control_block;
    ingress_rate_monitor() ingress_rate_monitor_control_block;
    leaf_downstream_routing () downstream_routing_control_clock;
    l2_ternary_processing() l2_ternary_processing_control_block;
    my_station_processing() my_station_processing_control_block;
    ndp_processing() ndp_processing_control_block;

    //#ifdef DP_ALGO_ECMP
    //upstream_routing() upstream_ecmp_routing_control_block;
    //#endif
    upstream_routing() upstream_ecmp_routing_control_block;
    cp_assisted_multicriteria_upstream_routing_tables() cp_assisted_multicriteria_upstream_routing_control_block;
    cp_assisted_multicriteria_upstream_policy_routing() cp_assisted_multicriteria_upstream_policy_routing_control_block;

    //metrics level calculator tables
    // *** APPLY BLOCK STATEMENT



    apply {

    if(hdr.p2p_feedback.isValid()){

         //if the p2p feedback is valid that means there is a a valid delay feedback from the neighbour switch. so forward it to CP
       standard_metadata.egress_spec = CPU_PORT;
       local_metadata.flag_hdr.do_l3_l2 = false; //thie means . this packet doesn;t need normal forwarding processing. It wil only be used for updating the internal routing related information
       exit;

    }else if (hdr.packet_out.isValid()) {
       // Set the egress port to that found in the packet-out metadata...
       standard_metadata.egress_spec = hdr.packet_out.egress_port;
       // Remove the packet-out header...
       hdr.packet_out.setInvalid();
       // Exit the pipeline here, no need to go through other tables.
       exit;
    }else if (hdr.packet_in.isValid() && IS_RECIRCULATED(standard_metadata)) {  //This means this packet is replicated from egress to setup
        //log_msg("Found a recirculated packet");
        local_metadata.flag_hdr.do_l3_l2 = false; //thie means . this packet doesn;t need normal forwarding processing. It wil only be used for updating the internal routing related information
        egress_queue_rate_value_map.write((bit<32>)hdr.packet_in.path_delay_event_port, (bit<48>)local_metadata.egress_rate_event_hdr.egress_traffic_color );
        egress_queue_rate_last_update_time_map.write((bit<32>)hdr.packet_in.path_delay_event_port, standard_metadata.ingress_global_timestamp);
        mark_to_drop(standard_metadata);
   }else{ //This means these packets are normal packets and they will generate the events
        init_pkt();
        //ingress_delay_processor_control_block.apply(hdr, local_metadata, standard_metadata);
        ingress_rate_monitor_control_block.apply(hdr, local_metadata, standard_metadata);  //TODO we need to make this hash and meter based to adapt with per flow or some policy based admission control
    }


    // If this is a packet-out from the controller... we may not need this at this moment


    if ((hdr.icmpv6.type == ICMP6_TYPE_NS ) && (hdr.icmpv6.type == ICMP6_TYPE_NS)){
       ndp_processing_control_block.apply(hdr, local_metadata, standard_metadata); //This will set the local_metaata.do_l3_l2 field to true if this is a NDP packet
       //log_msg("egress spec is {} and egress port is {}",{standard_metadata.egress_spec , standard_metadata.egress_port});
       //TODO we may need to remove the extra headers if other switches forward these packet
       exit;
    }


    if (local_metadata.flag_hdr.do_l3_l2) {
        l2_ternary_processing_control_block.apply(hdr, local_metadata, standard_metadata);  //If it is a local broadcast packet we have to process it. but for spine and superspine we d not need it
        //log_msg("egress spec is {} and egress port is {}",{standard_metadata.egress_spec , standard_metadata.egress_port});
        my_station_processing_control_block.apply(hdr, local_metadata, standard_metadata);
        //log_msg("egress spec is {} and egress port is {}",{standard_metadata.egress_spec , standard_metadata.egress_port});
        if (hdr.ipv6.isValid() && local_metadata.flag_hdr.my_station_table_hit) {
            downstream_routing_control_clock.apply(hdr, local_metadata, standard_metadata);
            //log_msg("egress spec is {} and egress port is {}",{standard_metadata.egress_spec , standard_metadata.egress_port});
            if(local_metadata.flag_hdr.downstream_routing_table_hit){
                local_metadata.flag_hdr.is_pkt_toward_host = true;
                if(hdr.ipv6.hop_limit == 0) { mark_to_drop(standard_metadata); }
            }else{
                //Route the packet to upstream paths
                local_metadata.flag_hdr.is_pkt_toward_host = false;
                local_metadata.flag_hdr.found_multi_criteria_paths = true;
                #ifdef DP_ALGO_ECMP
                upstream_ecmp_routing_control_block.apply(hdr, local_metadata, standard_metadata);
                #endif
                #ifdef DP_ALGO_CP_ASSISTED_POLICY_ROUTING
                cp_assisted_multicriteria_upstream_routing_control_block.apply(hdr, local_metadata, standard_metadata);
                cp_assisted_multicriteria_upstream_policy_routing_control_block.apply(hdr, local_metadata, standard_metadata);
                #endif
                //log_msg("egress spec is {} and egress port is {}",{standard_metadata.egress_spec , standard_metadata.egress_port});
            }
        }
    }else{
        //log_msg("Unhandled packet in ingress processing");
    }



    }
}

//------------------------------------------------------------------------------
// 4. EGRESS PIPELINE
//
// In the v1model architecture, after the ingress pipeline, packets are
// processed by the Traffic Manager, which provides capabilities such as
// replication (for multicast or clone sessions), queuing, and scheduling.
//
// After the Traffic Manager, packets are processed by a so-called egress
// pipeline. Differently from the ingress one, egress tables can match on the
// egress_port intrinsic metadata as set by the Traffic Manager. If the Traffic
// Manager is configured to replicate the packet to multiple ports, the egress
// pipeline will see all replicas, each one with its own egress_port value.
//
// +---------------------+     +-------------+        +----------------------+
// | INGRESS PIPE        |     | TM          |        | EGRESS PIPE          |
// | ------------------- | pkt | ----------- | pkt(s) | -------------------- |
// | Set egress_spec,    |---->| Replication |------->| Match on egress port |
// | mcast_grp, or clone |     | Queues      |        |                      |
// | sess                |     | Scheduler   |        |                      |
// +---------------------+     +-------------+        +----------------------+
//
// Similarly to the ingress pipeline, the egress one operates on the parsed
// headers (hdr), the user-defined metadata (local_metadata), and the
// architecture-specific instrinsic one (standard_metadata) which now
// defines a read-only "egress_port" field.
//------------------------------------------------------------------------------
control EgressPipeImpl (inout parsed_headers_t hdr,
                        inout local_metadata_t local_metadata,
                        inout standard_metadata_t standard_metadata) {
    //==================My cuistom actions====================

    action set_all_header_invalid(){
        hdr.packet_out.setInvalid();
        hdr.packet_in.setInvalid();
        hdr.ethernet.setInvalid();
        hdr.ipv4.setInvalid();
        hdr.ipv6.setInvalid();
        hdr.mdn_int.setInvalid();
        hdr.p2p_feedback.setInvalid();
        hdr.tcp.setInvalid();
        hdr.udp.setInvalid();
        hdr.icmpv6.setInvalid();
        hdr.ndp.setInvalid();
        //hdr.delay_event_feedback.setInvalid();
    }
    action build_p2p_feedback_only(){
        hdr.p2p_feedback.setValid();
        bit<8> temp_next_hdr =   hdr.ipv6.next_hdr;
        hdr.ipv6.next_hdr = CONTROL_PACKET;
        hdr.p2p_feedback.next_hdr = temp_next_hdr;
        hdr.p2p_feedback.port_id = local_metadata.delay_info_hdr.path_delay_event_port;
        hdr.p2p_feedback.delay_event_type = local_metadata.delay_info_hdr.path_delay_event_type ;
        hdr.p2p_feedback.delay_event_data = local_metadata.delay_info_hdr.path_delay_event_data;
        hdr.mdn_int.setInvalid();
    }
    action build_p2p_feedback_with_fake_ack(){
        hdr.p2p_feedback.setValid();
        bit<8> temp_next_hdr =   hdr.ipv6.next_hdr;
        hdr.ipv6.next_hdr = CONTROL_PACKET;
        hdr.p2p_feedback.port_id = local_metadata.delay_info_hdr.path_delay_event_port;
        hdr.p2p_feedback.delay_event_type = local_metadata.delay_info_hdr.path_delay_event_type ;
        hdr.p2p_feedback.delay_event_data = local_metadata.delay_info_hdr.path_delay_event_data;
        hdr.p2p_feedback.next_hdr = MDN_INT;
        hdr.mdn_int.setValid();
        //mdn_int values are already set
        hdr.mdn_int.next_hdr = temp_next_hdr;
        hdr.tcp.ack_control_flag = FLAG_1 ;
        bit<128> temp_src_addr = hdr.ipv6.src_addr;
        hdr.ipv6.src_addr = hdr.ipv6.dst_addr;
        hdr.ipv6.dst_addr = temp_src_addr;
        hdr.ipv6.payload_len = 20; //Only the length of tcop header
        // now tcp header eschange
        bit<16> temp_src_port = hdr.tcp.src_port;
        hdr.tcp.src_port = hdr.tcp.dst_port;
        hdr.tcp.dst_port = temp_src_port;
        bit<32>  temp_ack_no = hdr.tcp.ack_no;
        hdr.tcp.ack_no = hdr.tcp.seq_no + 1;
        hdr.tcp.seq_no = temp_ack_no; // this means we are sending the seq number what the sender have acknowledged. that means no new data
        // REst of the fields are find. Just need  calculate the ipv6.payload_len
        bit<16>  new_window = hdr.tcp.window >>WINDOW_DECREASE_RATIO;
        hdr.tcp.window  = hdr.tcp.window - new_window;
        hdr.mdn_int.rate_control_event  = RATE_CONTROL_EVENT_ALREADY_APPLIED ;
        hdr.ipv6.ecn = 3;
    }
    action build_p2p_feedback_with_fake_ack_for_increase(){
        hdr.p2p_feedback.setValid();
        bit<8> temp_next_hdr =   hdr.ipv6.next_hdr;
        hdr.ipv6.next_hdr = CONTROL_PACKET;
        hdr.p2p_feedback.port_id = local_metadata.delay_info_hdr.path_delay_event_port;
        hdr.p2p_feedback.delay_event_type = local_metadata.delay_info_hdr.path_delay_event_type ;
        hdr.p2p_feedback.delay_event_data = local_metadata.delay_info_hdr.path_delay_event_data;
        hdr.p2p_feedback.next_hdr = MDN_INT;
        hdr.mdn_int.setValid();
        //mdn_int values are already set
        hdr.mdn_int.next_hdr = temp_next_hdr;
        hdr.tcp.ack_control_flag = FLAG_1 ;
        bit<128> temp_src_addr = hdr.ipv6.src_addr;
        hdr.ipv6.src_addr = hdr.ipv6.dst_addr;
        hdr.ipv6.dst_addr = temp_src_addr;
        hdr.ipv6.payload_len = 20; //Only the length of tcop header
        // now tcp header eschange
        bit<16> temp_src_port = hdr.tcp.src_port;
        hdr.tcp.src_port = hdr.tcp.dst_port;
        hdr.tcp.dst_port = temp_src_port;
        bit<32>  temp_ack_no = hdr.tcp.ack_no;
        hdr.tcp.ack_no = hdr.tcp.seq_no + 1;
        hdr.tcp.seq_no = temp_ack_no; // this means we are sending the seq number what the sender have acknowledged. that means no new data
        // REst of the fields are find. Just need  calculate the ipv6.payload_len
        bit<16>  new_window = hdr.tcp.window >>WINDOW_INCREASE_RATIO;
        hdr.tcp.window  = hdr.tcp.window + new_window;
        hdr.mdn_int.rate_control_event  = RATE_CONTROL_EVENT_ALREADY_APPLIED ; // This flag is carried all the way to source switch



    }
    action build_fake_ack_only(){
        hdr.mdn_int.setInvalid();
        hdr.p2p_feedback.setInvalid();

        hdr.tcp.ack_control_flag = FLAG_1 ;
        bit<128> temp_src_addr = hdr.ipv6.src_addr;
        hdr.ipv6.src_addr = hdr.ipv6.dst_addr;
        hdr.ipv6.dst_addr = temp_src_addr;
        hdr.ipv6.payload_len = 20; //Only the length of tcop header
        // now tcp header eschange
        bit<16> temp_src_port = hdr.tcp.src_port;
        hdr.tcp.src_port = hdr.tcp.dst_port;
        hdr.tcp.dst_port = temp_src_port;
        bit<32>  temp_ack_no = hdr.tcp.ack_no;
        hdr.tcp.ack_no = hdr.tcp.seq_no + 1;
        hdr.tcp.seq_no = temp_ack_no; // this means we are sending the seq number what the sender have acknowledged. that means no new data
        // REst of the fields are find. Just need  calculate the ipv6.payload_len
        bit<16>  new_window = hdr.tcp.window >>WINDOW_DECREASE_RATIO;
        hdr.tcp.window  = hdr.tcp.window - new_window;
        //hdr.ipv6.ecn = 3;
    }
    action build_fake_ack_only_for_increase(){
        hdr.mdn_int.setInvalid();
        hdr.p2p_feedback.setInvalid();

        hdr.tcp.ack_control_flag = FLAG_1 ;
        bit<128> temp_src_addr = hdr.ipv6.src_addr;
        hdr.ipv6.src_addr = hdr.ipv6.dst_addr;
        hdr.ipv6.dst_addr = temp_src_addr;
        hdr.ipv6.payload_len = 20; //Only the length of tcop header
        // now tcp header eschange
        bit<16> temp_src_port = hdr.tcp.src_port;
        hdr.tcp.src_port = hdr.tcp.dst_port;
        hdr.tcp.dst_port = temp_src_port;
        bit<32>  temp_ack_no = hdr.tcp.ack_no;
        hdr.tcp.ack_no = hdr.tcp.seq_no + 1;
        hdr.tcp.seq_no = temp_ack_no; // this means we are sending the seq number what the sender have acknowledged. that means no new data
        // REst of the fields are find. Just need  calculate the ipv6.payload_len
        bit<16>  new_window = hdr.tcp.window >>WINDOW_INCREASE_RATIO;
        hdr.tcp.window  = hdr.tcp.window + new_window;

        }
    //========================
    #ifdef ENABLE_DEBUG_TABLES
    debug_std_meta() debug_std_meta_egress_start;
    #endif  // ENABLE_DEBUG_TABLES
    egress_rate_monitor() egress_rate_monitor_control_block;
    egress_queue_depth_monitor() egress_queue_depth_monitor_control_block;
    #ifdef DP_BASED_RATE_CONTROL_ENABLED
    leaf_rate_control_processor() leaf_rate_control_processor_control_block;
    #endif

    apply {
        //if (local_metadata.is_multicast == true &&
        //      standard_metadata.ingress_port == standard_metadata.egress_port) {
        //    mark_to_drop(standard_metadata);
        //}
        bool is_recirculation_needed = false;
        // we can only do these stuuffs if this packet is a normal packet .
        if(IS_NORMAL(standard_metadata)){

            egress_queue_depth_monitor_control_block.apply(hdr, local_metadata, standard_metadata);
            egress_rate_monitor_control_block.apply(hdr, local_metadata, standard_metadata);
            #ifdef DP_BASED_RATE_CONTROL_ENABLED
            leaf_rate_control_processor_control_block.apply(hdr, local_metadata, standard_metadata);
            #elif  DP_ALGO_ECMP
            if(standard_metadata.deq_qdepth > ECN_THRESHOLD) hdr.ipv6.ecn = 3; //setting ecm mark
            #endif

            if (local_metadata.is_multicast == true ) {
                exit;
            }
            #ifdef DP_ALGO_CP_ASSISTED_POLICY_ROUTING
            if(IS_RECIRC_NEEDED(local_metadata)) {
                is_recirculation_needed = true;
            }
            #endif
            //TODO : if everything goes ok. We can convert this if-else to a single MAT

            if(is_recirculation_needed &&   IS_CONTROL_PKT_TO_NEIGHBOUR(local_metadata) && IS_CONTROL_PKT_TO_CP(local_metadata)){
                //log_msg("clone to session id  ing_port + Max_port * 2 --> this have both ingress port and CPU port and recirculation port");
                clone3(CloneType.E2E, (bit<32>)(standard_metadata.ingress_port)+ ((bit<32>)MAX_PORTS_IN_SWITCH * 2), {standard_metadata, local_metadata});
            }else if(  IS_CONTROL_PKT_TO_NEIGHBOUR(local_metadata) && IS_CONTROL_PKT_TO_CP(local_metadata)){
                //log_msg("clone to session id ing_port + Max_port  --> this have both ingress port and CPU port");
                clone3(CloneType.E2E, (bit<32>)(standard_metadata.ingress_port)+ (bit<32>)MAX_PORTS_IN_SWITCH, {standard_metadata, local_metadata});
            }else if (IS_CONTROL_PKT_TO_CP(local_metadata)) {
                //log_msg("clone to CPU port only");
                clone3(CloneType.E2E, CPU_CLONE_SESSION_ID, {standard_metadata, local_metadata});
            }else if ( IS_CONTROL_PKT_TO_NEIGHBOUR(local_metadata)) {
                 //log_msg("clone to ingress port for feedback to neighbour");
                 clone3(CloneType.E2E, (bit<32>)(standard_metadata.ingress_port), {standard_metadata, local_metadata});
            }else{
                 //log_msg("Unhandled logic in cloning control block");
            }
        }


// for handling the fake ACK we need to do 2 things
// 1) the switch it is generating -- here in egress we ned to build the fake ack based on some flags
// 2)  in other switches when this pkt is rcvd, it is normal pkt. but we have to make sure that this packet is not generating any other fake ack. so we have to identify if the pkt is a fake ack.

//if the pkt have valid mdn_int && ack_flag==1 && instance_type == e2i && hdr.mdn_int.rate_control_event ==RATE_CONTROL_EVENT_ALREADY_APPLIED -- that means this is a pkt generated for fake ack from egress. we need to forward it
  //     if this happens then we do not need to build neighbour hood feedback pkt


    if(IS_NORMAL(standard_metadata)){
        egressPortCounter.count((bit<32>)standard_metadata.egress_port);
        if(local_metadata.flag_hdr.is_pkt_toward_host){
            //log_msg("Egress_log: found packet toward host. Removing all extra headers. In future we may need to control tcp headers here");
            if(hdr.p2p_feedback.isValid() && hdr.mdn_int.isValid()){ //this is a fake ack
                //log_msg("A fake ack is being sent to the host");
                hdr.ipv6.next_hdr = hdr.mdn_int.next_hdr ;
                hdr.mdn_int.setInvalid();
                hdr.p2p_feedback.setInvalid();
            }else if(hdr.mdn_int.isValid()){
                //log_msg("This is a packet from a switch toward a host.Getting rid of the extra headers");
                hdr.ipv6.next_hdr = hdr.mdn_int.next_hdr;
                hdr.mdn_int.setInvalid();
                //ekhane somehow deklay_hdr valid paccje. j karone ndp ns er reply vull next_hdr soho
            }else{
                log_msg("This is a packet from a host toward a host. So no need to clone E2E for feedback");
                hdr.mdn_int.setInvalid();  //This is not needed for else part. But no harm in doing extra invalid. NOt optimized obviously
            }
        }else if (standard_metadata.egress_port == PORT_ZERO) {
             //log_msg("A normal packet has been  decided to be sent on port 0. Which should not be. Debug it");
             recirculate<parsed_headers_t>(hdr);
             mark_to_drop(standard_metadata);
        }else if (standard_metadata.egress_port == CPU_PORT) {
            //log_msg("This is a p2p feedback received from some neighbour switch. and sending it to CP");
            // Add packet_in header and set relevant fields, such as the
            // switch ingress port where the packet was received.
            set_all_header_invalid();
            hdr.packet_in.setValid();
            //hdr.dp_to_cp_feedback_hdr.setValid();
            hdr.packet_in.ingress_port = standard_metadata.ingress_port;
            //log_msg("Found msg for CP from created by p2p feedback ingress port {} with delay event type {}",{standard_metadata.ingress_port, local_metadata.delay_info_hdr.path_delay_event_type});
            //===
            hdr.packet_in.ingress_queue_event = local_metadata.ingress_queue_event_hdr.ingress_queue_event;
            hdr.packet_in.ingress_queue_event_data = local_metadata.ingress_queue_event_hdr.ingress_queue_event_data ;
            hdr.packet_in.ingress_queue_event_port =local_metadata.ingress_queue_event_hdr.ingress_queue_event_port;
            //===
            hdr.packet_in.egress_queue_event = local_metadata.egress_queue_event_hdr.egress_queue_event ;
            hdr.packet_in.egress_queue_event_data = local_metadata.egress_queue_event_hdr.egress_queue_event_data  ;
            hdr.packet_in.egress_queue_event_port = local_metadata.egress_queue_event_hdr.egress_queue_event_port;
            //===
            hdr.packet_in.ingress_traffic_color = local_metadata.ingress_rate_event_hdr.ingress_traffic_color  ;
            hdr.packet_in.ingress_rate_event_data = local_metadata.ingress_rate_event_hdr.ingress_rate_event_data  ;
            hdr.packet_in.ingress_rate_event_port = local_metadata.ingress_rate_event_hdr.ingress_rate_event_port;
            //log_msg("In cp feedback msg. egress traffic color is {}",{hdr.packet_in.egress_traffic_color});
            //===
            hdr.packet_in.egress_traffic_color = local_metadata.egress_rate_event_hdr.egress_traffic_color  ;
            hdr.packet_in.egress_rate_event_data = local_metadata.egress_rate_event_hdr.egress_rate_event_data  ;
            hdr.packet_in.egress_rate_event_port = local_metadata.egress_rate_event_hdr.egress_rate_event_port;
            //============
            hdr.packet_in.path_delay_event_type = hdr.p2p_feedback.delay_event_type ;
            hdr.packet_in.path_delay_event_data = hdr.p2p_feedback.delay_event_data;
            hdr.packet_in.dst_addr = local_metadata.delay_info_hdr.dst_addr;  //TODO : this is not correct. but we are not using this for now
            hdr.packet_in.path_delay_event_port =  local_metadata.delay_info_hdr.path_delay_event_port;
            //Set all other headers except the acket_in as invalid
        }
        else{
            //log_msg("Egress_log: Before sending a packet from leaf switch to non host neighbour. So adding the delay header{} {}", {hdr.ipv6.next_hdr, hdr.mdn_int.next_hdr});
            hdr.mdn_int.setValid();
            bit<8> temp_next_hdr =   hdr.ipv6.next_hdr ;
            hdr.ipv6.next_hdr = MDN_INT;
            hdr.mdn_int.src_enq_timestamp = local_metadata.pkt_timestamp.src_enq_timestamp;
            hdr.mdn_int.src_deq_timestamp = local_metadata.pkt_timestamp.src_deq_timestamp;
            hdr.mdn_int.next_hdr = temp_next_hdr;
            //log_msg("Egress_log: After sending a packet from leaf switch to non host neighbour. So adding the delay header{} {}", {hdr.ipv6.next_hdr, hdr.mdn_int.next_hdr});
        }
    }else{ //this is a cloned packet for control events
                // if dp_only_flag-- then recirculate
        if (standard_metadata.egress_port == PORT_ZERO) {
            set_all_header_invalid();
            hdr.ethernet.setValid();
            hdr.ethernet.ether_type = 0;
            hdr.packet_in.setValid();
                            //hdr.dp_to_cp_feedback_hdr.setValid();
            hdr.packet_in.ingress_port = standard_metadata.ingress_port;

            //===
            hdr.packet_in.ingress_queue_event = local_metadata.ingress_queue_event_hdr.ingress_queue_event;
            hdr.packet_in.ingress_queue_event_data = local_metadata.ingress_queue_event_hdr.ingress_queue_event_data ;
            hdr.packet_in.ingress_queue_event_port =local_metadata.ingress_queue_event_hdr.ingress_queue_event_port;
            //===
            hdr.packet_in.egress_queue_event = local_metadata.egress_queue_event_hdr.egress_queue_event ;
            hdr.packet_in.egress_queue_event_data = local_metadata.egress_queue_event_hdr.egress_queue_event_data  ;
            hdr.packet_in.egress_queue_event_port = local_metadata.egress_queue_event_hdr.egress_queue_event_port;
            //===
            hdr.packet_in.ingress_traffic_color = local_metadata.ingress_rate_event_hdr.ingress_traffic_color  ;
            hdr.packet_in.ingress_rate_event_data = local_metadata.ingress_rate_event_hdr.ingress_rate_event_data  ;
            hdr.packet_in.ingress_rate_event_port = local_metadata.ingress_rate_event_hdr.ingress_rate_event_port;
            //===
            hdr.packet_in.egress_traffic_color = local_metadata.egress_rate_event_hdr.egress_traffic_color  ;
            hdr.packet_in.egress_rate_event_data = local_metadata.egress_rate_event_hdr.egress_rate_event_data  ;
            hdr.packet_in.egress_rate_event_port = local_metadata.egress_rate_event_hdr.egress_rate_event_port;
            //log_msg("In cp feedback msg. egress traffic color is {}",{hdr.packet_in.egress_traffic_color});
            //============
            hdr.packet_in.path_delay_event_type = local_metadata.delay_info_hdr.path_delay_event_type ;
            hdr.packet_in.path_delay_event_data = local_metadata.delay_info_hdr.path_delay_event_data;
            hdr.packet_in.dst_addr = local_metadata.delay_info_hdr.dst_addr;
            hdr.packet_in.path_delay_event_port =  local_metadata.delay_info_hdr.path_delay_event_port;
            recirculate<parsed_headers_t>(hdr);
            //log_msg("A cloned packet is being recirculated");
        }else if (standard_metadata.egress_port == CPU_PORT) {
            // Add packet_in header and set relevant fields, such as the
            // switch ingress port where the packet was received.
            set_all_header_invalid();
            hdr.packet_in.setValid();
            //hdr.dp_to_cp_feedback_hdr.setValid();
            hdr.packet_in.ingress_port = standard_metadata.ingress_port;
            // Exit the pipeline here.
            //log_msg("Found msg for CP from ingress port {} with delay event type {}",{standard_metadata.ingress_port, local_metadata.delay_info_hdr.path_delay_event_type});
            //===
            hdr.packet_in.ingress_queue_event = local_metadata.ingress_queue_event_hdr.ingress_queue_event;
            hdr.packet_in.ingress_queue_event_data = local_metadata.ingress_queue_event_hdr.ingress_queue_event_data ;
            hdr.packet_in.ingress_queue_event_port =local_metadata.ingress_queue_event_hdr.ingress_queue_event_port;
            //===
            hdr.packet_in.egress_queue_event = local_metadata.egress_queue_event_hdr.egress_queue_event ;
            hdr.packet_in.egress_queue_event_data = local_metadata.egress_queue_event_hdr.egress_queue_event_data  ;
            hdr.packet_in.egress_queue_event_port = local_metadata.egress_queue_event_hdr.egress_queue_event_port;
            //===
            hdr.packet_in.ingress_traffic_color = local_metadata.ingress_rate_event_hdr.ingress_traffic_color  ;
            hdr.packet_in.ingress_rate_event_data = local_metadata.ingress_rate_event_hdr.ingress_rate_event_data  ;
            hdr.packet_in.ingress_rate_event_port = local_metadata.ingress_rate_event_hdr.ingress_rate_event_port;
            //===
            hdr.packet_in.egress_traffic_color = local_metadata.egress_rate_event_hdr.egress_traffic_color  ;
            hdr.packet_in.egress_rate_event_data = local_metadata.egress_rate_event_hdr.egress_rate_event_data  ;
            hdr.packet_in.egress_rate_event_port = local_metadata.egress_rate_event_hdr.egress_rate_event_port;
            //log_msg("In cp feedback msg. egress traffic color is {}",{hdr.packet_in.egress_traffic_color});
            //============
            hdr.packet_in.path_delay_event_type = local_metadata.delay_info_hdr.path_delay_event_type ;
            hdr.packet_in.path_delay_event_data = local_metadata.delay_info_hdr.path_delay_event_data;
            hdr.packet_in.dst_addr = local_metadata.delay_info_hdr.dst_addr;
            hdr.packet_in.path_delay_event_port =  local_metadata.delay_info_hdr.path_delay_event_port;
            ctrlPktToCPCounter.count((bit<32>)standard_metadata.egress_port);
            ////log_msg("chceking feedback values{}", {local_metadata});
        }else{
            //log_msg("This is a peer to peer feedback message in cloned part (for fake ack). this means a original packet is being cloned to ingress port. At this moment only add delay feedback and feedback ACK. Later we may add more stuffs");
            p2pFeedbackCounter.count((bit<32>)standard_metadata.egress_port);
            #ifdef DP_BASED_RATE_CONTROL_ENABLED
            if (hdr.mdn_int.isValid()   && (hdr.mdn_int.rate_control_event  == RATE_DECREASE_EVENT_NEED_TO_BE_APPLIED_IN_THIS_SWITCH)){
                if(local_metadata.flag_hdr.is_packet_from_downstream_port == true){
                    build_fake_ack_only();
                }else if (local_metadata.flag_hdr.is_packet_from_upstream_port == true){
                    build_p2p_feedback_with_fake_ack();
                }
            }else{
                if(local_metadata.flag_hdr.is_packet_from_downstream_port == true){
                    mark_to_drop(standard_metadata);
                }else if (local_metadata.flag_hdr.is_packet_from_upstream_port == true){
                    build_p2p_feedback_only();
                }

            }
            if (hdr.mdn_int.isValid()   && (hdr.mdn_int.rate_control_event  == RATE_INCREASE_EVENT_NEED_TO_BE_APPLIED_IN_THIS_SWITCH)){
                if(local_metadata.flag_hdr.is_packet_from_downstream_port == true){
                    build_fake_ack_only_for_increase();
                }else if (local_metadata.flag_hdr.is_packet_from_upstream_port == true){
                    build_p2p_feedback_with_fake_ack_for_increase();
                }
            }else{
                if(local_metadata.flag_hdr.is_packet_from_downstream_port == true){
                    mark_to_drop(standard_metadata);
                }else if (local_metadata.flag_hdr.is_packet_from_upstream_port == true){
                    build_p2p_feedback_only();
                }

            }
            //build_p2p_feedback_only();
            #else
            if(local_metadata.flag_hdr.is_packet_from_downstream_port == true){
                mark_to_drop(standard_metadata); //Because we do not want to send the feedback packets to hosts
            }else if (local_metadata.flag_hdr.is_packet_from_upstream_port == true){
                build_p2p_feedback_only();
            }
            #endif
        }
    }

    }
}


//------------------------------------------------------------------------------
// 5. CHECKSUM UPDATE
//
// Provide logic to update the checksum of outgoing packets.
//------------------------------------------------------------------------------
control ComputeChecksumImpl(inout parsed_headers_t hdr,
                            inout local_metadata_t local_metadata)
{
    apply {
        // The following function is used to update the ICMPv6 checksum of NDP
        // NA packets generated by the ndp_reply_table in the ingress pipeline.
        // This function is executed only if the NDP header is present.
        update_checksum(hdr.ndp.isValid(),
            {
               hdr.ipv6.src_addr,
               hdr.ipv6.dst_addr,
                hdr.ipv6.payload_len,
                8w0,
                hdr.ipv6.next_hdr,
                hdr.icmpv6.type,
                hdr.icmpv6.code,
                hdr.ndp.flags,
                hdr.ndp.target_ipv6_addr,
                hdr.ndp.type,
                hdr.ndp.length,
                hdr.ndp.target_mac_addr
            },
            hdr.icmpv6.checksum,
            HashAlgorithm.csum16
        );
    }
}


//------------------------------------------------------------------------------
// 6. DEPARSER
//
// This is the last block of the V1Model architecture. The deparser specifies in
// which order headers should be serialized on the wire. When calling the emit
// primitive, only headers that are marked as "valid" are serialized, otherwise,
// they are ignored.
//------------------------------------------------------------------------------
control DeparserImpl(packet_out packet, in parsed_headers_t hdr) {
    apply {
        packet.emit(hdr.packet_in);
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv6);
        packet.emit(hdr.mdn_int);
        packet.emit(hdr.p2p_feedback);
        packet.emit(hdr.tcp);
        packet.emit(hdr.udp);
        packet.emit(hdr.icmpv6);
        packet.emit(hdr.ndp);
    }
}

//------------------------------------------------------------------------------
// V1MODEL SWITCH INSTANTIATION
//
// Finally, we instantiate a v1model switch with all the control block
// instances defined so far.
//------------------------------------------------------------------------------
V1Switch(
    ParserImpl(),
    VerifyChecksumImpl(),
    IngressPipeImpl(),
    EgressPipeImpl(),
    ComputeChecksumImpl(),
    DeparserImpl()
) main;
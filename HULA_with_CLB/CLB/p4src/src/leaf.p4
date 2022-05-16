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
#include "upstream_routing.p4"
#include "ndp.p4"
#include "l2_ternary.p4"
#include "my_station.p4"
#include "l2_ternary.p4"
#include "leaf_downstream_routing.p4"
#include "clb_load_balancer.p4"
#include "hula.p4"


control VerifyChecksumImpl(inout parsed_headers_t hdr,inout local_metadata_t meta)
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


    leaf_downstream_routing () downstream_routing_control_clock;
    l2_ternary_processing() l2_ternary_processing_control_block;
    my_station_processing() my_station_processing_control_block;
    ndp_processing() ndp_processing_control_block;

    #ifdef DP_ALGO_ECMP
    upstream_routing() upstream_ecmp_routing_control_block;
    #endif


    #ifdef DP_ALGO_HULA
    hula_load_balancing() hula_load_balancing_control_block;
    #endif


    #ifdef DP_ALGO_CLB
    clb_load_balancing() clb_load_balancing_control_block;
    #endif

    apply {
    local_metadata.flag_hdr.do_l3_l2=true;
    local_metadata.flag_hdr.downstream_routing_table_hit = false;
    if (hdr.packet_out.isValid()) {
       // Set the egress port to that found in the packet-out metadata...
       standard_metadata.egress_spec = hdr.packet_out.egress_port;
       // Remove the packet-out header...
       hdr.packet_out.setInvalid();
       // Exit the pipeline here, no need to go through other tables.
       log_msg("LB: found a control packet");
       //exit;

       //process control packet here -- header format for ctrtIn --> counterReset= yes or no,
       if(hdr.packet_out.clb_flags[7:7] == (bit<1>)1){
           bit<32> load_counter_value = 0;
           load_counter.write(hdr.packet_out.tor_id, load_counter_value); //Reset the counter
           log_msg("LB: Control Message for reset counter found");
           mark_to_drop(standard_metadata);
           exit;
       }
       else if(hdr.packet_out.clb_flags[6:6] == (bit<1>)1){ //This is a control packet
           stored_bitmask.write( hdr.packet_out.tor_id, hdr.packet_out.bitmask[BITMASK_LENGTH - 1 :0]);
           level_to_link_store.write( (bit<32>)hdr.packet_out.level_to_link_id_store_index, hdr.packet_out.link_id);
           log_msg("LB: Control Message for path control:: linkID--{},  bitmask--{} level_to_link_id_store_index--{}",
                                          {hdr.packet_out.link_id, hdr.packet_out.bitmask[BITMASK_LENGTH - 1 :0], hdr.packet_out.level_to_link_id_store_index});
       }else{
           log_msg("LB: The CLB flag is unsupported --{}", {hdr.packet_out.clb_flags});
           log_msg("LB: Control Message for path control:: linkID--{},  bitmask--{} level_to_link_id_store_index--{}",
                                                     {hdr.packet_out.link_id, hdr.packet_out.bitmask[BITMASK_LENGTH - 1 :0], hdr.packet_out.level_to_link_id_store_index});
       }
    }else if (hdr.packet_in.isValid() && IS_RECIRCULATED(standard_metadata)) {  //This means this packet is replicated from egress
        //log_msg("Found a recirculated packet");
        local_metadata.flag_hdr.do_l3_l2 = false; //thie means . this packet doesn;t need normal forwarding processing.
        mark_to_drop(standard_metadata);
   }else{ //This means these packets are normal packets and they will generate the events


    }

    #ifdef ENABLE_DEBUG_TABLES
    debug_std_meta_ingress_start.apply(hdr, local_metadata, standard_metadata);
    #endif  // ENABLE_DEBUG_TABLES
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
                local_metadata.flag_hdr.found_multi_criteria_paths = false; // this means we must need to use ecmp path
                if ( local_metadata.flag_hdr.found_multi_criteria_paths  == false){ // this means in multicriteria table we have not found any paths. This may be due to lack of proper traffic class or IP predix in those tables
                    upstream_ecmp_routing_control_block.apply(hdr, local_metadata, standard_metadata);
                }
                #endif


                #ifdef DP_ALGO_CLB
                clb_load_balancing_control_block.apply(hdr, local_metadata, standard_metadata);
                #endif

                #ifdef DP_ALGO_HULA
                hula_load_balancing_control_block.apply(hdr, local_metadata, standard_metadata);
                #endif

            }
        }
    }else{
        //log_msg("Unhandled packet in ingress processing");
    }


    //log_msg("hdr.mdn_int.next_hdr after applying upstream routing = {}",{hdr.mdn_int.next_hdr});
    //acl_table.apply();
    #ifdef ENABLE_DEBUG_TABLES
    ingress_end_debug.apply(hdr, local_metadata, standard_metadata);
    #endif  // ENABLE_DEBUG_TABLES

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



    //========================
    #ifdef ENABLE_DEBUG_TABLES
    debug_std_meta() debug_std_meta_egress_start;
    #endif  // ENABLE_DEBUG_TABLES

    apply {
       if (standard_metadata.egress_port == CPU_PORT) {
           // Add packet_in header and set relevant fields, such as the
           // switch ingress port where the packet was received.
           hdr.packet_in.setValid();
           hdr.packet_in.ingress_port = standard_metadata.ingress_port;
           // Exit the pipeline here.
           exit;
       }

               // If this is a multicast packet (flag set by l2_ternary_table), make
               // sure we are not replicating the packet on the same port where it was
               // received. This is useful to avoid broadcasting NDP requests on the
               // ingress port.
       if (local_metadata.is_multicast == true &&
             standard_metadata.ingress_port == standard_metadata.egress_port) {
           mark_to_drop(standard_metadata);
       }


    #ifdef ENABLE_DEBUG_TABLES
    debug_std_meta_egress_start.apply(hdr, local_metadata, standard_metadata);
    #endif  // ENABLE_DEBUG_TABLES

    //egressPortCounter.count((bit<32>)standard_metadata.egress_port);

    //This block is  for destination based util count by each path
    /*bit<32> temp_util = 0;
    bit<32> register_index = (bit<32>)standard_metadata.egress_port * (bit<32>)hdr.ipv6.dst_addr[15:0]; //rightmost 16 bit shows the ToR ID in our scheme.
    destination_util_counter.count((bit<32>)register_index);
    log_msg("Old util was {}",{temp_util});
    temp_util = temp_util + standard_metadata.packet_length;
    destination_util_counter.write( (bit<32>)register_index, temp_util);
    log_msg("new util is {}",{temp_util});*/

    bit<32> counter_index = (bit<32>)standard_metadata.egress_port + (MAX_PORTS_IN_SWITCH* (bit<32>)hdr.ipv6.dst_addr[31:16]) -1 ; //rightmost 16 bit shows the ToR ID in our scheme.
    //log_msg("IP address is {} index is {}", {(bit<64>)hdr.ipv6.dst_addr, counter_index});
    //log_msg("Tor id is {}",{(bit<32>)hdr.ipv6.dst_addr[31:16]});

    destination_util_counter.count((bit<32>)counter_index);
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
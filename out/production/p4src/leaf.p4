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
#include "ingress_stats.p4"

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
    #ifdef ENABLE_DEBUG_TABLES
    debug_std_meta() debug_std_meta_ingress_start;
    #endif  // ENABLE_DEBUG_TABLES
    #ifdef LEAF_INGRESS_STATS
    leaf_ingress_stats_table() leaf_ingress_stats;
    #endif  // ENABLE_DEBUG_TABLES


    // Drop action definition, shared by many tables. Hence we define it on top.
    action drop() {
        // Sets an architecture-specific metadata field to signal that the
        // packet should be dropped at the end of this pipeline.
        mark_to_drop(standard_metadata);
    }
    action set_egress_port(port_num_t port_num) {
        standard_metadata.egress_spec = port_num;
    }
    action set_multicast_group(mcast_group_id_t gid) {
        // gid will be used by the Packet Replication Engine (PRE) in the
        // Traffic Manager--located right after the ingress pipeline, to
        // replicate a packet to multiple egress ports, specified by the control
        // plane by means of P4Runtime MulticastGroupEntry messages.
        standard_metadata.mcast_grp = gid;
        local_metadata.is_multicast = true;
    }

    table l2_ternary_table {
        key = {
            hdr.ethernet.dst_addr: ternary;
        }
        actions = {
            set_multicast_group;
            @defaultonly drop;
        }
        const default_action = drop;
        @name("l2_ternary_table_counter")
        counters = direct_counter(CounterType.packets_and_bytes);
    }
    action ndp_ns_to_na(mac_addr_t target_mac) {
            hdr.ethernet.src_addr = target_mac;
            hdr.ethernet.dst_addr = IPV6_MCAST_01;
            //hdr.ethernet.dst_addr = hdr.ethernet.src_addr;
            //hdr.ethernet.src_addr = target_mac;
            ipv6_addr_t host_ipv6_tmp = hdr.ipv6.src_addr;
            hdr.ipv6.src_addr = hdr.ndp.target_ipv6_addr;
            hdr.ipv6.dst_addr = host_ipv6_tmp;
            hdr.ipv6.next_hdr = IP_PROTO_ICMPV6;
            hdr.icmpv6.type = ICMP6_TYPE_NA;
            hdr.ndp.flags = NDP_FLAG_ROUTER | NDP_FLAG_OVERRIDE;
            hdr.ndp.type = NDP_OPT_TARGET_LL_ADDR;
            hdr.ndp.length = 1;
            hdr.ndp.target_mac_addr = target_mac;
            standard_metadata.egress_spec = standard_metadata.ingress_port;
        }

        table ndp_reply_table {
            key = {
                hdr.ipv6.src_addr: exact;
            }
            actions = {
                ndp_ns_to_na;
            }
            @name("ndp_reply_table_counter")
            counters = direct_counter(CounterType.packets_and_bytes);
        }

    table my_station_table {
        key = {
            hdr.ethernet.dst_addr: exact;
        }
        actions = { NoAction; }
        @name("my_station_table_counter")
        counters = direct_counter(CounterType.packets_and_bytes);
    }


    // *** ACL
    //
    // Provides ways to override a previous forwarding decision, for example
    // requiring that a packet is cloned/sent to the CPU, or dropped.
    //
    // We use this table to clone all NDP packets to the control plane, so to
    // enable host discovery. When the location of a new host is discovered, the
    // controller is expected to update the L2 and L3 tables with the
    // correspionding brinding and routing entries.

    // --- acl_table -----------------------------------------------------------

    action send_to_cpu() {
        standard_metadata.egress_spec = CPU_PORT;
    }

    action clone_to_cpu() {
        // Cloning is achieved by using a v1model-specific primitive. Here we
        // set the type of clone operation (ingress-to-egress pipeline), the
        // clone session ID (the CPU one), and the metadata fields we want to
        // preserve for the cloned packet replica.
        clone3(CloneType.I2E, CPU_CLONE_SESSION_ID, { standard_metadata.ingress_port });
    }

    table acl_table {
        key = {
            standard_metadata.ingress_port: ternary;
            hdr.ethernet.dst_addr:          ternary;
            hdr.ethernet.src_addr:          ternary;
            hdr.ethernet.ether_type:        ternary;
            hdr.ipv6.next_hdr:              ternary;
            hdr.icmpv6.type:                ternary;
            local_metadata.l4_src_port:     ternary;
            local_metadata.l4_dst_port:     ternary;
        }
        actions = {
            send_to_cpu;
            clone_to_cpu;
            drop;
            NoAction;
        }
        const default_action = NoAction;

        @name("acl_table_counter")
        counters = direct_counter(CounterType.packets_and_bytes);
    }


    //////****************************************************************Tables specific for Leaf Switches
    @name("host_egress_meter") direct_meter<bit<32>>(MeterType.bytes) host_egress_meter;

    action set_downstream_egress_port(port_num_t port_num,mac_addr_t dmac) {
            standard_metadata.egress_spec = port_num;
            hdr.ethernet.src_addr = hdr.ethernet.dst_addr;
            hdr.ethernet.dst_addr = dmac;
            // Decrement TTL
            hdr.ipv6.hop_limit = hdr.ipv6.hop_limit - 1;
            host_egress_meter.read(local_metadata.m_color);
    }
    table downstream_routing_table {
          key = {
              hdr.ipv6.dst_addr:          exact;

          }
          actions = {
              set_downstream_egress_port;
          }
          @name("downstream_routing_table")
          counters = direct_counter(CounterType.packets_and_bytes);
          meters = host_egress_meter;
    }


    action set_upstream_egress_port(port_num_t port_num) {
          standard_metadata.egress_spec = port_num;
        // Decrement TTL
          hdr.ipv6.hop_limit = hdr.ipv6.hop_limit - 1;
    }
    action_selector(HashAlgorithm.crc16, 32w128, 32w16) upstream_path_selector;
    table upstream_routing_table {
          key = {
              hdr.ipv6.dst_addr:          lpm;

              hdr.ipv6.dst_addr:          selector;
              hdr.ipv6.src_addr:          selector;
              hdr.ipv6.flow_label:        selector;
              hdr.ipv6.next_hdr:          selector;
              local_metadata.l4_src_port: selector;
              local_metadata.l4_dst_port: selector;
              standard_metadata.ingress_global_timestamp: selector;
          }
          actions = {
              set_upstream_egress_port;
          }
          implementation = upstream_path_selector;
          @name("upstream_routing_table_counter")
          counters = direct_counter(CounterType.packets_and_bytes);


    }

    // *** APPLY BLOCK STATEMENT

    bool do_l3_l2 = true;
    apply {
    #ifdef ENABLE_DEBUG_TABLES
    debug_std_meta_ingress_start.apply(hdr, local_metadata, standard_metadata);
    #endif  // ENABLE_DEBUG_TABLES
    #ifdef LEAF_INGRESS_STATS
    leaf_ingress_stats.apply(hdr, local_metadata, standard_metadata);
    #endif  // ENABLE_DEBUG_TABLES

    // If this is a packet-out from the controller...
    #ifdef  BASELINE
    if (hdr.packet_out.isValid()) {
       // Set the egress port to that found in the packet-out metadata...
       standard_metadata.egress_spec = hdr.packet_out.egress_port;
       // Remove the packet-out header...
       hdr.packet_out.setInvalid();
       // Exit the pipeline here, no need to go through other tables.
       exit;
    }

    if ((hdr.icmpv6.type == ICMP6_TYPE_NS ) && (hdr.icmpv6.type == ICMP6_TYPE_NS)){
       if (ndp_reply_table.apply().hit) { do_l3_l2 = false; }
    }
    if (do_l3_l2) {
        l2_ternary_table.apply();  //If it is a local broadcast packet we have to process it. but for spine and superspine we d not need it

        if (hdr.ipv6.isValid() && my_station_table.apply().hit) {
            if(downstream_routing_table.apply().hit){
                if (local_metadata.m_color >1) {drop();}
                if(hdr.ipv6.hop_limit == 0) { drop(); }
            }else{
            //Route the packet to upstream paths
                upstream_routing_table.apply();
            }
        }
    }
    acl_table.apply();
    #endif

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
     #ifdef ENABLE_DEBUG_TABLES
    debug_std_meta() debug_std_meta_egress_start;
    #endif  // ENABLE_DEBUG_TABLES
    #ifdef LEAF_INGRESS_STATS
    leaf_ingress_stats_table() leaf_egress_stats;
    #endif  // ENABLE_DEBUG_TABLES

    apply {
    #ifdef ENABLE_DEBUG_TABLES
        debug_std_meta_egress_start.apply(hdr, local_metadata, standard_metadata);
        #endif  // ENABLE_DEBUG_TABLES
     #ifdef LEAF_INGRESS_STATS
        leaf_egress_stats.apply(hdr, local_metadata, standard_metadata);
        #endif  // ENABLE_DEBUG_TABLES
        // If this is a packet-in to the controller, e.g., if in ingress we
        // matched on the ACL table with action send/clone_to_cpu...
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
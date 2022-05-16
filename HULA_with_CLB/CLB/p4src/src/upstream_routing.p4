
/*
#include <core.p4>






#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef UPSTREAM_ROUTING
#define UPSTREAM_ROUTING
control upstream_routing(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{
    action set_upstream_egress_port(port_num_t port_num) {
        standard_metadata.egress_spec = port_num;
        // Decrement TTL
        hdr.ipv6.hop_limit = hdr.ipv6.hop_limit - 1;
    }
    action_selector(HashAlgorithm.crc16, 32w128, 32w16) upstream_path_selector;
    table upstream_routing_table {
        key = {
            hdr.ipv6.dst_addr:          lpm;
            //===================================================
            hdr.ipv6.dst_addr:          selector;
            hdr.ipv6.src_addr:          selector;
            local_metadata.temp_8_bit:   selector;  //As we have modified the protcool headers according to our needs . we are using tempporary variable to store tcp protocol version to replicate
            //the exact behavior of ECMP
            local_metadata.l4_src_port: selector;
            local_metadata.l4_dst_port: selector;
        }
        actions = {
            set_upstream_egress_port;
        }
        implementation = upstream_path_selector;
        @name("upstream_routing_table_counter")
        counters = direct_counter(CounterType.packets_and_bytes);
    }
    apply {
        local_metadata.temp_8_bit = IP_PROTO_TCP;
        upstream_routing_table.apply();
    }
}
#endif

*/
//=================
#include <core.p4>






#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef UPSTREAM_ROUTING
#define UPSTREAM_ROUTING
control upstream_routing(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{
    @name("ecmp_flowlet_id_map") register<bit<16>>(32w8192) ecmp_flowlet_id_map;
    @name("ecmp_flowlet_lasttime_map") register<bit<48>>(32w8192) ecmp_flowlet_lasttime_map;

    @name("lookup_flowlet_map") action lookup_flowlet_map() {
        hash(local_metadata.flowlet_map_index, HashAlgorithm.crc16, (bit<13>)0, { hdr.ipv6.src_addr, hdr.ipv6.dst_addr,hdr.ipv6.next_hdr, hdr.tcp.src_port, hdr.tcp.dst_port,local_metadata.flowlet_id }, (bit<13>)8191);
        ecmp_flowlet_id_map.read(local_metadata.flowlet_id, (bit<32>)local_metadata.flowlet_map_index);
        local_metadata.flow_inter_packet_gap = (bit<48>)standard_metadata.ingress_global_timestamp;
        ecmp_flowlet_lasttime_map.read(local_metadata.flowlet_last_pkt_seen_time, (bit<32>)local_metadata.flowlet_map_index);
        local_metadata.flow_inter_packet_gap = local_metadata.flow_inter_packet_gap - local_metadata.flowlet_last_pkt_seen_time;
        ecmp_flowlet_lasttime_map.write((bit<32>)local_metadata.flowlet_map_index, standard_metadata.ingress_global_timestamp);
    }
    @name("update_flowlet_id") action update_flowlet_id() {
        local_metadata.flowlet_id = local_metadata.flowlet_id + 16w1;
        ecmp_flowlet_id_map.write((bit<32>)local_metadata.flowlet_map_index, (bit<16>)local_metadata.flowlet_id);
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
            //===================================================
            hdr.ipv6.dst_addr:          selector;
            hdr.ipv6.src_addr:          selector;
            hdr.ipv6.next_hdr:   selector;  //As we have modified the protcool headers according to our needs . we are using tempporary variable to store tcp protocol version to replicate
            //the exact behavior of ECMP
            local_metadata.l4_src_port: selector;
            local_metadata.l4_dst_port: selector;
            local_metadata.flowlet_id : selector;
        }
        actions = {
            set_upstream_egress_port;
        }
        implementation = upstream_path_selector;
        @name("upstream_routing_table_counter")
        counters = direct_counter(CounterType.packets_and_bytes);
    }
    apply {
        lookup_flowlet_map();
        if (local_metadata.flow_inter_packet_gap  > FLOWLET_INTER_PACKET_GAP_THRESHOLD)
             update_flowlet_id();
        upstream_routing_table.apply();
    }
}
#endif












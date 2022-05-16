
#include <core.p4>

#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"



control hula_load_balancing(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{

    @name("ecmp_flowlet_id_map") register<bit<16>>(32w8192) hula_flowlet_id_map;
    @name("ecmp_flowlet_lasttime_map") register<bit<48>>(32w8192) hula_flowlet_lasttime_map;
    @name("flowlet_last_used_port") register<bit<9>>(32w8192) flowlet_last_used_port;

    @name("hula_lookup_flowlet_map") action hula_lookup_flowlet_time_map() {
        hash(local_metadata.flowlet_map_index, HashAlgorithm.crc16, (bit<13>)0, { hdr.ipv6.src_addr, hdr.ipv6.dst_addr,hdr.ipv6.next_hdr, hdr.tcp.src_port, hdr.tcp.dst_port,local_metadata.flowlet_id }, (bit<13>)8191);
        local_metadata.flow_inter_packet_gap = (bit<48>)standard_metadata.ingress_global_timestamp;
        hula_flowlet_lasttime_map.read(local_metadata.flowlet_last_pkt_seen_time, (bit<32>)local_metadata.flowlet_map_index);
        local_metadata.flow_inter_packet_gap = local_metadata.flow_inter_packet_gap - local_metadata.flowlet_last_pkt_seen_time;
        hula_flowlet_lasttime_map.write((bit<32>)local_metadata.flowlet_map_index, standard_metadata.ingress_global_timestamp);
    }


    action use_old_port() {
        flowlet_last_used_port.read(local_metadata.flowlet_last_used_path,(bit<32>)local_metadata.flowlet_map_index);
        standard_metadata.egress_spec = local_metadata.flowlet_last_used_path;
        // Decrement TTL
        hdr.ipv6.hop_limit = hdr.ipv6.hop_limit - 1;
    }
    action hula_set_upstream_egress_port(port_num_t port_num) {
        standard_metadata.egress_spec = port_num;
        // Decrement TTL
        hdr.ipv6.hop_limit = hdr.ipv6.hop_limit - 1;
        flowlet_last_used_port.write((bit<32>)local_metadata.flowlet_map_index,(bit<9>)standard_metadata.egress_spec );
    }

    action hula_set_upstream_default_egress_port(port_num_t port_num) {
        standard_metadata.egress_spec = port_num;
        // Decrement TTL
        hdr.ipv6.hop_limit = hdr.ipv6.hop_limit - 1;
        flowlet_last_used_port.write((bit<32>)local_metadata.flowlet_map_index,(bit<9>)standard_metadata.egress_spec );
    }
   table hula_routing_table {
       key = {
            hdr.ipv6.dst_addr:          lpm;
       }
       actions = {
           hula_set_upstream_egress_port;
           @defaultonly hula_set_upstream_default_egress_port;
       }
   }

   apply {

       hula_lookup_flowlet_time_map();
       if (local_metadata.flow_inter_packet_gap  > FLOWLET_INTER_PACKET_GAP_THRESHOLD){
            hula_routing_table.apply();
        }else{
            use_old_port();
        }

   }


}












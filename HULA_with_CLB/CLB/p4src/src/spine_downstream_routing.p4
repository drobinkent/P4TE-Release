#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef SPINE_DOWNSTREAM_ROUTING
#define SPINE_DOWNSTREAM_ROUTING
control spine_downstream_routing(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{
   @name("host_egress_meter") direct_meter<bit<32>>(MeterType.bytes) host_egress_meter;


   action set_downstream_egress_port(port_num_t port_num,mac_addr_t dmac) {
          standard_metadata.egress_spec = port_num;
          hdr.ethernet.src_addr = hdr.ethernet.dst_addr;
          hdr.ethernet.dst_addr = dmac;
          // Decrement TTL
          hdr.ipv6.hop_limit = hdr.ipv6.hop_limit - 1;
          local_metadata.flag_hdr.downstream_routing_table_hit = true;


  }
   table downstream_routing_table {
         key = {
             hdr.ipv6.dst_addr:          lpm;

         }
         actions = {
             set_downstream_egress_port;
         }
         @name("downstream_routing_table")
         counters = direct_counter(CounterType.packets_and_bytes);
   }
   apply {
       downstream_routing_table.apply();

   }
}
#endif





#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef L2_TERNARY_PROCESSING
#define L2_TERNARY_PROCESSING
control l2_ternary_processing(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{
    // Drop action definition, shared by many tables. Hence we define it on top.
   action drop() {
       // Sets an architecture-specific metadata field to signal that the
       // packet should be dropped at the end of this pipeline.
       mark_to_drop(standard_metadata);
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
   apply {
        if(l2_ternary_table.apply().hit){
            exit;
        }

   }
}
#endif





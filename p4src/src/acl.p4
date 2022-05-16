#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef ACL_PROCESSING
#define ACL_PROCESSING
control acl_processing(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{
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
   apply {
        acl_table.apply();
   }
}
#endif





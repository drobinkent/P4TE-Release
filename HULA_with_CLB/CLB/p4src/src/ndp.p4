#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef NDP_PROCESSING
#define NDP_PROCESSING
control ndp_processing(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{
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
   apply {
        if (ndp_reply_table.apply().hit) {
            local_metadata.flag_hdr.do_l3_l2 = false;
            local_metadata.flag_hdr.is_pkt_toward_host = true;

        }else{
            local_metadata.flag_hdr.do_l3_l2 = true;
        }
   }
}
#endif





#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifdef LEAF_EGRESS_STATS
control leaf_egress_stats_table(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{
    @name("leaf_egress_meter") direct_meter<bit<32>>(MeterType.bytes) leaf_egress_meter;
    action monitor_leaf_outgoing_flow() {
        leaf_egress_meter.read(local_metadata.egress_traffic_color);
    }
    table leaf_egress_stats {
        key = {
              hdr.ipv6.dst_addr:          exact;
        //Currently this is just dst address based monitoring for leaf switches. Later we may add some othe field
        }
        actions = { monitor_leaf_outgoing_flow; }
        const default_action = monitor_leaf_outgoing_flow;
        meters = leaf_egress_meter;
    }
    apply {
        leaf_egress_stats.apply();
    }
}
#endif
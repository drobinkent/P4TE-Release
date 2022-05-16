#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifdef LEAF_INGRESS_STATS
control leaf_ingress_stats_table(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{
    @name("leaf_ingress_meter") direct_meter<bit<32>>(MeterType.bytes) leaf_ingress_meter;
    action monitor_leaf_incoming_flow() {
        leaf_ingress_meter.read(local_metadata.ingress_traffic_color);
    }
    table leaf_ingress_stats {
        key = {
              hdr.ipv6.src_addr:          exact;
        //Currently this is just src addre based monitoring for leaf switches. Later we may add some othe field
        }
        actions = { monitor_leaf_incoming_flow; }
        const default_action = monitor_leaf_incoming_flow;
        meters = leaf_ingress_meter;
    }
    apply {
        leaf_ingress_stats.apply();
    }
}
#endif
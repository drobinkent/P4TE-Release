#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef EGRESS_RATE_MONITOR
#define EGRESS_RATE_MONITOR
control egress_rate_monitor(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{
    @name("egress_meter") direct_meter<bit<32>>(MeterType.packets) egress_meter;
    action monitor_outgoing_flow() {
        egress_meter.read( local_metadata.egress_rate_event_hdr.egress_traffic_color);
        local_metadata.egress_rate_event_hdr.egress_rate_event_port =  standard_metadata.egress_port;
        bit<32> port_id = (bit<32>)standard_metadata.egress_port;

        local_metadata.egress_rate_event_hdr.egress_rate_event_port =  standard_metadata.egress_port ;
    }
    table egress_rate_monitor_table {
        key = {
              standard_metadata.egress_port : exact;
        //Currently this is just egress  port based monitoring for all
        // switches. Later we may add some othe field
        }
        actions = { monitor_outgoing_flow; }
        const default_action = monitor_outgoing_flow;
        meters = egress_meter;
    }
    apply {
        egress_rate_monitor_table.apply();
        if( local_metadata.egress_rate_event_hdr.egress_traffic_color  != local_metadata.temp) {
            local_metadata.flag_hdr.is_control_pkt_from_egr_queue_rate = true;
            local_metadata.egress_rate_event_hdr.event_src_type =  EVENT_ORIGINATOR_NEIGHBOUR_SWITCH; //TODO we are not sure about that. But seems okay.
            local_metadata.egress_rate_event_hdr.egress_rate_event_data = (bit<48> )EVENT_EGR_RATE_CHANGED;
            //log_msg("Egress queue rate  event. traffic color is {}", { local_metadata.egress_rate_event_hdr.egress_traffic_color});

        }
        // We basically do this false assignment step in init_packet. Addig extra else llop may require extra stage in RMT. So we are skipping that
        //else{
          //  local_metadata.flag_hdr.is_control_pkt_from_egr_queue_rate = false;
        //}
    }
}
#endif
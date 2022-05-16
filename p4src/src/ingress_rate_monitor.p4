/*#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef INGRESS_RATE_MONITOR
#define INGRESS_RATE_MONITOR
control ingress_rate_monitor(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{
    @name("ingress_meter") direct_meter<bit<32>>(MeterType.packets) ingress_meter;
    action monitor_incoming_flow() {
        ingress_meter.read( local_metadata.ingress_rate_event_hdr.ingress_traffic_color);
        //log_msg("Ingress traffic color is {}", {local_metadata.ingress_rate_event_hdr.ingress_traffic_color});
    }
    // action monitor_incoming_flow() {
      //      bit<32>    tempColor;
        //    ingress_meter.read( tempColor);
          //  //log_msg("Ingress traffic color is {}", {tempColor});
        //}

    table ingress_stats {
        key = {
              standard_metadata.ingress_port : exact;
        //Currently this is just ingress  port based monitoring for all
        // switches. Later we may add some othe field
        }
        actions = { monitor_incoming_flow; }
        //const default_action = monitor_incoming_flow;
        meters = ingress_meter;
    }

    apply{
        ingress_stats.apply();
        if( local_metadata.ingress_rate_event_hdr.ingress_traffic_color > 0) {
            local_metadata.flag_hdr.is_control_pkt_from_ing_queue_rate = true;
             local_metadata.ingress_rate_event_hdr.event_src_type =  EVENT_ORIGINATOR_LOCAL_SWITCH;
             //log_msg("Ingress queue rate  event. traffic color is {}", { local_metadata.ingress_rate_event_hdr.ingress_traffic_color});
        }
        // We basically do this false assignment step in init_packet. Addig extra else llop may require extra stage in RMT. So we are skipping that
        //else{
          //  local_metadata.flag_hdr.is_control_pkt_from_ing_queue_rate = false;
        //}
    }
}
#endif
*/


//================================= New version of Ingress rae monitor. Here instead of per port based monitoring, we will monitor agregated flow rate
//monitoring================

#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef INGRESS_RATE_MONITOR
#define INGRESS_RATE_MONITOR
control ingress_rate_monitor(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{
    @name("flow_type_based_ingress_meter_for_upstream") meter(MAX_FLOW_TYPES,MeterType.packets) flow_type_based_ingress_meter_for_upstream;
    @name("flow_type_based_ingress_meter_for_downstream") meter(MAX_FLOW_TYPES, MeterType.packets) flow_type_based_ingress_meter_for_downstream;

    action monitor_incoming_flow_based_on_flow_type_for_pkts_rcvd_from_upstream( bit<9> flow_type_based_meter_idx) {
        flow_type_based_ingress_meter_for_upstream.execute_meter((bit<32>)flow_type_based_meter_idx,  local_metadata.ingress_rate_event_hdr.ingress_traffic_color);
        local_metadata.is_pkt_rcvd_from_downstream = false;
        //log_msg("Ingress traffic color is {}", {local_metadata.ingress_rate_event_hdr.ingress_traffic_color});
        local_metadata.ingress_rate_event_hdr.ingress_rate_event_port =  standard_metadata.ingress_port;
        local_metadata.flag_hdr.is_packet_from_downstream_port = false;
        local_metadata.flag_hdr.is_packet_from_upstream_port = true;
    }
    action monitor_incoming_flow_based_on_flow_type_for_pkts_rcvd_from_downstream(bit<9> flow_type_based_meter_idx) {
        flow_type_based_ingress_meter_for_downstream.execute_meter((bit<32>)flow_type_based_meter_idx,  local_metadata.ingress_rate_event_hdr.ingress_traffic_color);
        local_metadata.is_pkt_rcvd_from_downstream = true;
        //log_msg("Ingress traffic color is {}", {local_metadata.ingress_rate_event_hdr.ingress_traffic_color});
        local_metadata.ingress_rate_event_hdr.ingress_rate_event_port = standard_metadata.ingress_port;
        local_metadata.flag_hdr.is_packet_from_downstream_port = true;
        local_metadata.flag_hdr.is_packet_from_upstream_port = false;
    }

    table flow_type_based_ingress_stats_table {
        key = {
            standard_metadata.ingress_port : exact;
            //Currently this is just ingress  port based monitoring for all
            // switches. Later we may add some othe field
            hdr.ipv6.traffic_class: exact ;
        }
        actions = {
            monitor_incoming_flow_based_on_flow_type_for_pkts_rcvd_from_upstream;
            monitor_incoming_flow_based_on_flow_type_for_pkts_rcvd_from_downstream;
        }
        //const default_action = monitor_incoming_flow;
    }

    apply{
        flow_type_based_ingress_stats_table.apply();
        if( local_metadata.ingress_rate_event_hdr.ingress_traffic_color > 0) {
            local_metadata.flag_hdr.is_control_pkt_from_ing_queue_rate = true;
             local_metadata.ingress_rate_event_hdr.event_src_type =  EVENT_ORIGINATOR_LOCAL_SWITCH;
             //TODO, we can move this if-else condition to route selection where we will check the ingress traffic color to select path
             //log_msg("Ingress queue rate  event. traffic color is {}", { local_metadata.ingress_rate_event_hdr.ingress_traffic_color});
        }
        // We basically do this false assignment step in init_packet. Addig extra else llop may require extra stage in RMT. So we are skipping that
        //else{
          //  local_metadata.flag_hdr.is_control_pkt_from_ing_queue_rate = false;
        //}
    }
}
#endif










#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"

//Here we will have range based tables to decide about the levels of a metrics. the actions parameter will contain 2 parameter. 1) corresponding level for given range 2) weight-- at this moment this is un used
//but at some point later we can implement an algorithm for giving weight to a path depending on their metrics level.

//instead of using this kind of table for division we can just use division. but we are ading these for future exapansion and for assigning some weight.
// Also we can use this for k-shortest path. for example: we can add another range field here. this can help us to find how to find which group will have how many members.
// also using this kind of table facillates exponential scale. without table such non linear scales can not be used

#ifndef  PATH_DELAY_METRICS_LEVEL_CALCULATOR
#define PATH_DELAY_METRICS_LEVEL_CALCULATOR
control path_delay_metrics_level_calculator(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{

    action set_delay_metrics_level(bit<8> delay_level, bit<8> weight ) {
        port_to_port_delay_value_map.write((bit<32>)hdr.p2p_feedback.port_id, (bit<48>)delay_level);
        port_to_port_delay_last_update_time_map.write((bit<32>)hdr.p2p_feedback.port_id, standard_metadata.ingress_global_timestamp);
    }
    table path_delay_metrics_level_calculator_table {
        key = {
            hdr.p2p_feedback.delay_event_data: range;
        }
        actions = {
            set_delay_metrics_level;
        }
        //default_action = set_delay_metrics_level;  WE do not want any default action here
    }



    apply {
        path_delay_metrics_level_calculator_table.apply();

    }

}
#endif




#ifndef  EGRESS_QUEUE_DEPTH_METRICS_LEVEL_CALCULATOR
#define EGRESS_QUEUE_DEPTH_METRICS_LEVEL_CALCULATOR
control egress_queue_depth_metrics_level_calculator(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{

    action set_queue_depth_metrics_level(bit<8> delay_level, bit<8> weight ) {
        // We can directly write to the port status. or save it in a different metadata variable. and write later.
        //
        port_to_port_delay_value_map.write((bit<32>)hdr.packet_in.path_delay_event_port, (bit<48>)delay_level);
        port_to_port_delay_last_update_time_map.write((bit<32>)hdr.packet_in.path_delay_event_port, standard_metadata.ingress_global_timestamp);
    }
    table queue_depth_metrics_level_calculator_table {
        key = {
            hdr.p2p_feedback.delay_event_data: range;
        }
        actions = {
            set_queue_depth_metrics_level;
        }
        //default_action = set_delay_metrics_level;  WE do not want any default action here
    }



    apply {
        queue_depth_metrics_level_calculator_table.apply();
    }

}
#endif

// We do not need level finding for queue rate, because it is already quantised by color. so only 2 tables are required. and each of them requires1 write. so in a single stage they can be
//allocated.

//  level setup -- leaf and spine
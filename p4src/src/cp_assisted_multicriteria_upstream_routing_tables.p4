#include <core.p4>






#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef CP_ASSISTED_MULTICRITERIA_UPSTREAM_ROUTING_TABLES
#define CP_ASSISTED_MULTICRITERIA_UPSTREAM_ROUTING__TABLES
control cp_assisted_multicriteria_upstream_routing_tables(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{

    //======================================== Table for slecting path with minimum delay ==========================================
    /*action delay_based_upstream_path_selector_action_without_param() {
        local_metadata.delay_based_path = 0;
        local_metadata.flag_hdr.found_path_delay_based_path = false;
    }
    action delay_based_upstream_path_selector_action_with_param(bit<9> port_num) {
        local_metadata.delay_based_path = port_num;
        local_metadata.flag_hdr.found_path_delay_based_path = true;
    }

    action_selector(HashAlgorithm.crc16, 32w128, 32w16) delay_based_upstream_path_selector;   //This have to be random  path selector or we need to add few selector
    table delay_based_upstream_path_table {
        key = {
            hdr.ipv6.dst_addr:          lpm;
            local_metadata.delay_value_range : range;
            local_metadata.minimum_group_members_requirement : range;
            //===================================================
            hdr.ipv6.dst_addr:          selector;
            hdr.ipv6.src_addr:          selector;
            hdr.ipv6.flow_label:        selector;
            hdr.ipv6.next_hdr:          selector;
            local_metadata.l4_src_port: selector;
            local_metadata.l4_dst_port: selector;
            standard_metadata.ingress_global_timestamp: selector;
        }
        actions = {
            delay_based_upstream_path_selector_action_without_param;
            delay_based_upstream_path_selector_action_with_param;
        }
        default_action = delay_based_upstream_path_selector_action_without_param;
        implementation = delay_based_upstream_path_selector;
        @name("delay_based_upstream_path_table_counter")
        counters = direct_counter(CounterType.packets_and_bytes);
    }*/



    //======================================== Table for slecting path with minimum egress queue depth ==========================================
    action egr_queue_depth_based_upstream_path_selector_action_without_param() {
        local_metadata.egr_queue_based_path = 0;
        local_metadata.flag_hdr.found_egr_queue_depth_based_path = false;

    }
    action egr_queue_depth_based_upstream_path_selector_action_with_param(bit<9> port_num) {
        local_metadata.egr_queue_based_path = port_num;
        local_metadata.flag_hdr.found_egr_queue_depth_based_path = true;
    }

    action_selector(HashAlgorithm.crc16, 32w128, 32w16) egr_queue_depth_based_upstream_path_selector;   //This have to be random  path selector
    table egr_queue_depth_based_upstream_path_table {
        key = {
            hdr.ipv6.dst_addr:          lpm;
            local_metadata.egr_queue_depth_value_range : range;
            local_metadata.minimum_group_members_requirement : range;
             //===================================================
            hdr.ipv6.dst_addr:          selector;
            hdr.ipv6.src_addr:          selector;
            hdr.ipv6.flow_label:        selector;
            hdr.ipv6.next_hdr:          selector;
            local_metadata.l4_src_port: selector;
            local_metadata.l4_dst_port: selector;
            standard_metadata.ingress_global_timestamp: selector;
        }
        actions = {
            egr_queue_depth_based_upstream_path_selector_action_without_param;
            egr_queue_depth_based_upstream_path_selector_action_with_param;
        }
        default_action = egr_queue_depth_based_upstream_path_selector_action_without_param;
        implementation = egr_queue_depth_based_upstream_path_selector;
        @name("egr_queue_depth_based_upstream_path_table_counter")
        counters = direct_counter(CounterType.packets_and_bytes);
    }




    //--------------------------------- Table for egress rate----------------------------------------
    // Rate is a measure of link capicity and utlilization. But queue depth includes buffer. so it is not a stright forward measurement for utilization.
    // if for a port queu rate is 10 pps, queue depth may be 15-100. Or may be more, queue rate is more instantinaours. and most importantly current meters only provide 3 color based feature. not
    // generic meter capability.
    //


     //======================================== Table for slecting path with minimum egress port rate ==========================================
    action egr_port_rate_based_upstream_path_selector_action_without_param() {
        local_metadata.egr_rate_based_path = 0;
        local_metadata.flag_hdr.found_egr_queue_rate_based_path = false;

    }
    action egr_port_rate_based_upstream_path_selector_action_with_param(bit<9> port_num) {
        local_metadata.egr_rate_based_path = port_num;
        local_metadata.flag_hdr.found_egr_queue_rate_based_path = true;
    }

    action_selector(HashAlgorithm.crc16, 32w128, 32w16) egr_port_rate_based_upstream_path_selector;   //This have to be random  path selector
    table egr_port_rate_based_upstream_path_table {
        key = {
            hdr.ipv6.dst_addr:          lpm;
            local_metadata.egr_port_rate_value_range : range;
            local_metadata.minimum_group_members_requirement : range;
             //===================================================
            hdr.ipv6.dst_addr:          selector;
            hdr.ipv6.src_addr:          selector;
            hdr.ipv6.flow_label:        selector;
            hdr.ipv6.next_hdr:          selector;
            local_metadata.l4_src_port: selector;
            local_metadata.l4_dst_port: selector;
            standard_metadata.ingress_global_timestamp: selector;
        }
        actions = {
            egr_port_rate_based_upstream_path_selector_action_without_param;
            egr_port_rate_based_upstream_path_selector_action_with_param;
        }
        default_action = egr_port_rate_based_upstream_path_selector_action_without_param;
        implementation = egr_port_rate_based_upstream_path_selector;
        @name("egr_port_rate_based_upstream_path_table_counter")
        counters = direct_counter(CounterType.packets_and_bytes);
    }


    apply {

        //delay_based_upstream_path_table.apply();
        egr_queue_depth_based_upstream_path_table.apply();
        local_metadata.egr_port_rate_value_range  = 1; //This is required to find the port with green color.
        egr_port_rate_based_upstream_path_table.apply();
        //log_msg("Delay based selected path  {}", {local_metadata.delay_based_path});
    }

}
#endif








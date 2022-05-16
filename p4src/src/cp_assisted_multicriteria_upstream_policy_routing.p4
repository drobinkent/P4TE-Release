#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef CP_ASSISTED_MULTICRITERIA_UPSTREAM_POLICY_ROUTING
#define CP_ASSISTED_MULTICRITERIA_UPSTREAM_POLICY_ROUTING
control cp_assisted_multicriteria_upstream_policy_routing(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{

    //======================================== Table for slecting path according to policy ==========================================
    @name("flowlet_id_map") register<bit<16>>(32w8192) flowlet_id_map;
    @name("flowlet_lasttime_map") register<bit<48>>(32w8192) flowlet_lasttime_map;
    @name("flowlet_last_used_port") register<bit<9>>(32w8192) flowlet_last_used_port;

    @name("lookup_flowlet_id_map") action lookup_flowlet_id_map() {
        hash(local_metadata.flowlet_map_index, HashAlgorithm.crc16, (bit<13>)0, { hdr.ipv6.src_addr, hdr.ipv6.dst_addr,  hdr.ipv6.flow_label, hdr.tcp.src_port, hdr.tcp.dst_port }, (bit<13>)8191);
        //flowlet_id_map.read(local_metadata.flowlet_id, (bit<32>)local_metadata.flowlet_map_index);
        local_metadata.flow_inter_packet_gap = (bit<48>)standard_metadata.ingress_global_timestamp;
        flowlet_lasttime_map.read(local_metadata.flowlet_last_pkt_seen_time, (bit<32>)local_metadata.flowlet_map_index);
        local_metadata.flow_inter_packet_gap = local_metadata.flow_inter_packet_gap - local_metadata.flowlet_last_pkt_seen_time;
        flowlet_lasttime_map.write((bit<32>)local_metadata.flowlet_map_index, standard_metadata.ingress_global_timestamp);
        //flowlet_last_used_port.read(local_metadata.flowlet_last_used_path,(bit<32>)local_metadata.flowlet_map_index);  //TODO We may not need thsi here
    }
    @name("update_flowlet_id") action update_flowlet_id_map() {
        //local_metadata.flowlet_id = local_metadata.flowlet_id + 16w1;
        //flowlet_id_map.write((bit<32>)local_metadata.flowlet_map_index, (bit<16>)local_metadata.flowlet_id);
        flowlet_last_used_port.write((bit<32>)local_metadata.flowlet_map_index,(bit<9>)standard_metadata.egress_spec );
    }
    action use_old_port() {
        flowlet_last_used_port.read(local_metadata.flowlet_last_used_path,(bit<32>)local_metadata.flowlet_map_index);
        standard_metadata.egress_spec = local_metadata.flowlet_last_used_path;
        // Decrement TTL
        hdr.ipv6.hop_limit = hdr.ipv6.hop_limit - 1;
    }
   /* action use_low_delay_port() {
        standard_metadata.egress_spec = local_metadata.delay_based_path;
        // Decrement TTL
        hdr.ipv6.hop_limit = hdr.ipv6.hop_limit - 1;
    }*/
    action use_low_egress_queue_depth_port() {
         standard_metadata.egress_spec = local_metadata.egr_queue_based_path ;
         // Decrement TTL
         hdr.ipv6.hop_limit = hdr.ipv6.hop_limit - 1;
     }
     action use_low_egress_queue_rate_port() {
          standard_metadata.egress_spec =local_metadata.egr_rate_based_path ;
          // Decrement TTL
          hdr.ipv6.hop_limit = hdr.ipv6.hop_limit - 1;
      }

    /*table policy_based_upstream_routing {
        key = {
            hdr.ipv6.traffic_class: exact ;
            local_metadata.ingress_queue_event_hdr.ingress_queue_event   :exact;
            local_metadata.ingress_rate_event_hdr.ingress_traffic_color  :exact;
            local_metadata.ingress_queue_event_hdr.ingress_queue_event    :exact;

        }
        actions = {
            use_old_port;
            //use_low_delay_port;
            use_low_egress_queue_depth_port;
        }
        default_action = use_old_port;
        //implementation = delay_based_upstream_path_selector;
        //@name("delay_based_upstream_path_table_counter")
        //counters = direct_counter(CounterType.packets_and_bytes);
    }*/


    apply {
        lookup_flowlet_id_map();
        // bit<48> last_used_path_previous_rate_update_time = 0;
        // egress_queue_rate_last_update_time_map.read(last_used_path_previous_rate_update_time, (bit<32>)local_metadata.flowlet_last_used_path);

        if ((hdr.ipv6.traffic_class == TRAFFIC_CLASS_HIGH_THROUGHPUT) || (hdr.ipv6.traffic_class == TRAFFIC_CLASS_HIGH_THROUGHPUT2)){ //Need to implement this.
            // use low queue rate port . assumption is that, we can use this port to send more amount of data
            if (local_metadata.flow_inter_packet_gap > FLOWLET_INTER_PACKET_GAP_THRESHOLD){
                  //Select the path according to flow type
                 bit<48> low_utilization_path_rate_status = 0;
                  egress_queue_rate_value_map.read(low_utilization_path_rate_status, (bit<32>)local_metadata.egr_rate_based_path);
                 if(low_utilization_path_rate_status == (bit<48>)GREEN ){
                    use_low_egress_queue_rate_port();
                 }else if(low_utilization_path_rate_status == (bit<48>)YELLOW ){ // now try to find a better path. here we will use low_e_q_Depth port
                     use_low_egress_queue_depth_port();
                 }else if((low_utilization_path_rate_status == (bit<48>)RED ) ){ // use safe rate port
                     use_low_egress_queue_depth_port();
                 }
                 //use_low_egress_queue_rate_port();
                 update_flowlet_id_map();
            }else{
                use_old_port();
                update_flowlet_id_map();
            }
        }else{
             if (local_metadata.flow_inter_packet_gap > FLOWLET_INTER_PACKET_GAP_THRESHOLD){
                   //Select the path according to flow type
                   bit<48> low_delay_path_rate_status = 0;
                   egress_queue_rate_value_map.read(low_delay_path_rate_status, (bit<32>)local_metadata.egr_queue_based_path);
                  if(low_delay_path_rate_status == (bit<48>)GREEN ){
                     use_low_egress_queue_depth_port();
                     //use_low_delay_port();
                  }
                  else if(low_delay_path_rate_status == (bit<48>)YELLOW ){ // now try to find a better path. here we will use low_e_q_Depth port
                      use_low_egress_queue_rate_port();
                  }else if((low_delay_path_rate_status == (bit<48>)RED ) ){ // use safe rate port
                      use_low_egress_queue_rate_port();
                  }
                  update_flowlet_id_map();
             }else{
                 use_old_port();
                 update_flowlet_id_map();
             }
         }

    }

}
#endif



//Heuristic behind our path selection for low_delay_port
// Heuritic `1 : we reverify a packet because we hope that, even a slight reordering can be handled by the tcp stack. as those stack deploy re-ordering capability in the host stack.
// also DCn env is pretty fast. so delay variation can be handled by the stack
// if an egress port rate is green then it means we can pass it through the old port.
// if an egress port rate is YELLOW, then it means there are already a lot of traffic through this port, try to find some other port.

//when we see an egress port is rate !GREEN that means some other flow have seen congestion on that port. so we reroute the traffic





// A concpet: Let for each port if for traffic class a we see congestion we circulate this info to info and there we keep track info of this.
// If a flow of same type comes and can not find a safe port it will retoute traffic to other port. the taarget is to find whther a flow is
// .hampering the safe rate of other types of traffic. if a flow hampers the safe rate of other traffic , then we need to reroute the flow. if
// no suitable uncongested path is found then reduce the rate.
//Otherwise the flow can use the port and send more and more traffic. ---------- this is the heurusitic behuind class based traffic control


// when we have no class based rate control in egeress, then we onyl consider if the port is congested. YELLOW rate shows the maximum upper safe limit.
// it also gives the upper limit on link utilization. RED rate is a buffer to handle burst. bcz we can not ensure a port will be always within safe rate.
//


//We are not checking the egress_queue_rate_last_update_time_map of a port bcz, assume a port's rate info is not updated in the ingress stage,
// Then sending a packet will change it's status and the info will be reflected. To save memeory read write we use this opprtunisitic decision
/*
#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef CP_ASSISTED_MULTICRITERIA_UPSTREAM_POLICY_ROUTING
#define CP_ASSISTED_MULTICRITERIA_UPSTREAM_POLICY_ROUTING
control cp_assisted_multicriteria_upstream_policy_routing(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{

    //======================================== Table for slecting path according to policy ==========================================
    @name("flowlet_id_map") register<bit<16>>(32w8192) flowlet_id_map;
    @name("flowlet_lasttime_map") register<bit<48>>(32w8192) flowlet_lasttime_map;
    @name("flowlet_last_used_port") register<bit<9>>(32w8192) flowlet_last_used_port;

    @name("lookup_flowlet_id_map") action lookup_flowlet_id_map() {
        hash(local_metadata.flowlet_map_index, HashAlgorithm.crc16, (bit<13>)0, { hdr.ipv6.src_addr, hdr.ipv6.dst_addr,  hdr.ipv6.flow_label, hdr.tcp.src_port, hdr.tcp.dst_port }, (bit<13>)8191);
        //flowlet_id_map.read(local_metadata.flowlet_id, (bit<32>)local_metadata.flowlet_map_index);
        local_metadata.flow_inter_packet_gap = (bit<48>)standard_metadata.ingress_global_timestamp;
        flowlet_lasttime_map.read(local_metadata.flowlet_last_pkt_seen_time, (bit<32>)local_metadata.flowlet_map_index);
        local_metadata.flow_inter_packet_gap = local_metadata.flow_inter_packet_gap - local_metadata.flowlet_last_pkt_seen_time;
        flowlet_lasttime_map.write((bit<32>)local_metadata.flowlet_map_index, standard_metadata.ingress_global_timestamp);
        flowlet_last_used_port.read(local_metadata.flowlet_last_used_path,(bit<32>)local_metadata.flowlet_map_index);  //TODO We may not need thsi here
    }
    @name("update_flowlet_id") action update_flowlet_id_map() {
        //local_metadata.flowlet_id = local_metadata.flowlet_id + 16w1;
        //flowlet_id_map.write((bit<32>)local_metadata.flowlet_map_index, (bit<16>)local_metadata.flowlet_id);
        flowlet_last_used_port.write((bit<32>)local_metadata.flowlet_map_index,(bit<9>)standard_metadata.egress_spec );
    }
    action use_old_port() {
        standard_metadata.egress_spec = local_metadata.flowlet_last_used_path;
        // Decrement TTL
        hdr.ipv6.hop_limit = hdr.ipv6.hop_limit - 1;
    }
    action use_low_delay_port() {
        standard_metadata.egress_spec = local_metadata.delay_based_path;
        // Decrement TTL
        hdr.ipv6.hop_limit = hdr.ipv6.hop_limit - 1;
    }
    action use_low_egress_queue_depth_port() {
         standard_metadata.egress_spec = local_metadata.egr_queue_based_path ;
         // Decrement TTL
         hdr.ipv6.hop_limit = hdr.ipv6.hop_limit - 1;
     }
     action use_low_egress_queue_rate_port() {
          standard_metadata.egress_spec =local_metadata.egr_rate_based_path ;
          // Decrement TTL
          hdr.ipv6.hop_limit = hdr.ipv6.hop_limit - 1;
      }

    table policy_based_upstream_routing {
        key = {
            hdr.ipv6.traffic_class: exact ;
            local_metadata.ingress_queue_event_hdr.ingress_queue_event   :exact;
            local_metadata.ingress_rate_event_hdr.ingress_traffic_color  :exact;
            local_metadata.ingress_queue_event_hdr.ingress_queue_event    :exact;

        }
        actions = {
            use_old_port;
            use_low_delay_port;
            use_low_egress_queue_depth_port;
        }
        default_action = use_old_port;
        //implementation = delay_based_upstream_path_selector;
        //@name("delay_based_upstream_path_table_counter")
        //counters = direct_counter(CounterType.packets_and_bytes);
    }


    apply {
        lookup_flowlet_id_map();
        // bit<48> last_used_path_previous_rate_update_time = 0;
        // egress_queue_rate_last_update_time_map.read(last_used_path_previous_rate_update_time, (bit<32>)local_metadata.flowlet_last_used_path);
        bit<48> low_delay_path_rate_status = 0;
        egress_queue_rate_value_map.read(low_delay_path_rate_status, (bit<32>)local_metadata.egr_queue_based_path);
        if ((hdr.ipv6.traffic_class == TRAFFIC_CLASS_LOW_DELAY) ||  (hdr.ipv6.traffic_class == TRAFFIC_CLASS_HIGH_THROUGHPUT)){
            if (local_metadata.flow_inter_packet_gap > FLOWLET_INTER_PACKET_GAP_THRESHOLD){
                if(low_delay_path_rate_status == (bit<48>)GREEN ){
                    //use_low_egress_queue_depth_port();
                    use_low_egress_queue_depth_port();
                 }else if(low_delay_path_rate_status >= (bit<48>)YELLOW ){ // now try to find a better path. here we will use low_e_q_Depth port
                     use_low_egress_queue_rate_port();
                 }
                 update_flowlet_id_map();
            }else{
                 use_old_port();
                 update_flowlet_id_map();
             }
        }
        else{

            local_metadata.flag_hdr.found_egr_queue_depth_based_path = false;
            local_metadata.flag_hdr.found_egr_queue_rate_based_path = false;
            local_metadata.flag_hdr.found_path_delay_based_path = false;
            //use_low_delay_port(); //for all other traffic try to reduce FCT
            //this will force to use ECMP for all other traffic
        }

    }

}
#endif
*/

//Heuristic behind our path selection for low_delay_port
// Heuritic `1 : we reverify a packet because we hope that, even a slight reordering can be handled by the tcp stack. as those stack deploy re-ordering capability in the host stack.
// also DCn env is pretty fast. so delay variation can be handled by the stack
// if an egress port rate is green then it means we can pass it through the old port.
// if an egress port rate is YELLOW, then it means there are already a lot of traffic through this port, try to find some other port.

//when we see an egress port is rate !GREEN that means some other flow have seen congestion on that port. so we reroute the traffic





// A concpet: Let for each port if for traffic class a we see congestion we circulate this info to info and there we keep track info of this.
// If a flow of same type comes and can not find a safe port it will retoute traffic to other port. the taarget is to find whther a flow is
// .hampering the safe rate of other types of traffic. if a flow hampers the safe rate of other traffic , then we need to reroute the flow. if
// no suitable uncongested path is found then reduce the rate.
//Otherwise the flow can use the port and send more and more traffic. ---------- this is the heurusitic behuind class based traffic control


// when we have no class based rate control in egeress, then we onyl consider if the port is congested. YELLOW rate shows the maximum upper safe limit.
// it also gives the upper limit on link utilization. RED rate is a buffer to handle burst. bcz we can not ensure a port will be always within safe rate.
//


//We are not checking the egress_queue_rate_last_update_time_map of a port bcz, assume a port's rate info is not updated in the ingress stage,
// Then sending a packet will change it's status and the info will be reflected. To save memeory read write we use this opprtunisitic decision


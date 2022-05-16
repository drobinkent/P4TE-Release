//This file contains all the actions related to hop by hop delay statistics and exchange and relevant processing.


#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef LEAF_RATE_CONTROL_PROCESSOR
#define LEAF_RATE_CONTROL_PROCESSOR
control leaf_rate_control_processor(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{

    @name("flowlet_id_to_seq_number_of_last_rate_control_action_map") register<bit<32>>(8192) flowlet_id_to_seq_number_of_last_rate_control_action_map;
    apply{
    // if flowlet calculation is not done earlier do here. else use old flowlet id
    // If earlier in the pipeline we have not calculated the flowlet_id calculate it here using
    //hash(local_metadata.flowlet_map_index, HashAlgorithm.crc16, (bit<13>)0, { hdr.ipv6.src_addr, hdr.ipv6.dst_addr, hdr.ipv6.flow_label}, (bit<13>)8191);

        //===== This part is for identifying flow condition, whther this flow neds flow control or not. One problem here is that, after the FIN packet there may be more packet of the flow
        // for details look at this https://www.geeksforgeeks.org/tcp-connection-termination/?ref=lbp . The point if we want exact tracking of TCP, we have to replicate the TCP state machine here
        // At this moment we are not focusing in the exact dynamics of tcp. Later we may add that part

        if(hdr.tcp.syn_control_flag == FLAG_1){ //first pkt of the flow
            flowlet_id_to_seq_number_of_last_rate_control_action_map.write((bit<32>)(local_metadata.flowlet_map_index), hdr.tcp.seq_no); // This is the initial seq_no of the tcp connection
            //log_msg("Entered a flow into rate control map");
            hdr.mdn_int.rate_control_event = RATE_CONTROL_EVENT_ALREADY_APPLIED;
        }else if (hdr.tcp.fin_control_flag == FLAG_1 )  {
            flowlet_id_to_seq_number_of_last_rate_control_action_map.write((bit<32>)local_metadata.flowlet_map_index, 0); // This is the last seq_no of the tcp connection. so clearing it
            //log_msg("cleared a flow from rate control map");
        } // TODO we may add a logic for ack packets. if a packet is ack packet then we might skip it. but if there is data then we can not skip it
        else {//if ((hdr.mdn_int.rate_control_event == RATE_CONTROL_EVENT_NOT_YET_APPLIED) ){
            //bit<32>  last_seq_no_with_rate_control = 0 ;
            flowlet_id_to_seq_number_of_last_rate_control_action_map.read(hdr.mdn_int.last_seq_no_with_rate_control, (bit<32>)local_metadata.flowlet_map_index);
            if(hdr.mdn_int.last_seq_no_with_rate_control + SEQ_NUMBER_THRESHOLD_FOR_RATE_CONTROL < hdr.tcp.seq_no){
                // Only in this case we need to do rate control
                hdr.mdn_int.rate_control_allowed_for_the_tcp_flow = RATE_CONTROL_ALLOWED_FOR_THE_FLOW; //else rate control is not allowed and the vlaue is written in init_pkt of leaf.p4

            }
        }

        //========This part is for actual flow control=================
        //=If the flow is allowed to impose rate control and it's not an fake ack packet then we will generate fake ack.
        // Otherwise if this packet is a fake ack packet and we create another fake ack for this packet then this will create a repple effect. which we do not want
        // TODO : implement these logic using a table
        if (hdr.tcp.isValid() && (hdr.mdn_int.rate_control_allowed_for_the_tcp_flow == RATE_CONTROL_ALLOWED_FOR_THE_FLOW) &&
                (hdr.mdn_int.rate_control_event != RATE_CONTROL_EVENT_ALREADY_APPLIED )){
                //This condition means, we are going to apply rate control in this switch. On what condition we decide to do rate control. Implement the logic here. Our taret is to add this logic through a table for easier expansion
            flowlet_id_to_seq_number_of_last_rate_control_action_map.write((bit<32>)local_metadata.flowlet_map_index, hdr.tcp.seq_no); //TODO : we have to make sure that we are calling the flowlet computtion mandatoryly
             if ((local_metadata.egress_rate_event_hdr.egress_traffic_color >= (bit<32>) RED )  && (local_metadata.ingress_rate_event_hdr.ingress_traffic_color>= (bit<32>) RED) ) {
                 hdr.mdn_int.rate_control_event = RATE_DECREASE_EVENT_NEED_TO_BE_APPLIED_IN_THIS_SWITCH ;
                 //hdr.ipv6.ecn = 3; //mark congestion occured

            }
            else if ((local_metadata.egress_rate_event_hdr.egress_traffic_color <= (bit<32>) YELLOW )  && (local_metadata.ingress_rate_event_hdr.ingress_traffic_color< (bit<32>) RED) ) {
               hdr.mdn_int.rate_control_event =RATE_INCREASE_EVENT_NEED_TO_BE_APPLIED_IN_THIS_SWITCH ;

            }

            //log_msg("Updated a flow into rate control map");
        }else if ( hdr.tcp.isValid() && hdr.mdn_int.isValid() && (hdr.tcp.ack_control_flag == FLAG_1 )  && (hdr.mdn_int.rate_control_event  == RATE_CONTROL_EVENT_ALREADY_APPLIED)){
            // This means this is a fake ack generated by some other swithc. Just forward the packet and update the register
            flowlet_id_to_seq_number_of_last_rate_control_action_map.write((bit<32>)local_metadata.flowlet_map_index, hdr.tcp.seq_no); //TODO : we have to make sure that we are calling the flowlet computtion mandatoryly
            //log_msg(" A pkt is marked with fake ack rcvd in this leaf switch");
        }else{
            //log_msg("Unhandled control branch in leaf rate control");
        }
    }

}
#endif





#ifndef SPINE_RATE_CONTROL_PROCESSOR
#define SPINE_RATE_CONTROL_PROCESSOR
control spine_rate_control_processor(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{

    apply{
    //========This part is for actual flow control=================
        //=If the flow is allowed to impose rate control and it's not an fake ack packet then we will generate fake ack.
        // Otherwise if this packet is a fake ack packet and we create another fake ack for this packet then this will create a repple effect. which we do not want
        // TODO : implement these logic using a table
        if (hdr.tcp.isValid() &&  (hdr.mdn_int.rate_control_allowed_for_the_tcp_flow == RATE_CONTROL_ALLOWED_FOR_THE_FLOW) && (hdr.mdn_int.rate_control_event != RATE_CONTROL_EVENT_ALREADY_APPLIED )){
                //This condition means, we are going to apply rate control in this switch. On what condition we decide to do rate control. Implement the logic here. Our taret is to add this logic through a table for easier expansion
            //flowlet_id_to_seq_number_of_last_rate_control_action_map.write(local_metadata.flowlet_map_index, hdr.tcp.seq_no); //TODO : we have to make sure that we are calling the flowlet computtion mandatoryly
            if ((local_metadata.egress_rate_event_hdr.egress_traffic_color >= (bit<32>) RED )  && (local_metadata.ingress_rate_event_hdr.ingress_traffic_color>= (bit<32>) RED) ) {
                 hdr.mdn_int.rate_control_event =RATE_DECREASE_EVENT_NEED_TO_BE_APPLIED_IN_THIS_SWITCH ;
                 //hdr.ipv6.ecn = 3; //mark congestion occured

            }else if ((local_metadata.egress_rate_event_hdr.egress_traffic_color <= (bit<32>) YELLOW )  && (local_metadata.ingress_rate_event_hdr.ingress_traffic_color < (bit<32>) RED) ) {
               hdr.mdn_int.rate_control_event =RATE_INCREASE_EVENT_NEED_TO_BE_APPLIED_IN_THIS_SWITCH ;

            }


        }else if ( hdr.tcp.isValid() &&  hdr.mdn_int.isValid() && (hdr.tcp.ack_control_flag == FLAG_1 )  && (hdr.mdn_int.rate_control_event  == RATE_CONTROL_EVENT_ALREADY_APPLIED)){
            //Nothing is need to be done here
        }else{
            //log_msg("Unhandled control branch in spine switch rate control");
        }
    }

}
#endif




//need to check if   hdr.mdn_int.rate_control_event ==RATE_CONTROL_EVENT_NEED_TO_BE_APPLIED_IN_THIS_SWITCH then we will clone the packet to the ingress port
  //  IS_CONTROL_PKT_TO_NEIGHBOUR macro te option add korte hobe
//and in the cloned version of the packet we will set  hdr.mdn_int.rate_control_event ==RATE_CONTROL_EVENT_ALREADY_APPLIED and forward the packet.


//policy routing  er logic ekta table use korbo
//rate control er logic ekta table use korbo -- eta diye scheduling o korbo.

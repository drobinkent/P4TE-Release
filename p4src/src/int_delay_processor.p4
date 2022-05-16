//This file contains all the actions related to hop by hop delay statistics and exchange and relevant processing.


#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef INT_DELAY_PROC
#define INT_DELAY_PROC
control int_delay_processor(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{
    register<timestamp_t>(MAX_PORTS_IN_SWITCH) path_avg_delay_registers;  //Think about keeping 2 dfrnt value for in pod and outside of pod network
    register<timestamp_t>(MAX_PORTS_IN_SWITCH) path_last_updated_delay_registers;  //Think about keeping 2 dfrnt value for in pod and outside of pod network
    register<timestamp_t>(MAX_PORTS_IN_SWITCH) time_of_last_delay_update; //WE are not using this. But this can be used for a threshold time to decide whther we want to generate evnet or not. This
    //Can be used for controlling the frequency of event generated

    apply{
    
    //Assumption: local_metadata.delay_info_hdr.setValid(); is done in some previous step. Which we are doing in the start of ingress processsing. Otherwise
    //Values stored in this header struct will not be preserved

        bit<48> old_avg_delay = 0;
        bit<48> last_updated_avg_delay = 0;
        bit<32> port_id = (bit<32>)standard_metadata.ingress_port;
        path_avg_delay_registers.read(old_avg_delay, port_id);
        path_last_updated_delay_registers.read(last_updated_avg_delay, port_id);
        bit<48> delay_for_this_pkt = standard_metadata.ingress_global_timestamp - hdr.mdn_int.src_enq_timestamp;
        old_avg_delay = old_avg_delay >>2;
        delay_for_this_pkt = delay_for_this_pkt >>2 ; //at this moment we are doing .5 weight to old and .5 to current delay value
        delay_for_this_pkt = old_avg_delay+ delay_for_this_pkt;
        path_avg_delay_registers.write(port_id, delay_for_this_pkt );
        //log_msg("Packet's standard_metadata.ingress_global_timestamp and hdr.mdn_int.src_enq_timestamp are {} {}", {standard_metadata.ingress_global_timestamp , hdr.mdn_int.src_enq_timestamp} );
        local_metadata.delay_info_hdr.path_delay_event_port = standard_metadata.ingress_port;
        if(delay_for_this_pkt >= (last_updated_avg_delay + PATH_DELAY_THRESHOLD)){
            //This means thsi packet  has seen increased delay through this port.  we need to report it io control plane.
            //Mark this situatin in mdn_int header. When the packet will be seen as marked in hedaer a packet in will be generated  and sent to CP
            local_metadata.delay_info_hdr.path_delay_event_type = EVENT_PATH_DELAY_INCREASED;
            local_metadata.delay_info_hdr.event_src_type =  EVENT_ORIGINATOR_NEIGHBOUR_SWITCH;  //This packet will be sent to neighbour switch. For them the event originator is neighbour switch
            local_metadata.delay_info_hdr.path_delay_event_data = delay_for_this_pkt;
            local_metadata.delay_info_hdr.dst_addr = hdr.ipv6.dst_addr;
            local_metadata.flag_hdr.is_control_pkt_from_delay_proc = true;
            path_last_updated_delay_registers.write(port_id, delay_for_this_pkt);
            //clone3(CloneType.I2E, (bit<32>)(standard_metadata.ingress_port), {standard_metadata, local_metadata});
            //log_msg("Inside int_delay_processor delay increase.path_delay_event_type = {}",{ local_metadata.delay_info_hdr.path_delay_event_type});
        }else if(delay_for_this_pkt <= (last_updated_avg_delay - PATH_DELAY_THRESHOLD)){
            local_metadata.delay_info_hdr.path_delay_event_type = EVENT_PATH_DELAY_DECREASED;
            local_metadata.delay_info_hdr.event_src_type =  EVENT_ORIGINATOR_NEIGHBOUR_SWITCH;  //This packet will be sent to neighbour switch. For them the event originator is neighbour switch
            local_metadata.delay_info_hdr.path_delay_event_data = delay_for_this_pkt;
            local_metadata.delay_info_hdr.dst_addr = hdr.ipv6.dst_addr;
            path_last_updated_delay_registers.write(port_id, delay_for_this_pkt );
            local_metadata.flag_hdr.is_control_pkt_from_delay_proc = true;
            //clone3(CloneType.I2E, (bit<32>)(standard_metadata.ingress_port), {standard_metadata, local_metadata});
            //log_msg("Inside int_delay_processor delay decreased.path_delay_event_type = {}",{ local_metadata.delay_info_hdr.path_delay_event_type});
        }
        //    void write(in bit<32> index, in T value);

    ////log_msg("Delay processing completed", standard_metadata);
    //After all processing is done , now we will  set the mdn_int_src_enq_timestamp  in the packet for next hop
    }

}
#endif





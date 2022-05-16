//This file contains all the actions related to hop by hop delay statistics and exchange and relevant processing.


#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef EG_QUEUE_DEPTH_PROCESSOR
#define EG_QUEUE_DEPTH_PROCESSOR
control egress_queue_depth_monitor(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{

    register<bit<19>>(MAX_PORTS_IN_SWITCH) port_last_updated_egress_queue_avg_depth;


    apply{
             //This section is for egress queue depth buildup checking. Rememeber, only egress queueu can not control a flow. Because
            //egress queueu only checkes totoal flow in a egress port. If 2 application sends data on same port of a switch then over the egress queue depth we need per flow
            //Rate control.
        {
            #ifdef ECN_ENABLED
            //log_msg("ECN enabled");
            if (standard_metadata.enq_qdepth >= ECN_THRESHOLD){
                hdr.ipv6.ecn = 3;
            }
            #else
            //bit<19> old_deq_depth = 0;
            bit<32> port_id = (bit<32>)standard_metadata.egress_spec;
            bit<19> last_updated_deq_depth = 0;
            port_last_updated_egress_queue_avg_depth.read(last_updated_deq_depth, port_id);
            local_metadata.egress_queue_event_hdr.egress_queue_event_port =  standard_metadata.egress_port;; //this is common for all kind of evnets. so setting in only one place
            if(standard_metadata.deq_qdepth >= (last_updated_deq_depth + EGRESS_QUEUE_DEPTH_THRESHOLD)){
                //This means this packet  has seen increased delay through this port.  we need to report it io control plane.
                //MNArk this situatin in standard_metadata header. When the packet will be seen as marked in hedaer a packet in will be generated  and sent to CP
                local_metadata.egress_queue_event_hdr.event_src_type =  EVENT_ORIGINATOR_LOCAL_SWITCH;
                local_metadata.egress_queue_event_hdr.egress_queue_event = EVENT_EGR_QUEUE_INCREASED;
                local_metadata.egress_queue_event_hdr.egress_queue_event_data = (bit<48>)standard_metadata.deq_qdepth;
                port_last_updated_egress_queue_avg_depth.write(port_id, standard_metadata.deq_qdepth);
                local_metadata.flag_hdr.is_control_pkt_from_egr_queue_depth = true;
                //log_msg("Egress dequeue depth increase event. old queue depth {} new queue depth {}", {last_updated_deq_depth, standard_metadata.deq_qdepth});

            }else if(standard_metadata.deq_qdepth < (last_updated_deq_depth - EGRESS_QUEUE_DEPTH_THRESHOLD)){
                local_metadata.egress_queue_event_hdr.event_src_type =  EVENT_ORIGINATOR_LOCAL_SWITCH;
                local_metadata.egress_queue_event_hdr.egress_queue_event = EVENT_EGR_QUEUE_DECREASED;
                local_metadata.egress_queue_event_hdr.egress_queue_event_data = (bit<48>) standard_metadata.deq_qdepth;
                port_last_updated_egress_queue_avg_depth.write(port_id, standard_metadata.deq_qdepth);
                local_metadata.flag_hdr.is_control_pkt_from_egr_queue_depth = true;
                //log_msg("Egress dequeue depth decrease event. old queue depth {} new queue depth {}", {last_updated_deq_depth, standard_metadata.deq_qdepth});
            }else{
                //Calculate weighted average here for the path
                local_metadata.egress_queue_event_hdr.egress_queue_event = EVENT_EGR_QUEUE_UNCHANGED;
                //old_deq_depth = old_deq_depth >>2;
                //bit<19> temp_queue_depth  = standard_metadata.deq_qdepth;
                //temp_queue_depth = temp_queue_depth >>2 ; //at this moment we are doing .5 weight to old and .5 to current delay value
                //temp_queue_depth = old_deq_depth + temp_queue_depth;
                local_metadata.flag_hdr.is_control_pkt_from_egr_queue_depth = false;
            }

            #endif
        }
    }

}
#endif





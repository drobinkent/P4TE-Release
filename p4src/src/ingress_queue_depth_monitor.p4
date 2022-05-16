//This file contains all the actions related to hop by hop delay statistics and exchange and relevant processing.


#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef ING_QUEUE_DEPTH_MONITOR
#define ING_QUEUE_DEPTH_MONITOR
control ingress_queue_depth_monitor(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{

    register<bit<19>>(MAX_PORTS_IN_SWITCH) port_ingress_queue_avg_depth;
    register<bit<19>>(MAX_PORTS_IN_SWITCH) port_last_updated_ingress_queue_avg_depth;


    apply{
         //This section is for ingress queue depth buildup checking. Rememeber, only ingress queueu can not control a flow. Because
                //Ingress queueu only checkes totoal flow in a ingress port. If 2 application sends data on same port of a switch then over the ingress queue depth we need per flow
                //Rate control.
        {
            bit<19> old_enq_depth = 0;
            bit<32> port_id = (bit<32>)standard_metadata.ingress_port;
            bit<19> last_updated_enq_depth = 0;
            port_ingress_queue_avg_depth.read(old_enq_depth, port_id);
            port_last_updated_ingress_queue_avg_depth.read(last_updated_enq_depth, port_id);
            local_metadata.ingress_queue_event_hdr.ingress_queue_event_port =  standard_metadata.ingress_port; //this is common for all kind of evnets. so setting in only one place
            if(standard_metadata.enq_qdepth >= (last_updated_enq_depth + INGRESS_QUEUE_DEPTH_THRESHOLD)){
                //This means thsi packet  has seen increased delay through this port.  we need to report it io control plane.
                //MNArk this situatin in standard_metadata header. When the packet will be seen as marked in hedaer a packet in will be generated  and sent to CP
                local_metadata.ingress_queue_event_hdr.event_src_type =  EVENT_ORIGINATOR_LOCAL_SWITCH;
                local_metadata.ingress_queue_event_hdr.ingress_queue_event = EVENT_ING_QUEUE_INCREASED;
                local_metadata.ingress_queue_event_hdr.ingress_queue_event_data = (bit<48>)standard_metadata.enq_qdepth;
                port_last_updated_ingress_queue_avg_depth.write(port_id, standard_metadata.enq_qdepth);
                local_metadata.flag_hdr.is_control_pkt_from_ing_queue_depth = true;
                //log_msg("Ingress queue depth increase event. old queue depth {} new queue depth {}", {last_updated_enq_depth, standard_metadata.enq_qdepth});
            }else if(standard_metadata.enq_qdepth <= (last_updated_enq_depth - INGRESS_QUEUE_DEPTH_THRESHOLD)){
                local_metadata.ingress_queue_event_hdr.event_src_type =  EVENT_ORIGINATOR_LOCAL_SWITCH;
                local_metadata.ingress_queue_event_hdr.ingress_queue_event = EVENT_ING_QUEUE_DECREASED;
                local_metadata.ingress_queue_event_hdr.ingress_queue_event_data = (bit<48>) standard_metadata.enq_qdepth;
                port_last_updated_ingress_queue_avg_depth.write(port_id, standard_metadata.enq_qdepth);
                local_metadata.flag_hdr.is_control_pkt_from_ing_queue_depth = true;
                //log_msg("Ingress queue depth decrease event. old queue depth {} new queue depth {}", {last_updated_enq_depth, standard_metadata.enq_qdepth});
            }else{
                //Calculate weighted average here for the path
                local_metadata.ingress_queue_event_hdr.ingress_queue_event =EVENT_ING_QUEUE_UNCHANGED;
                old_enq_depth = old_enq_depth >>2;
                bit<19> temp_queue_depth  = standard_metadata.enq_qdepth;
                temp_queue_depth = temp_queue_depth >>2 ; //at this moment we are doing .5 weight to old and .5 to current delay value
                temp_queue_depth = old_enq_depth + temp_queue_depth;
                local_metadata.flag_hdr.is_control_pkt_from_ing_queue_depth = false;

            }
            //    void write(in bit<32> index, in T value);
            port_ingress_queue_avg_depth.write(port_id, standard_metadata.enq_qdepth );
        }
    }

}
#endif





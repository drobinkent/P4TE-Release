#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifdef ENABLE_DEBUG_TABLES
    control debug_std_meta(inout parsed_headers_t    hdr,inout local_metadata_t    local_metadata,
                           inout standard_metadata_t standard_metadata)
    {
        table dbg_table {
            key = {
                // This is a complete list of fields inside of the struct
                // standard_metadata_t as of the 2018-Sep-01 version of
                // p4c in the file p4c/p4include/v1model.p4.

                // parser_error is commented out because the p4c back end
                // for bmv2 as of that date gives an error if you include
                // a field of type 'error' in a table key.
                standard_metadata.ingress_port : exact;
                standard_metadata.egress_spec : exact;
                standard_metadata.egress_port : exact;
                standard_metadata.packet_length : exact;
                standard_metadata.enq_timestamp : exact;
                standard_metadata.enq_qdepth : exact;
                standard_metadata.deq_timedelta : exact;
                standard_metadata.deq_qdepth : exact;
                standard_metadata.ingress_global_timestamp : exact;
                standard_metadata.egress_global_timestamp : exact;
                standard_metadata.mcast_grp : exact;
                standard_metadata.egress_rid : exact;
                standard_metadata.checksum_error : exact;
                //standard_metadata.parser_error : exact;
                //standard_metadata.qid : exact;
                standard_metadata.instance_type:exact;
                standard_metadata.packet_length : exact;
                standard_metadata.priority:exact;
                //all local metadata


                local_metadata.l4_src_port: exact;
                local_metadata.l4_dst_port: exact;
                local_metadata.is_multicast: exact;

                local_metadata.flag_hdr.is_control_pkt_from_delay_proc: exact;
                local_metadata.flag_hdr.is_control_pkt_from_ing_queue_rate: exact;
                local_metadata.flag_hdr.is_control_pkt_from_ing_queue_depth: exact;
                local_metadata.flag_hdr.is_control_pkt_from_egr_queue_depth: exact;
                local_metadata.flag_hdr.do_l3_l2: exact;
                local_metadata.flag_hdr.my_station_table_hit: exact;
                local_metadata.flag_hdr.downstream_routing_table_hit: exact;
                local_metadata.flag_hdr.is_pkt_toward_host:exact;


                //all hdr field

                hdr.mdn_int.next_hdr: exact;
                hdr.mdn_int.src_enq_timestamp: exact;
                hdr.mdn_int.src_deq_timestamp: exact;



                //All control header fields
                local_metadata.delay_info_hdr.event_src_type: exact;
                local_metadata.delay_info_hdr.path_delay_event_type: exact;
                local_metadata.delay_info_hdr.path_delay_event_data: exact;


                local_metadata.egress_rate_event_hdr.egress_traffic_color: exact;

                hdr.ipv6.next_hdr: exact;
                hdr.ipv6.flow_label : exact;
                hdr.ipv6.traffic_class : exact;

                hdr.tcp.src_port : exact;
                hdr.tcp.dst_port : exact;
                hdr.tcp.seq_no : exact;
                hdr.tcp.ack_no : exact;
                hdr.tcp.data_offset : exact;
                hdr.tcp.res : exact;
                hdr.tcp.ecn : exact;
                //hdr.tcp.ctrl : exact;
                hdr.tcp.urg_control_flag : exact;
                hdr.tcp.ack_control_flag : exact;
                hdr.tcp.psh_control_flag : exact;
                hdr.tcp.rst_control_flag : exact;
                hdr.tcp.syn_control_flag : exact;
                hdr.tcp.fin_control_flag : exact;
                hdr.tcp.window : exact;
                hdr.tcp.checksum : exact;
                hdr.tcp.urgent_ptr : exact;


            }
            actions = { NoAction; }
            const default_action = NoAction();
        }
        apply {
            dbg_table.apply();

        }
    }
#endif

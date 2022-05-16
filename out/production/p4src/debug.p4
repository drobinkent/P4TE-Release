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
                standard_metadata.instance_type : exact;
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
                standard_metadata.packet_length : exact;
                standard_metadata.priority:exact;
                //all local metadata
                local_metadata.m_color: exact;
                local_metadata.ingress_traffic_color: exact;

            }
            actions = { NoAction; }
            const default_action = NoAction();
        }
        apply {
            dbg_table.apply();
        }
    }
#endif

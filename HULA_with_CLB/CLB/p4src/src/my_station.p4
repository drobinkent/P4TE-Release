#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef MY_STATION_PROCESSING
#define MY_STATION_PROCESSING
control my_station_processing(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{
    table my_station_table {
            key = {
                hdr.ethernet.dst_addr: exact;
            }
            actions = { NoAction; }
            @name("my_station_table_counter")
            counters = direct_counter(CounterType.packets_and_bytes);
        }
   apply {

        if(my_station_table.apply().hit) local_metadata.flag_hdr.my_station_table_hit = true;
        else local_metadata.flag_hdr.my_station_table_hit = false;
   }
}
#endif





#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef DP_ONLY_MULTICRITERIA_UPSTREAM_POLICY_ROUTING
#define DP_ONLY_MULTICRITERIA_UPSTREAM_POLICY_ROUTING
control dp_only_multicriteria_upstream_policy_routing(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{

    //The overall flow of this block have to be like follwoing.
    // if (local_metadata.flag_hdr.do_l3_l2) {
 //   then call the actions of route finding
  //  }else{
//        call the actions of route maintanence
    //}
    //We may not be able to use this way because of P4 language features. on that case we need to move these stuffs in main ingress pipe

    //This is a 8 bit map. that means 2^8 levels can be kept. Which is actually not necessary. But we are  keeping them redundant now
    //At this moment we are only using 4 levels. so a mere 2 bit should be good enough
    @name("port_to_metrics_current_level_map")register<bit<8>>(MAX_PORTS_IN_SWITCH) port_to_metrics_current_level_map;
    @name("level_4_index")register<bit<32>>(MAX_PORTS_IN_SWITCH) level_4_index;
    @name("level_4_path_list")register<bit<32>>(MAX_PORTS_IN_SWITCH) level_4_path_list;
    @name("level_4_path_list_hi_index")register<bit<32>>(1) level_4_path_list_hi_index; //Low index will be always 0

    @name("level_3_index")register<bit<32>>(MAX_PORTS_IN_SWITCH) level_3_index;
    @name("level_3_path_list")register<bit<32>>(MAX_PORTS_IN_SWITCH) level_3_path_list;
    @name("level_3_path_list_hi_index")register<bit<32>>(1) level_3_path_list_hi_index; //Low index will be always 0

    @name("level_2_index")register<bit<32>>(MAX_PORTS_IN_SWITCH) level_2_index;
    @name("level_2_path_list")register<bit<32>>(MAX_PORTS_IN_SWITCH) level_2_path_list;
    @name("level_2_path_list_hi_index")register<bit<32>>(1) level_2_path_list_hi_index; //Low index will be always 0

    @name("level_1_index")register<bit<32>>(MAX_PORTS_IN_SWITCH) level_1_index;
    @name("level_1_path_list")register<bit<32>>(MAX_PORTS_IN_SWITCH) level_1_path_list;
    @name("level_1_path_list_hi_index")register<bit<32>>(1) level_1_path_list_hi_index; //Low index will be always 0

    @name("level_membership_bitmap")register<bit<4>>(1) level_membership_bitmap; //This is a 4 bit register. Here we will keep track which level is empty and which level is non empty
    //MSB for level 4-- lsb for level1


    action process_feedback(path_index, metrics_level){
    }


    apply {

    }

}
#endif





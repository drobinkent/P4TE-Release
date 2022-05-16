import ipaddress

class ControlPacket:

    def __init__(self, packet):
        # @controller_header("packet_in")
        # header packet_in_t {
        #     port_num_t  ingress_port;
        # bit<2>      _pad;
        #
        # //===
        # bit<8>     ingress_queue_event;
        # bit<48>    ingress_queue_event_data;
        # bit<9>     ingress_queue_event_port;
        #
        # //===
        # bit<8>     egress_queue_event;
        # bit<48>    egress_queue_event_data;
        # bit<9>     egress_queue_event_port;
        #
        # //===
        # bit<32>    ingress_traffic_color;
        # bit<48>    ingress_rate_event_data;
        # bit<9>     ingress_rate_event_port;
        #
        # //===
        # bit<32>    egress_traffic_color;
        # bit<48>    egress_rate_event_data;
        # bit<9>     egress_rate_event_port;
        #
        # bit<8> delay_event_src_type;  //This field is for notifying whther an event is hop to hop or came from a hop more than 1 hop distance
        # //Next fields are event data
        # //bit<16>
        # bit<8>    path_delay_event_type;
        # bit<48>     path_delay_event_data;
        # bit<128> dst_addr;   //This is the address for which the switch has found increased or decreased delay
        # bit<9>     path_delay_event_port;
        #
        # }
        self.ingress_port= int.from_bytes(packet.metadata[0].value, byteorder='big', signed=True)
        self._pad= packet.metadata[1].value
        self.ingress_queue_event= int.from_bytes(packet.metadata[2].value, byteorder='big', signed=True)
        self.ingress_queue_event_data= int.from_bytes(packet.metadata[3].value, byteorder='big', signed=True)
        self.ingress_queue_event_port=int.from_bytes(packet.metadata[4].value, byteorder='big', signed=True)

        self.egress_queue_event= int.from_bytes(packet.metadata[5].value, byteorder='big', signed=True)
        self.egress_queue_event_data= int.from_bytes(packet.metadata[6].value, byteorder='big', signed=True)
        self.egress_queue_event_port = int.from_bytes(packet.metadata[7].value, byteorder='big', signed=True)

        self.ingress_traffic_color= int.from_bytes(packet.metadata[8].value, byteorder='big', signed=True)
        self.ingress_rate_event_data= int.from_bytes(packet.metadata[9].value, byteorder='big', signed=True)
        self.ingress_rate_event_port=int.from_bytes(packet.metadata[10].value, byteorder='big', signed=True)

        self.egress_traffic_color= int.from_bytes(packet.metadata[11].value, byteorder='big', signed=True)
        self.egress_rate_event_data= int.from_bytes(packet.metadata[12].value, byteorder='big', signed=True)
        self.egress_rate_event_port=int.from_bytes(packet.metadata[13].value, byteorder='big', signed=True)

        self.delay_event_src_type= int.from_bytes(packet.metadata[14].value, byteorder='big', signed=True)
        self.path_delay_event_type= int.from_bytes(packet.metadata[15].value, byteorder='big', signed=True)
        self.path_delay_event_data= int.from_bytes(packet.metadata[16].value, byteorder='big', signed=True)
        self.dest_IPv6_address= ipaddress.IPv6Address( packet.metadata[17].value ) # eed to convert this to ipv6 address
        self.path_delay_event_port=int.from_bytes(packet.metadata[18].value, byteorder='big', signed=True)
        pass

    def __str__(self):
        strRepresentation = ""
        strRepresentation = strRepresentation + "ingress_port : " + str(self.ingress_port) + "\n"
        strRepresentation = strRepresentation + "_pad:" + str(self._pad.value) + "\n"
        strRepresentation = strRepresentation + "ingress_queue_event : " + str(self.ingress_queue_event) + "\n"
        strRepresentation = strRepresentation + "ingress_queue_event_data : " + str(self.ingress_queue_event_data) + "\n"
        strRepresentation = strRepresentation + "egress_queue_event : " + str(self.egress_queue_event) + "\n"
        strRepresentation = strRepresentation + "egress_queue_event_data : " + str(self.egress_queue_event_data) + "\n"
        strRepresentation = strRepresentation + "ingress_traffic_color : " + str(self.ingress_traffic_color) + "\n"
        strRepresentation = strRepresentation + "ingress_rate_event_data : " + str(self.ingress_rate_event_data) + "\n"
        strRepresentation = strRepresentation + "egress_traffic_color : " + str(self.egress_traffic_color) + "\n"
        strRepresentation = strRepresentation + "egress_rate_event_data : " + str(self.egress_rate_event_data) + "\n"
        strRepresentation = strRepresentation + "delay_event_src_type : " + str(self.delay_event_src_type) + "\n"
        strRepresentation = strRepresentation + "path_delay_event_type : " + str(self.path_delay_event_type) + "\n"
        strRepresentation = strRepresentation + "path_delay_event_data: " + str(self.path_delay_event_data) + "\n"
        strRepresentation = strRepresentation + "dest_IPv6_address: " + str(self.dest_IPv6_address) + "\n"
        return strRepresentation


# What is the result of p4 type exansion
# if we have 8 bit invalid constnat what happens if we make it 48 bit
IDEA:

1) When we insert port for ingress and egress port stats, we can also add whether they areconnected to leaf, spine or super spine, thus it can help to identify 
metrics, based on each type of switch. For example, a spine switch can get delay info for it's upstream ports for specific superspine. 



#Feedback header field meanings. 

* Dealy_hdr -- This field is collected by neighbour switch and send to sender of the packet. So we need 2 info, the ip address and the port
of the packet that have found the delay. 
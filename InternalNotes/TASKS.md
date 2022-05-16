#Tasks we need to do

1. Calculate oversubscription ratio
    * Calculate Link bandwidth accordingly
    * Calculate meter rate acordingly and setup
2. Ingress and egress statictics in P4

3. If port id cpu port do not add 2 port in the multicast group. Bmv2 may make 2 copies.
4. make a set of global registers for each of the materices. If for any metrics a port is marked in egress we will make a 
ctrl hdr for that port and sent it. in egress 

    if a port of a packet is marked for creating ctrl hdr we will clone it to the session with that port
        So there will be 2 copy 1 for cpu and one for that port. 
        In egress
        
        If there is a a packet to be send to neighbour swithc as feedback clone to the session with  ingress or egress port
        else clone to cpu session 
        
        if packet is cloned send ctrl packet
        else normal forwarding              


5. In one method keep all table setup for statistics. so that it is easy to find  
        
 


========================
By default customized_algo == false
algo part
    if matching path found make customized_algo == true

if customized_algo_enabled -- false or config == false then fall back to ecmp


# nick mackkeon ar hotnets 19/18 ar paper a proposal ache control event gulo k sperate thread a process korar. we can do that
on that case cp r dorkar nai. so amra jekono device a ja change kori cp theke shegulo k, oi device er store a save kore rekhe dite pari. tarpor sob event CP te process kore 
special algorithm chalate pari.
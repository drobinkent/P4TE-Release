# How we will do testing 

    We will install 2 distribution and 2 different precision
    and we can show our concept of installing paths for first link and buying time

In MyController.py there is a function startMonitoringFromController, here we will start a new thread per device which will install the 
distribution 

In statisticspuller we will pull only the upaward ports counter. all other will be not read to minimize the time 

The statsticspuller thread will have a function to configure the distribution. -- load_balancer_config_thread_function
this function 
start a new thread 
then in the therad follow the algorihtm in presentation 
we will prepare all the message and dispatch them together. 
-- obviously if too many packets are sent together then buffer can be overhelmed. to handle that in this experiement wer will 
keep buffer capacity a lot. 

The statsticspuller thread will pull only  pull statictics from the configured device. all other device will be lleft untouched. 

# As out target is only testing algorothm we will only run the CLB from one switch.
#This parameter defines that name. The algorithm will be only run with that device


In data plane program, we will set, if for a switch CLB can not find any path then default action will set 
the path to -1. 

then we will check if no vlaid path is found then use ECMP. As a result only our configured switch will 
use the load balanicng algorohtm. Al other will use ECMP.
    


# Result Visualization





===============================================================

# How to test the load balancer 
How to do test : 

Assume we want to test 128 packets per second using 4 links. our precision tolerance is 8 packets. So total weight group can be 16
Also you have to make sure that the sum of the wight is at max 16.
so in make file, DBITMASK_LENGTH = 16 and DPRECISION_FACTOR = 3 
-- here 16 means 16 weight groups and 3 means shofting right 3 times. which is equivalent to divide by 8 that means precision of 8. 
and for representing 16 we need 4 bits (0 to 15)

-DENABLE_DEBUG_TABLES -DDP_ALGO_CLB  -DBITMASK_LENGTH=16  -DBITMASK_POSITION_INDICATOR_BITS_LENGTH=4  -DPRECISION_FACTOR=3


-- This is for P4 program 


for controller we need to open ConfigConst.py and at the bottom we need to change the configs

#=======================configurations for CLB
CPU_PORT = 255
CLB_TESTER_DEVICE_NAME = "p0l0" # As out target is only testing algorithm we will only run the CLB from one switch.
#This parameter defines that name. The algorithm will be only run with that device
LOAD_DISTRIBUTION_1 = [(5,2),(6,6),(7,1),(8,7)]
LOAD_DISTRIBUTION_2 = [(5,7),(6,1),(7,6),(8,2)]

DISTRO1_INSTALL_DELAY = 0   # Weight distribution 1 will be installed after 50 second of the controller thread starts
DISTRO2_INSTALL_DELAY = 125  # Weight distribution 2 will be installed after 50 second of the controller thread starts


BITMASK_LENGTH = 16  # This must match with the P4 program 

And do not forget to configure the packet processing rate of the links in ConfigConst.py

----

Next open CNF and there configure pps = 128
because we are testing for 128 packets per second


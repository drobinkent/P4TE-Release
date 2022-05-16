# How to setup the environment
    . Go to jfingerhut's github repository of P4-guide. (https://github.com/jafingerhut/p4-guide)
    . Use the install script you want to use appropriate for your distribution.
    . We have used the Ubuntu 20.04 version (https://github.com/jafingerhut/p4-guide/blob/master/bin/install-p4dev-v4.sh)

# # Now download the github repository for this project 
    . Link : https://github.com/drobinkent/CLB.git

# All the necessary libraries should be already installed in the system by now


# There are 3 types of results used in paper 

    * for accuracy analysis checkou to commit  "43ca015aa558dec37ebb81e7f1987d79e8b15aff". Then follow the README. 
    * For performance improvement anlysis, we have created websearch pattern (the real data center workload ) for different load factors. 
        
        1) Open the "MininetSimulator/ClosConstants.py". At the very bottom of the file change the TCP_SERVER_COMAND_FILE and TCP_CLIENT_COMAND_FILE for different workload.
        2) then open the "ConfigConst.py" and change the variable "ALGORITHM_IN_USE" value to any scheme you want to use . 3 options CLB, HULA, ECMP
        3) Then compile the P4 command using the command "make p4-clb" , "make p4-ecmp"  or "make p4-hula". whichever you have configured in  previous step
        4) then open 2 terminals. in one terminal execute command "make start_clos" , this will start the mininet 
        5) then in another terminal  execute command "make start_ctrlr". This will start the controller and automatically deploy various flow from the hosts according the configuration of step 1
        6) make sure you start both the mininet simulator and the controller quickly. Or you can increase the value  TEST_START_DELAY in "MininetSimulator/ClosConstants.py" to increase the delay between miniet simulator start and deploying the flows
        7) Once all flows are finished the results are saved in "testAndMeasurement/TEST_RESULTS"
        8) All the results used in the paper are saved in "testAndMeasurement/TEST_RESULTS_USED_IN_PAPER" with 
        9) there are 3 scripts to analyze the Average flow completion time and load imbalance. they are a) FCTAnalyzer.py and b) LoadBalancerResultAnalyzer.py

    * For analyze the convergence time between the hash boundary based scheme and CLB, there is a python script. It is "ConvergeneceTimeCalculator/WCMPConvergenceCalculator.py"
    * Similarly to analyze the impact og hash based indexing and how it helps to save stateful memory in switch the code is in file "ConvergeneceTimeCalculator/HashCollisionEvaluator.py"

    



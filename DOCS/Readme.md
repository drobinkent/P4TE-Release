# How to setup the environment
    . Go to jfingerhut's github repository of P4-guide. 
    https://github.com/jafingerhut/p4-guide/blob/master/bin/README-install-troubleshooting.md
    . Use the follwoing VM 
    2021-Dec-03	Ubuntu 20.04	4 GByte VM image
    It has everything installed and ready to run

# Now download the github repository for this project 

# All the necessary libraries should be already installed in the system by now

# How to run this system 

* Open three terminal and go inside the folder where you have copied this project 
* In one terminal write "make start_clos" -- This will start the mininet network based data plane 
* In another terminal write "make start_ctrlr" -- This will start the control plane
* After 1 min has gone, the controller will configure everything. In another terminal write follwing command 
python3 TestCaseDeployer.py traffic_configuration_file_path 
This will start the traffic and the results will be saved to testAndMeasurement/TEST_RESULTS folder. 
Example traffic configurations can be found in testAndMeasurement/TestConfigs folder. 
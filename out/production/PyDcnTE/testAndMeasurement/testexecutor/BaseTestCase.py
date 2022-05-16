# # there will be a speific generic way of executing a test case
#
# Steps are
#
# a) Setup test case
#     -- setup sender , reciver, packet generaition distribution
# b) Create test Packets
# c) send packets
# d) calculate evaluation reports./ This report is from end host
# e) some meaurements will be collected by switches to controller. We need to process them and prepare the test case
#
# All the test cases will have these things in common
#
# We will have a python dictionary type
#
# Test case name --> python script
# when we will call a specific test case, relevant python script will be executed and the rport will be generated.

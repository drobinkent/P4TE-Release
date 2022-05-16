import glob
from os import listdir
from os.path import isfile, join

import numpy as np

import ConfigConst


def getAllFilesInDirectory(folderPath):

    # r=root, d=directories, f = files
    onlyfiles = [f for f in listdir(folderPath) if (isfile(join(folderPath, f)))]
    # print("Total files in this directory is ", len(onlyfiles))
    return onlyfiles

def getAVGFCTByFolder(folderName):
    files = getAllFilesInDirectory(folderName)
    flowTypeVsFCTMap = {}
    flowTypeVsFlowCountMap = {}
    QOS_AWARE_TRAFFIC_FLOW_VOLUMES = {8000,16000}  #you have to add these volumes manually
    for v in QOS_AWARE_TRAFFIC_FLOW_VOLUMES:
        TRAFFIC_VOLUME_TYPE.append(v)
    for flowVolume in TRAFFIC_VOLUME_TYPE:
        flowTypeVsFCTMap[flowVolume]  = 0
        flowTypeVsFlowCountMap[flowVolume] = 0
    for f in files:
        filePath = folderName+"/"+str(f)
        try:
            f =open(filePath , 'r')
            line = f.readline()
            #(sender[0]+'\t'+str(sender[1])+'\t'+receiver[0]+'\t'+str(flow_size)+'\t'+str(start)+'\t'+str(end)+'\t'+str(fct)+'\t'+str(bw))
            #2001:1:1:1::	35466	2001:1:1:1::1:1	51200.0	2021-06-07 21:35:09.471579	2021-06-07 21:35:49.964961	40.493382	0.010115233150938097
            tokens = line.split()
            flowSize = float(tokens[3])
            fct = float(tokens[8])

            for flowVolume in TRAFFIC_VOLUME_TYPE:
                if abs(flowVolume*1024 - flowSize) <= (.1*flowVolume*1024):
                    flowTypeVsFCTMap[flowVolume] = flowTypeVsFCTMap.get(flowVolume) + fct
                    flowTypeVsFlowCountMap[flowVolume] = flowTypeVsFlowCountMap.get(flowVolume) + 1
        except Exception as e:
            print("Exception occcured in processing results from folder "+folderName+ ". Excemtion is "+(e.with_traceback()))
    for f in flowTypeVsFCTMap:
        print(str(f) + " -- ",flowTypeVsFCTMap.get(f))
        print(str(f) + " -- ",flowTypeVsFlowCountMap.get(f))
        print(str(f) + " -- ",flowTypeVsFCTMap.get(f)/flowTypeVsFlowCountMap.get(f))
    pass

def getPercentileFCTByFolder(folderName):
    files = getAllFilesInDirectory(folderName)
    flowTypeVsFCTMap = {}
    flowTypeVsFlowCountMap = {}
    QOS_AWARE_TRAFFIC_FLOW_VOLUMES = {8000,16000}  #you have to add these volumes manually
    # for v in QOS_AWARE_TRAFFIC_FLOW_VOLUMES:
    #     if (not (v in TRAFFIC_VOLUME_TYPE)):
    #         TRAFFIC_VOLUME_TYPE.append(v)


    # TRAFFIC_VOLUME_TYPE.append(3200)
    TRAFFIC_VOLUME_TYPE = []
    for f in files:
        filePath = folderName+"/"+str(f)
        try:
            f =open(filePath , 'r')
            line = f.readline()
            tokens = line.split()
            flowSize = float(tokens[3])
            if (not (flowSize in TRAFFIC_VOLUME_TYPE)):
                TRAFFIC_VOLUME_TYPE.append(flowSize)

        except Exception as e:
            print("Exception occcured in processing results from folder "+folderName+ ". Excemtion is ",str(e))
    for flowVolume in TRAFFIC_VOLUME_TYPE:
        flowTypeVsFCTMap[flowVolume]  = []
        flowTypeVsFlowCountMap[flowVolume] = 0
    for f in files:
        filePath = folderName+"/"+str(f)
        try:
            f =open(filePath , 'r')
            line = f.readline()
            #(sender[0]+'\t'+str(sender[1])+'\t'+receiver[0]+'\t'+str(flow_size)+'\t'+str(start)+'\t'+str(end)+'\t'+str(fct)+'\t'+str(bw))
            #2001:1:1:1::	35466	2001:1:1:1::1:1	51200.0	2021-06-07 21:35:09.471579	2021-06-07 21:35:49.964961	40.493382	0.010115233150938097
            tokens = line.split()
            flowSize = float(tokens[3])
            fct = float(tokens[8])

            for flowVolume in TRAFFIC_VOLUME_TYPE:
                if abs(flowVolume*1 - flowSize) <= (.0005*flowVolume*1):
                    flowTypeVsFCTMap.get(flowVolume).append(fct)
                    # flowTypeVsFCTMap[flowVolume] = flowTypeVsFCTMap.get(flowVolume).append(fct)
                    flowTypeVsFlowCountMap[flowVolume] = flowTypeVsFlowCountMap.get(flowVolume) + 1
                    # if(flowVolume == 3200):
                    #     print("filename is "+str(f))
        except Exception as e:
            print("Exception occcured in processing results from folder "+folderName+ ". Excemtion is ",str(e))
    totalFlowsize = 0
    totalOfFlowSizeMultipliedByAvgFct=0
    for f in flowTypeVsFCTMap:
        # print(str(f) + " -- ",np.percentile(flowTypeVsFCTMap.get(f), 80))
        if(flowTypeVsFlowCountMap.get(f) <=0):
            pass
        else:
            print(str(f) + " -- ",flowTypeVsFlowCountMap.get(f))

            # print(str(f) + " -- ",flowTypeVsFCTMap.get(f)/flowTypeVsFlowCountMap.get(f))
            totalFlowsize= totalFlowsize+ float(f)

            totalOfFlowSizeMultipliedByAvgFct = totalOfFlowSizeMultipliedByAvgFct + ( float(f) * np.average(flowTypeVsFCTMap.get(f)))
            print(str(f) + " -- ",np.average(flowTypeVsFCTMap.get(f)))
            # print(str(f) + " -- ",np.std(flowTypeVsFCTMap.get(f)))

            # totalOfFlowSizeMultipliedByAvgFct = totalOfFlowSizeMultipliedByAvgFct + ( float(f) * np.percentile(flowTypeVsFCTMap.get(f),100))
            # print(str(f) + " -- ",np.percentile(flowTypeVsFCTMap.get(f),100))
    print("Average FCT  = ", totalOfFlowSizeMultipliedByAvgFct/totalFlowsize)

    pass



# print("For WebSearch Workload, with Load Factor 1.0")
# # # print("Algorithms Nanme : HULA ")
# # # getPercentileFCTByFolder("/home/deba/Desktop/Top-K-Path/testAndMeasurement/TEST_RESULTS/HULA_RESULTS/WebSearchWorkLoad_load_factor_0.8")
# print("Algorithms Nanme : P4KP ")
# getPercentileFCTByFolder("/home/deba/Desktop/Top-K-Path/testAndMeasurement/TEST_RESULTS/P4KP_RESULTS/WebSearchWorkLoad_load_factor_1.0")
# print("Algorithms Nanme : ECMP ")
# getPercentileFCTByFolder("/home/deba/Desktop/Top-K-Path/testAndMeasurement/TEST_RESULTS/ECMP_RESULTS/WebSearchWorkLoad_load_factor_1.0")
# print("\n\n\n")
#
#
# print("For WebSearch Workload, with Load Factor 0.8")
# print("Algorithms Nanme : HULA ")
# getPercentileFCTByFolder("/home/deba/Desktop/Top-K-Path/testAndMeasurement/TEST_RESULTS/HULA_RESULTS/WebSearchWorkLoad_load_factor_0.8")
# print("Algorithms Nanme : P4KP ")
# getPercentileFCTByFolder("/home/deba/Desktop/Top-K-Path/testAndMeasurement/TEST_RESULTS/P4KP_RESULTS/WebSearchWorkLoad_load_factor_0.8")
# print("Algorithms Nanme : ECMP ")
# getPercentileFCTByFolder("/home/deba/Desktop/Top-K-Path/testAndMeasurement/TEST_RESULTS/ECMP_RESULTS/WebSearchWorkLoad_load_factor_0.8")
# print("\n\n\n")
print("For WebSearch Workload, with Load Factor 0.7")
print("Algorithms Nanme : HULA ")
getPercentileFCTByFolder("/home/deba/Desktop/Top-K-Path/testAndMeasurement/TEST_RESULTS/HULA_RESULTS/WebSearchWorkLoad_load_factor_0.7")
print("Algorithms Nanme : P4KP ")
getPercentileFCTByFolder("/home/deba/Desktop/Top-K-Path/testAndMeasurement/TEST_RESULTS/P4KP_RESULTS/WebSearchWorkLoad_load_factor_0.7")
print("Algorithms Nanme : ECMP ")
getPercentileFCTByFolder("/home/deba/Desktop/Top-K-Path/testAndMeasurement/TEST_RESULTS/ECMP_RESULTS/WebSearchWorkLoad_load_factor_0.7")
print("\n\n\n")
print("For WebSearch Workload, with Load Factor 0.5")
print("Algorithms Nanme : HULA ")
getPercentileFCTByFolder("/home/deba/Desktop/Top-K-Path/testAndMeasurement/TEST_RESULTS/HULA_RESULTS/WebSearchWorkLoad_load_factor_0.5")
print("Algorithms Nanme : P4KP ")
getPercentileFCTByFolder("/home/deba/Desktop/Top-K-Path/testAndMeasurement/TEST_RESULTS/P4KP_RESULTS/WebSearchWorkLoad_load_factor_0.5")
print("Algorithms Nanme : ECMP ")
getPercentileFCTByFolder("/home/deba/Desktop/Top-K-Path/testAndMeasurement/TEST_RESULTS/ECMP_RESULTS/WebSearchWorkLoad_load_factor_0.5")
# print("\n\n\n")
print("For WebSearch Workload, with Load Factor 0.4")
print("Algorithms Nanme : HULA ")
getPercentileFCTByFolder("/home/deba/Desktop/Top-K-Path/testAndMeasurement/TEST_RESULTS/HULA_RESULTS/WebSearchWorkLoad_load_factor_0.4")
print("Algorithms Nanme : P4KP")
getPercentileFCTByFolder("/home/deba/Desktop/Top-K-Path/testAndMeasurement/TEST_RESULTS/P4KP_RESULTS/WebSearchWorkLoad_load_factor_0.4")
print("Algorithms Nanme : ECMP ")
getPercentileFCTByFolder("/home/deba/Desktop/Top-K-Path/testAndMeasurement/TEST_RESULTS/ECMP_RESULTS/WebSearchWorkLoad_load_factor_0.4")
# print("\n\n\n\n")
print("For WebSearch Workload, with Load Factor 0.2")
print("Algorithms Nanme : HULA ")
getPercentileFCTByFolder("/home/deba/Desktop/Top-K-Path/testAndMeasurement/TEST_RESULTS/HULA_RESULTS/WebSearchWorkLoad_load_factor_0.2")
print("Algorithms Nanme : P4KP ")
getPercentileFCTByFolder("/home/deba/Desktop/Top-K-Path/testAndMeasurement/TEST_RESULTS/P4KP_RESULTS/WebSearchWorkLoad_load_factor_0.2")
print("Algorithms Nanme : ECMP ")
getPercentileFCTByFolder("/home/deba/Desktop/Top-K-Path/testAndMeasurement/TEST_RESULTS/ECMP_RESULTS/WebSearchWorkLoad_load_factor_0.2")



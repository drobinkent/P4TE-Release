#Here all code relevan to result processor will be added

#REsult processing
# Read the loadCFG it has 2 parts 1) host config 2) switch config
# loook at testAndEval.py followo same file passing mechanism. we will actually
# Need to move the CFg loading part of both testandEval and result processor in same place.
# In test we only read host config. For result processing we need to load 1) host config 2) swiotch config 3) TEST case config 4) result processor

# Tasks :
# Write 2 function
# 1) ServerSidePortStatisticsProcessor(self, filename) -- return list of PortStatsJson
# 2) ClientSideIperf result Processor(self, filename) -- return IperfResultObject


import json
import math
import matplotlib.pyplot as plot
import numpy as np
import ConfigConst as CC
import testAndMeasurement.ResultParsers as rp
from os import listdir
from os.path import isfile, join

_decoder = json.JSONDecoder()
_encoder = json.JSONEncoder()
_space = '\n'

def loads(s):
    """A generator reading a sequence of JSON values from a string."""
    while s:
        s = s.strip()
        obj, pos = _decoder.raw_decode(s)
        if not pos:
            raise ValueError('no JSON object found at %i' % pos)
        yield obj
        s = s[pos:]


def loadRowJsonAsDictFromFile(file_path):
    with open(file_path, 'r') as fh:
        data = fh.read()
    try:
        rawJsonObjects = loads(data)
        return  rawJsonObjects
    except Exception as ex:  # pylint: disable=broad-except
        print('Could not parse JSON from file (ex): {0}'.format(str(ex)))
        print("Exiting!!")
        exit(1)

def indexToRowColumn( index, totalColumns):
    row = int(math.floor(index/float(totalColumns)))
    column = index % totalColumns
    return row, column  # TODO we may need to subtract 1 t match the index number(as index starts from zero)

def  controllerSidePortStatisticsProcessor(fileName):
    '''
    This function reads the given file and parses all the serverside statistics from the file and return them as list
    '''
    rawJsonObjects = loadRowJsonAsDictFromFile(fileName)
    if(rawJsonObjects == None) :
        print("Failed to retrieve valid server side statistics from file:"+fileName+" Exiting!!!")
        exit(1)
    switchPortStatstics = []
    for o in rawJsonObjects:
        switchPortStats = rp.SwitchPortStatistics_from_dict(o)
        #print(switchPortStats)
        switchPortStatstics.append(switchPortStats)
    #print(switchPortStatstics)
    return switchPortStatstics


def  iPerf3ResultProcessorForSinglehost(fileName):
    '''
    This function reads the given file and parses all the serverside statistics from the file and return them as list
    '''
    rawJsonObjects = loadRowJsonAsDictFromFile(fileName)
    if((rawJsonObjects == None) ):
        print("Failed to retrieve valid host side  Iperf3 statistics from file:"+fileName+" Exiting!!!")
        exit(1)
    switchIPerfStatistics = []
    for o in rawJsonObjects:
        switchIPerfStat = rp.IPerfResult_from_dict(o)
        #print(switchPortStats)
        switchIPerfStatistics.append(switchIPerfStat)
    #print(switchIPerfStatistics)
    return switchIPerfStatistics


def testFunction():
    contrrollerPortStatsFilePath = "/home/deba/Desktop/PyDcnTE/result/p0l0.json"
    portSVal= controllerSidePortStatisticsProcessor(contrrollerPortStatsFilePath)
    #print(portSVal)
    hostsideIPerfResultFilePath = "/home/deba/Desktop/PyDcnTE/testAndMeasurement/TEST_RESULTS/ECMP1-h0p0l0-h1p1l1"
    hostVal = iPerf3ResultProcessorForSinglehost(hostsideIPerfResultFilePath)
    return

class PortToCounterValue:
    def __init__(self):
        self.times = []
        self.counterValues = []

def upwardLinkUtilizationVisualizer(folderPath,deviceName, plotAxes, startTime=0):
    '''
    This function draws graph for CDF (summation of packets passed through the link) of a device
    :param folderPath: Path of the folder where the function will look for a file
    :param deviceName: with name deviceName.json
    :param startTime indicates value before this time will be discarded wll drawing the graph
    :return: Nothing. But draws graph in the given axes
    '''
    #TODO
    # there is a problem here. For superspines upward links utilization is not a matter. for super spine it should be downward link.
    # Next we are only giving the counter. But we are not actually showing how much of the link capcity we are using. We can only compare when we have 2 sets of resutls
    portStatisticsAsList = controllerSidePortStatisticsProcessor(folderPath+deviceName+".json")
    #s= rp.SwitchPortStatistics()
    portVsPortToCounterValueMap = {}
    for stats in portStatisticsAsList:
        for p in stats.port_stats.upward_port_ingress_packet_counter.keys():   # this is a port vs counter map
            portId = int(p)
            counter_value = int(stats.port_stats.upward_port_ingress_packet_counter.get(p))
            if portVsPortToCounterValueMap.get(portId) == None:
                portVsPortToCounterValueMap[portId] = PortToCounterValue()

            if(stats.time >startTime):
                portVsPortToCounterValueMap[portId].times.append(stats.time)
                portVsPortToCounterValueMap[portId].counterValues.append(counter_value)
            #no wwe have all the port vs counter in the portVsCounterMap map . now plot it
    for port in portVsPortToCounterValueMap:
        plotAxes.plot(portVsPortToCounterValueMap[port].times, portVsPortToCounterValueMap[port].counterValues)
    plotAxes.set_title(label = deviceName)


def processHostSideResultFolder(folderPath ="/home/deba/Desktop/PyDcnTE/testAndMeasurement/TEST_RESULTS/ECMP2"):
    onlyfiles = [f for f in listdir(folderPath) if (isfile(join(folderPath, f)) and (not (f.endswith("server"))))]   #SKip the files that are server logs
    print(onlyfiles)
    return



# if __name__ == '__main__':
#     testFunction()
#     rp.ConfigLoader(CC.TOPOLOGY_CONFIG_FILE)

def processResults():
    #testFunction()
    # Generate axis. then pass file and axes to the function
    config = rp.ConfigLoader(CC.TOPOLOGY_CONFIG_FILE)
    totalNumOfSwitches = len(config.nameToSwitchMap)
    squareRootOftotalNumOfSwitches = math.sqrt(totalNumOfSwitches)
    nRow = math.ceil(squareRootOftotalNumOfSwitches)
    nColumn = math.ceil(totalNumOfSwitches/nRow)
    fig, axes = plot.subplots(nrows=nRow, ncols=nColumn, sharex=True, sharey=True)
    index=0
    for devName in config.nameToSwitchMap:
        print("Visualizing for dev:"+devName)

        row, col = indexToRowColumn(index= index, totalColumns= nColumn)
        #axes[row,col].plot(x, x*x)

        #pass this axes to function. plot will be drawn to this axes
        upwardLinkUtilizationVisualizer(CC.CONTROLLER_STATISTICS_RESULT_FILE_PATH, devName,startTime=0, plotAxes= axes[row,col])
        index  = index+1
    plot.show()

        # For each test config there should be a folder Name
        # all logs relevant to that test case will be written to that folder.
        # So assume for same configuration we have 2 algo. there will be 2 folder with ouput.
        # INside each folder there will be a special file where the time when the test will be started is written down.
        # We will use that time while processing and visualiing the server logs

        # to compare, we have to make sure inside 2 folder we have same set of file. each file will be name src-dst.json.
        #then we will compare 2 algo perfprmance
        # Basocally we do not need testconfig here. From the iperf result we wil find results. and from the name we will get src-dest and total data sent
        # also from the iPEerf result we can fund src and dest.

    processHostSideResultFolder()


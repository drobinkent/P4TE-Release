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
import os
import shutil
import sys

import matplotlib
import ConfigConst as CC
import testAndMeasurement.ResultParsers as rp
from os import listdir
from os.path import isfile, join, getmtime
from datetime import datetime

matplotlib.use("pgf")
matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    'font.family': 'serif',
    'text.usetex': True,
    'pgf.rcfonts': False,
    'legend.fontsize': 5,
    'legend.handlelength': 2
})

from matplotlib import pyplot as plt

_decoder = json.JSONDecoder()
_encoder = json.JSONEncoder()
_space = '\n'

PERCENTILE_STEP_SIZE = 1
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
        #print("Raw json objects are"+str(json.dumps(rawJsonObjects)))
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


def  iPerf3ResultProcessorForSinglehost(fileName,src,dst):
    '''
    This function reads the given file and parses all the serverside statistics from the file and return them as list
    '''
    rawJsonObjects = loadRowJsonAsDictFromFile(fileName)
    if((rawJsonObjects == None) ):
        print("Failed to retrieve valid host side  Iperf3 statistics from file:"+fileName+" Exiting!!!")
        exit(1)
    switchIPerfStatistics = []
    for o in rawJsonObjects:
        try:
            switchIPerfStat = rp.IPerfResult_from_dict(o)
            switchIPerfStat.setSrcDestName(src, dst)
            #print(switchPortStats)
            switchIPerfStatistics.append(switchIPerfStat)
            # try:
            #     for o in rawJsonObjects:
            #         switchIPerfStat = rp.IPerfResult_from_dict(o)
            #         switchIPerfStat.setSrcDestName(src, dst)
            #         #print(switchPortStats)
            #         switchIPerfStatistics.append(switchIPerfStat)
            #     #print(switchIPerfStatistics)
            # except AssertionError as e:
            #     print("Exception in reading result file "+fileName+" Exception is "+str(e))
            #     print(e)
            #     return None
            # except AttributeError as e :
            #     print("attribute Error occured in file "+fileName)
            #     return None
        except Exception as e:
            print("Failed to load json from file : ", fileName)
            return None

    return switchIPerfStatistics




class PortToCounterValue:
    def __init__(self):
        self.times = []
        self.counterValues = []


def getMinMaxtimeStampForLInkVisulationforAFolder(folderPath):
    onlyfiles = [f for f in listdir(folderPath) if (isfile(join(folderPath, f)) and (not (f.endswith("server"))))]   #SKip the files that are server logs
    startTime = 0
    for f in onlyfiles:
        if str(f) == "test_start_timer.txt":
            # This is a time file
            #print("Test Timer info file ")
            with open(str(join(folderPath, f)), 'r') as fh:
                data = fh.readline()
            print("Data is "+str(data))
            startTime = int(data)
            fh.close()
    folderPath = folderPath+"/client-logs-0"
    s,max, _  = parseIperfResultsFromFolder(folderPath)
    endTime = startTime+max
    print("Max  is "+str(endTime))
    return startTime, endTime

def parseIperfResultsFromFolder(folderPath):
    onlyfiles = [f for f in listdir(folderPath) if (isfile(join(folderPath, f)) and (not (f.endswith("server"))))]   #SKip the files that are server logs
    iperfResultObjects = []
    startTime = 0
    endTime = 0
    for f in onlyfiles:
        hostNames = str(f).split("-")
        temp = getmtime(folderPath+"/"+f)
        if temp >endTime:
            endTime = temp
        #print(f)
        if(len(hostNames) == 2):
            src = hostNames[0]
            dst = hostNames[1]
            #print("src :"+src+" | dest: " +dst)
            #iperfResultObjects = iperfResultObjects +  iPerf3ResultProcessorForSinglehost(str(join(folderPath, f)), src, dst)
            val =  iPerf3ResultProcessorForSinglehost(str(join(folderPath, f)), src, dst)
            if(val != None):
                iperfResultObjects.append(val)
        elif(len(hostNames) == 4):
            src = hostNames[0]
            srcPort= hostNames[1]
            dst = hostNames[2]
            dstPort = hostNames[3]
            #print("src :"+src+" | dest: " +dst)
            #iperfResultObjects = iperfResultObjects +  iPerf3ResultProcessorForSinglehost(str(join(folderPath, f)), src, dst)
            val =  iPerf3ResultProcessorForSinglehost(str(join(folderPath, f)), src, dst)  # this may have multiple results. Because in a single file w emay put multiple test results
            if(val != None):
                iperfResultObjects.append(val)
        elif str(f) == "test_start_timer.txt":
            # This is a time file
            #print("Test Timer info file ")
            with open(str(join(folderPath, f)), 'r') as fh:
                data = fh.read()
            startTime = int(data)
            fh.close()
        else:
            print("Unwanted file. Exiting!!")
            exit(1)
    val = rp.IPerfResultObjectsForOneFolder(folderPath, startTime, iperfResultObjects)
    stime, endTime , maxDuration= getMinMaxtimeStampOfTheIperfResults(val)
    return startTime, maxDuration, val



def getPortUtilizationData(folderPath, deviceName, startTime=0, endTime=9999999999):
    '''
    We tried a lot but can not find the issue of timing difference between controller time and the time in statistics colletcted.
    So we will manually clear the log and collect the maximum number of packets for a a link to compare their performance
    :param folderPath:
    :param deviceName:
    :param startTime:
    :param endTime:
    :return:
    '''
    controllerStatistics = controllerSidePortStatisticsProcessor(folderPath+deviceName+".json")
    upwardPortToEgressCounter = {}
    upwardPortToIngressCounter = {}
    downwardPortToEgressCounter = {}
    downwardPortToIngressCounter = {}
    for stats in controllerStatistics:
        if((stats.time >=startTime) and (stats.time <= endTime)):
            for p in stats.port_stats.upward_port_ingress_packet_counter.keys():   # this is a port vs counter map
                portId = int(p)
                upward_port_ingress_packet_counter = int(stats.port_stats.upward_port_egress_packet_counter.get(p))
                if ( upwardPortToIngressCounter.get(p) == None):
                    upwardPortToIngressCounter[p] = upward_port_ingress_packet_counter
                else:
                    if upwardPortToIngressCounter.get(p)< upward_port_ingress_packet_counter:
                        upwardPortToIngressCounter[p] = upward_port_ingress_packet_counter
            for p in stats.port_stats.upward_port_egress_packet_counter.keys():   # this is a port vs counter map
                portId = int(p)
                upward_port_egress_packet_counter = int(stats.port_stats.upward_port_egress_packet_counter.get(p))
                if ( upwardPortToEgressCounter.get(p) == None):
                    upwardPortToEgressCounter[p] = upward_port_ingress_packet_counter
                else:
                    if upwardPortToEgressCounter.get(p)< upward_port_ingress_packet_counter:
                        upwardPortToEgressCounter[p] = upward_port_ingress_packet_counter
            for p in stats.port_stats.downward_port_egress_packet_counter.keys():   # this is a port vs counter map
                portId = int(p)
                downward_port_egress_packet_counter = int(stats.port_stats.downward_port_egress_packet_counter.get(p))
                if ( downwardPortToEgressCounter.get(p) == None):
                    downwardPortToEgressCounter[p] = downward_port_egress_packet_counter
                else:
                    if downwardPortToEgressCounter.get(p)< downward_port_egress_packet_counter:
                        downwardPortToEgressCounter[p] = downward_port_egress_packet_counter
            for p in stats.port_stats.downward_port_inress_packet_counter.keys():   # this is a port vs counter map
                portId = int(p)
                downward_port_inress_packet_counter = int(stats.port_stats.downward_port_inress_packet_counter.get(p))
                if ( downwardPortToIngressCounter.get(p) == None):
                    downwardPortToIngressCounter[p] = downward_port_inress_packet_counter
                else:
                    if downwardPortToIngressCounter.get(p)< downward_port_inress_packet_counter:
                        downwardPortToIngressCounter[p] = downward_port_inress_packet_counter
    return (upwardPortToEgressCounter , upwardPortToIngressCounter, downwardPortToEgressCounter, downwardPortToIngressCounter)


def upwardLinkUtilizationVisualizerProcessor(folderPath,deviceName, plotAxes, startTime, endTime):
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
    controllerStatistics = controllerSidePortStatisticsProcessor(folderPath+deviceName+".json")
    # s= rp.SwitchPortStatistics()
    portVsPortToCounterValueMap = {}
    portVsUtilizationRateMap = {}

    oldTime = 0
    for stats in controllerStatistics:

        #print(stats)
        newTime = stats.time  # these values have to be taken from map not static values
        for p in stats.port_stats.upward_port_ingress_packet_counter.keys():   # this is a port vs counter map
            portId = int(p)

            if( (portVsPortToCounterValueMap.get(portId) == None) or (len(portVsPortToCounterValueMap[portId].counterValues) <=0)):
                oldCounterValue = 0
            else:
                oldCounterValue = portVsPortToCounterValueMap[portId].counterValues[-1] # -1 indexed item always gives the last item
            portRate = stats.port_stats.queue_rates.get(p)
            totalCapcityInTimeDelta = (newTime-oldTime)*portRate
            new_counter_value = int(stats.port_stats.upward_port_egress_packet_counter.get(p))

            # if(new_counter_value > 0):
            #     print("Place to debug")
            totalPacketInTimeDelta = new_counter_value - oldCounterValue
            portutilizationRate = (totalPacketInTimeDelta/totalCapcityInTimeDelta )* 100
            oldCounterValue = new_counter_value
            if portVsPortToCounterValueMap.get(portId) == None:
                portVsPortToCounterValueMap[portId] = PortToCounterValue()
                portVsUtilizationRateMap[portId] = PortToCounterValue()
            if((stats.time >=startTime) and (stats.time <= endTime)):
                # if (deviceName == "p0s0" and new_counter_value>0):
                #     print("Got p0s0")
                portVsPortToCounterValueMap[portId].times.append(stats.time)
                portVsPortToCounterValueMap[portId].counterValues.append(new_counter_value)
                portVsUtilizationRateMap[portId].times.append(stats.time)
                portVsUtilizationRateMap[portId].counterValues.append(portutilizationRate)
            #no we have all the port vs counter in the portVsCounterMap map . now plot it
        oldTime = newTime
    print("Device Name"+deviceName)
    for port in portVsPortToCounterValueMap:
        plotAxes.set_ylim([0,100])
        plotAxes.plot(portVsUtilizationRateMap[port].times, portVsUtilizationRateMap[port].counterValues)
        print(portVsUtilizationRateMap[port].times)
        print(portVsUtilizationRateMap[port].counterValues)

        #print(str(port), "--", str(portVsUtilizationRateMap[port].counterValues)+"\n")
    plotAxes.set_title(label = deviceName)

def dowawardLinkUtilizationVisualizerProcessor(folderPath,deviceName, plotAxes, startTime, endTime):
    '''
    This function draws graph for CDF (summation of packets passed through the link) of a device port
    :param folderPath: Path of the folder where the function will look for a file
    :param deviceName: with name deviceName.json
    :param startTime indicates value before this time will be discarded wll drawing the graph
    :return: Nothing. But draws graph in the given axes
    '''
    #TODO
    # there is a problem here. For superspines upward links utilization is not a matter. for super spine it should be downward link.
    # Next we are only giving the counter. But we are not actually showing how much of the link capcity we are using. We can only compare when we have 2 sets of resutls
    controllerStatistics = controllerSidePortStatisticsProcessor(folderPath+deviceName+".json")
    # s= rp.SwitchPortStatistics()
    portVsPortToCounterValueMap = {}
    portVsUtilizationRateMap = {}

    oldTime = 0
    for stats in controllerStatistics:

        #print(stats)
        newTime = stats.time  # these values have to be taken from map not static values
        for p in stats.port_stats.upward_port_ingress_packet_counter.keys():   # this is a port vs counter map
            portId = int(p)

            if( (portVsPortToCounterValueMap.get(portId) == None) or (len(portVsPortToCounterValueMap[portId].counterValues) <=0)):
                oldCounterValue = 0
            else:
                oldCounterValue = portVsPortToCounterValueMap[portId].counterValues[-1] # -1 indexed item always gives the last item
            portRate = stats.port_stats.queue_rates.get(p)
            totalCapcityInTimeDelta = (newTime-oldTime)*portRate
            new_counter_value = int(stats.port_stats.upward_port_egress_packet_counter.get(p))
            # if(new_counter_value > 0):
            #     print("Place to debug")
            totalPacketInTimeDelta = new_counter_value - oldCounterValue
            portutilizationRate = (totalPacketInTimeDelta/totalCapcityInTimeDelta )* 100
            oldCounterValue = new_counter_value
            if portVsPortToCounterValueMap.get(portId) == None:
                portVsPortToCounterValueMap[portId] = PortToCounterValue()
                portVsUtilizationRateMap[portId] = PortToCounterValue()
            if((stats.time >=startTime) and (stats.time <= endTime)):
                portVsPortToCounterValueMap[portId].times.append(stats.time)
                portVsPortToCounterValueMap[portId].counterValues.append(new_counter_value)
                portVsUtilizationRateMap[portId].times.append(stats.time)
                portVsUtilizationRateMap[portId].counterValues.append(portutilizationRate)
            #no we have all the port vs counter in the portVsCounterMap map . now plot it
        oldTime = newTime
    for port in portVsPortToCounterValueMap:
        plotAxes.plot(portVsUtilizationRateMap[port].times, portVsUtilizationRateMap[port].counterValues)
        #print(str(port), "--", str(portVsUtilizationRateMap[port].counterValues)+"\n")
    plotAxes.set_title(label = deviceName)



def  downwardLinkUtilizationVisualizer(nRow, nColumn, config, startTime, endTime):
    fig, axes = plt.plot.subplots(nrows=nRow, ncols=nColumn, sharex=True, sharey=True)
    index=0
    for devName in config.nameToSwitchMap:
        #print("Visualizing for dev:"+devName)

        row, col = indexToRowColumn(index= index, totalColumns= nColumn)
        #axes[row,col].plot(x, x*x)

        #pass this axes to function. plot will be drawn to this axes
        upwardLinkUtilizationVisualizerProcessor(CC.CONTROLLER_STATISTICS_RESULT_FILE_PATH, devName, plotAxes= axes[row,col], startTime = startTime, endTime =  endTime)
        index  = index+1
    plt.plot.show()

def  upwardLinkUtilizationVisualizer(nRow, nColumn, config, startTime, endTime, figfilePath):
    fig, axes =plt.subplots(nrows=nRow, ncols=nColumn, sharex=True, sharey=True)
    index=0
    for devName in config.nameToSwitchMap:
        #print("Visualizing for dev:"+devName)

        row, col = indexToRowColumn(index= index, totalColumns= nColumn)
        #axes[row,col].plot(x, x*x)

        #pass this axes to function. plot will be drawn to this axes
        upwardLinkUtilizationVisualizerProcessor(CC.CONTROLLER_STATISTICS_RESULT_FILE_PATH, devName, plotAxes= axes[row,col], startTime = startTime, endTime =  endTime)
        index  = index+1
    plt.savefig(figfilePath)



def  upwardLinkUtilizationAnalyzer( config):
    devToLinkUtilizationDataMap = {}
    for devName in config.nameToSwitchMap:
        val =getPortUtilizationData(folderPath = CC.CONTROLLER_STATISTICS_RESULT_FILE_PATH, deviceName=devName)
        devToLinkUtilizationDataMap[devName] = val
    return devToLinkUtilizationDataMap


def visulaizeFlowSizeVsFCT(iPerfResultObjectsForOneFolder):
    '''
    A simple figure to show flow size vs FCT
    :return:
    '''
    l = sorted(iPerfResultObjectsForOneFolder.iperfResults, key=lambda x: getattr(x[0].end.sum_sent, 'end'))

    flowSizeAsArray = []
    fctAsArray = []
    for r in l:
        #r = IPerfResult(r)
        fctAsArray.append(r[0].getLocalFCT())
        flowSizeAsArray.append(r[0].getTotalBytesSent())
    print(flowSizeAsArray)
    print(fctAsArray)
    #fig, axes = plot.subplots(nrows=1, ncols=1, sharex=True, sharey=True)
    # axes.hist(flowSizeAsArray, 20)
    matplotlib.pyplot.plot.hist(fctAsArray, 10)
    #plot.plot(flowSizeAsArray, fctAsArray)
    matplotlib.pyplot.plot.show()

def visulaizeFlowSizeVsRetransmit(iPerfResultObjectsForOneFolder):
    '''
    A simple figure to show flow size vs FCT
    :return:
    '''
    l = sorted(iPerfResultObjectsForOneFolder.iperfResults, key=lambda x: getattr(x[0].end.sum_sent, 'retransmits')) #Why x[0]? because we are expecting here that there will be only one result in one folder
    #Though that is not really true. Becuase in our system where we are parsing the results as json, we are can handle multiple results. But in later processing we are expecting only one result.
    # Yes this is a kind  of discepancy. But that's how we are working now.

    flowSizeAsArray = []
    totalRetransmitAsArray = []
    for r in l:
        #r = IPerfResult(r)
        totalRetransmitAsArray.append(r[0].getTotalRetransmits())
        flowSizeAsArray.append(r[0].getTotalBytesSent())
    print(flowSizeAsArray)
    print(totalRetransmitAsArray)
    #fig, axes = plot.subplots(nrows=1, ncols=1, sharex=True, sharey=True)
    # axes.hist(flowSizeAsArray, 20)
    matplotlib.pyplot.plot.hist(totalRetransmitAsArray, 500)
    #plot.plot(flowSizeAsArray, fctAsArray)
    matplotlib.pyplot.plot.show()

def groupIperfResultsByFlowTypeBasedOnFlowVolume(iPerfResultObjectsForOneFolder):
    iperfResultsSortedByFlowVolume = sorted(iPerfResultObjectsForOneFolder[2].iperfResults, key=lambda x: getattr(x[0].end.sum_received, 'bytes')) # sort by number of bytes sent
    processedResultsByFlowtypeMap = {} # this is the list where we will keep PerTrafficClassSummaryResults for each of the flow type
    for flowVolume in CC.FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB:
        flowVolumeInbyte = flowVolume * 1024 # because in CC.FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB we have defined size in KB
        perClassResult = rp.PerTrafficClassSummaryResults(flowVolumeInbyte)
        processedResultsByFlowtypeMap[flowVolume]=(perClassResult)
    for iperfResult in iperfResultsSortedByFlowVolume:
        unprocessedResult = iperfResult[0]  # Becuse we are expecting that there will be only one Iperf result in a file.
        for k in processedResultsByFlowtypeMap.keys():
            upperBoundOfAcceptableFlowVolume =(processedResultsByFlowtypeMap.get(k).getTraficClassIdentifierFlowVolume() * (1+(CC.FLOW_VOLUME_IDENTIFIER_VARIATION_LIMIT_IN_PERCENTAGE/100)))
            lowerBoundOfAcceptableFlowVolume = (processedResultsByFlowtypeMap.get(k).getTraficClassIdentifierFlowVolume() * (1-(CC.FLOW_VOLUME_IDENTIFIER_VARIATION_LIMIT_IN_PERCENTAGE/100)))
            if (unprocessedResult.start.test_start.bytes >= lowerBoundOfAcceptableFlowVolume) and (unprocessedResult.start.test_start.bytes <= upperBoundOfAcceptableFlowVolume):
                #print("found in class --"+str(processedResult.getTraficClassIdentifierFlowVolume()))
                processedResultsByFlowtypeMap.get(k).addIperfResult(unprocessedResult)
    return processedResultsByFlowtypeMap

def groupIperfResultsDirectlyByFlowTypeBasedOnFlowVolume(iPerfResultObjectsForOneFolder):
    iperfResultsSortedByFlowVolume = sorted(iPerfResultObjectsForOneFolder.iperfResults, key=lambda x: getattr(x[0].end.sum_received, 'bytes')) # sort by number of bytes sent
    processedResultsByFlowtypeMap = {} # this is the list where we will keep PerTrafficClassSummaryResults for each of the flow type
    for flowVolume in CC.FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB:
        flowVolumeInbyte = flowVolume * 1024 # because in CC.FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB we have defined size in KB
        perClassResult = rp.PerTrafficClassSummaryResults(flowVolumeInbyte)
        processedResultsByFlowtypeMap[flowVolume]=(perClassResult)
    for iperfResult in iperfResultsSortedByFlowVolume:
        unprocessedResult = iperfResult[0]  # Becuse we are expecting that there will be only one Iperf result in a file.
        for k in processedResultsByFlowtypeMap.keys():
            upperBoundOfAcceptableFlowVolume =(processedResultsByFlowtypeMap.get(k).getTraficClassIdentifierFlowVolume() * (1+(CC.FLOW_VOLUME_IDENTIFIER_VARIATION_LIMIT_IN_PERCENTAGE/100)))
            lowerBoundOfAcceptableFlowVolume = (processedResultsByFlowtypeMap.get(k).getTraficClassIdentifierFlowVolume() * (1-(CC.FLOW_VOLUME_IDENTIFIER_VARIATION_LIMIT_IN_PERCENTAGE/100)))
            if (unprocessedResult.start.test_start.bytes >= lowerBoundOfAcceptableFlowVolume) and (unprocessedResult.start.test_start.bytes <= upperBoundOfAcceptableFlowVolume):
                #print("found in class --"+str(processedResult.getTraficClassIdentifierFlowVolume()))
                processedResultsByFlowtypeMap.get(k).addIperfResult(unprocessedResult)
    return processedResultsByFlowtypeMap

def getMinMaxtimeStampOfTheIperfResults(iPerfResultObjectsForOneFolder):
    iperfResultsSortedByTimestamp = sorted(iPerfResultObjectsForOneFolder.iperfResults, key=lambda x: x[0].getEndTimeInSec()) # sort by starting time stamp
    minTimeStamp = iperfResultsSortedByTimestamp[0][0].start.timestamp.timesecs
    maxTimeStamp = iperfResultsSortedByTimestamp[len(iperfResultsSortedByTimestamp)-1][0].getEndTimeInSec()
    maxDuration = iperfResultsSortedByTimestamp[len(iperfResultsSortedByTimestamp)-1][0].end.sum_received.seconds
    return minTimeStamp, maxTimeStamp , maxDuration

class PercentileSummaryResultForOneFlowTypeAndOneIteration(dict):
    def __init__(self):

        self.fctPercentileList = []
        self.datalosspercentileList = []
        self.successfulDataPercentileList = []
        self.retransmitPercentileList = []
        self.tcpThroughputInBPSList = []
        self.fctSTD = 0
        self.dataLossSTD = 0
        self.successfulDataSTD = 0
        self.retransmitSTD = 0
        self.tcpThroughoutSTD = 0
        self.fctAVG = 0
        self.dataLossAVG = 0
        self.successfulDataAVG = 0
        self.retransmitAVG = 0
        self.tcpThroughoutAVG = 0
        dict.__init__(self, fctPercentileList = self.fctPercentileList, datalosspercentileList = self.datalosspercentileList,
                      successfulDataPercentileList = self.successfulDataPercentileList,
                      retransmitPercentileList = self.retransmitPercentileList,
                      tcpThroughputInBPSList = self.tcpThroughputInBPSList,
                      fctSTD =self.fctSTD,
                      dataLossSTD = self.dataLossSTD,
                      successfulDataSTD = self.successfulDataSTD,
                      retransmitSTD = self.retransmitSTD,
                      tcpThroughoutSTD = self.tcpThroughoutSTD,
                      fctAVG = self.fctAVG,
                      dataLossAVG = self.dataLossAVG,
                      successfulDataAVG = self.successfulDataAVG,
                      retransmitAVG = self.retransmitAVG,
                      tcpThroughoutAVG = self.tcpThroughoutAVG)



class MyTuple(dict):
    def __init__(self, percentile, percentileValue):
        dict.__init__(self, percentile=percentile,percentileValue=percentileValue )
        self.percentile = percentile
        self.percentileValue = percentileValue

    def __str__(self):
        return "["+str(self.percentile)+","+str(self.percentileValue)+"]"
    def getMyselfInKBPS(self):
        return (self.percentile, self.percentileValue/(1024*8))
    def dumps(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

def processIPerfResultsFromOneFolderAndOneFlowTypeAndGetPercentileBasedSummary(iPerfResultObjectsForOneFolderOneFlowType, percentileStepSize):
    finalResult = PercentileSummaryResultForOneFlowTypeAndOneIteration()
    for v in range (0,101,percentileStepSize):
        if(len(iPerfResultObjectsForOneFolderOneFlowType.iperfResults)>0): # this logic is for only one traffic class tests. because for only one calss other class will be none
            finalResult.fctPercentileList.append(MyTuple(v,iPerfResultObjectsForOneFolderOneFlowType.getNthPercentilieFCT(v)))
            finalResult.datalosspercentileList.append(MyTuple(v,iPerfResultObjectsForOneFolderOneFlowType.getNthPercentilieDataLoss(v)))
            finalResult.successfulDataPercentileList.append(MyTuple(v,iPerfResultObjectsForOneFolderOneFlowType.getNthPercentilieSuccessfulData(v)))
            finalResult.retransmitPercentileList.append(MyTuple(v,iPerfResultObjectsForOneFolderOneFlowType.getNthPercentilieRetransmit(v)))
            finalResult.tcpThroughputInBPSList.append(MyTuple(v,iPerfResultObjectsForOneFolderOneFlowType.getNthPercentilieTCPThroughputInBPS(v)))
    finalResult.fctSTD = iPerfResultObjectsForOneFolderOneFlowType.getSTDOfFCT()
    finalResult.fctAVG = iPerfResultObjectsForOneFolderOneFlowType.getAvgFCT()
    finalResult.dataLossSTD = iPerfResultObjectsForOneFolderOneFlowType.getSTDOfDataLoss()
    finalResult.dataLossAVG = iPerfResultObjectsForOneFolderOneFlowType.getAvgDataLoss()
    finalResult.successfulDataSTD = iPerfResultObjectsForOneFolderOneFlowType.getSTDOfSuccessfulData()
    finalResult.successfulDataAVG = iPerfResultObjectsForOneFolderOneFlowType.getAVGOfSuccessfulData()
    finalResult.retransmitSTD = iPerfResultObjectsForOneFolderOneFlowType.getSTDOfRetransmit()
    finalResult.retransmitAVG = iPerfResultObjectsForOneFolderOneFlowType.getAVGOfRetransmit()
    finalResult.tcpThroughoutSTD = iPerfResultObjectsForOneFolderOneFlowType.getSTDOfTCPThroughputInBPS()
    finalResult.tcpThroughoutAVG = iPerfResultObjectsForOneFolderOneFlowType.getAVGOfTCPThroughputInBPS()

    return finalResult




def processIPerfResultsFromOneFolderOld(iPerfResultObjectsForOneFolder):
    '''
    Here we will classify the flows according to their traffic class or in general flow size for analyzing the results
    :param iPerfResultObjectsForOneFolder:
    :return:
    '''
    iperfResultsSortedByFlowVolume = sorted(iPerfResultObjectsForOneFolder.iperfResults, key=lambda x: getattr(x[0].end.sum_received, 'bytes')) # sort by number of bytes sent

    processedResultsByFlowtype = [] # this is the list where we will keep PerTrafficClassSummaryResults for each of the flow type
    for flowVolume in CC.FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB:
        flowVolumeInbyte = flowVolume * 1024 # because in CC.FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB we have defined size in KB
        perClassResult = rp.PerTrafficClassSummaryResults(flowVolumeInbyte)
        processedResultsByFlowtype.append(perClassResult)

    startTimeOfCtrlrStaticticsTobeProcessedForFolder = 9999999999999
    endTimeOfCtrlrStaticticsTobeProcessedForFolder = 0
    for iperfResult in iperfResultsSortedByFlowVolume:
        unprocessedResult = iperfResult[0]  # Becuse we are expecting that there will be only one Iperf result in a file.
        # And iperfResult[0]  is an instance of  <class 'testAndMeasurement.ResultParsers.IPerfResult'>
        if (startTimeOfCtrlrStaticticsTobeProcessedForFolder > unprocessedResult.start.timestamp.timesecs):
            startTimeOfCtrlrStaticticsTobeProcessedForFolder = unprocessedResult.start.timestamp.timesecs
        if (endTimeOfCtrlrStaticticsTobeProcessedForFolder < unprocessedResult.start.timestamp.timesecs):
            endTimeOfCtrlrStaticticsTobeProcessedForFolder = unprocessedResult.start.timestamp.timesecs
        for processedResult in processedResultsByFlowtype:
            upperBoundOfAcceptableFlowVolume =(processedResult.getTraficClassIdentifierFlowVolume() * (1+(CC.FLOW_VOLUME_IDENTIFIER_VARIATION_LIMIT_IN_PERCENTAGE/100)))
            lowerBoundOfAcceptableFlowVolume = (processedResult.getTraficClassIdentifierFlowVolume() * (1-(CC.FLOW_VOLUME_IDENTIFIER_VARIATION_LIMIT_IN_PERCENTAGE/100)))
            if (unprocessedResult.start.test_start.bytes >= lowerBoundOfAcceptableFlowVolume) and (unprocessedResult.start.test_start.bytes <= upperBoundOfAcceptableFlowVolume):
                #print("found in class --"+str(processedResult.getTraficClassIdentifierFlowVolume()))
                processedResult.addIperfResult(unprocessedResult)
    print(startTimeOfCtrlrStaticticsTobeProcessedForFolder)
    print(endTimeOfCtrlrStaticticsTobeProcessedForFolder)
    print(datetime.fromtimestamp(startTimeOfCtrlrStaticticsTobeProcessedForFolder).strftime("%A, %B %d, %Y %I:%M:%S"))
    print(datetime.fromtimestamp(endTimeOfCtrlrStaticticsTobeProcessedForFolder).strftime("%A, %B %d, %Y %I:%M:%S"))
    print(processedResultsByFlowtype)



    for r in processedResultsByFlowtype:
        fctPercentileList = []
        #for row in r.iperfResults:
        for v in range (10,101,10):
            if(len(r.iperfResults)>0): # this logic is for only one traffic class tests. because for only one calss other class will be none
                fctPercentileList.append(r.getNthPercentilieFCT(v))
        if(len(r.iperfResults) >0 ):
            print("flow type -- ",r.getTraficClassIdentifierFlowVolume())
            print("total flow in this category -- ",len(r.iperfResults))
            print("Avg FCT --",r.getAvgFCT())
            print("FCT list is "+str(fctPercentileList))

    for r in processedResultsByFlowtype:
        datalosspercentileList = []
        successfulDataPercentileList = []
        for v in range (10,101,10):
            if(len(r.iperfResults)>0): # this logic is for only one traffic class tests. because for only one calss other class will be none
                datalosspercentileList.append(r.getNthPercentilieDataLoss(v))
                successfulDataPercentileList.append((r.getNthPercentilieSuccessfulData(v)))
        if(len(r.iperfResults) >0 ):
            print("flow type -- ",r.getTraficClassIdentifierFlowVolume())
            print("total flow in this category -- ",len(r.iperfResults))
            print("Avg data los --", r.getAvgDataLoss())
            print("data loss list is "+str(datalosspercentileList))
            print("Successful Data volume list is "+str(successfulDataPercentileList))
    for r in processedResultsByFlowtype:
        retransmitPercentileList = []
        for v in range (10,101,10):
            if(len(r.iperfResults)>0): # this logic is for only one traffic class tests. because for only one calss other class will be none
                retransmitPercentileList.append(r.getNthPercentilieRetransmit(v))
        if(len(r.iperfResults) >0 ):
            print("flow type -- ",r.getTraficClassIdentifierFlowVolume())
            print("total flow in this category -- ",len(r.iperfResults))
            print("Retransmit loss list is "+str(retransmitPercentileList))
    return processedResultsByFlowtype

def processIPerfResultsFromOneFolderForAllFlowCombinedly(iPerfResultObjectsForOneFolder):
    iperfResultsSortedBySuccessfulFlowVolume  = sorted(iPerfResultObjectsForOneFolder.iperfResults, key=lambda x: x[0].end.sum_received.bytes)
    flowVolumeVsFctList = [( x[0].end.sum_received.bytes , x[0].end.sum_received.seconds) for x in iperfResultsSortedBySuccessfulFlowVolume]
    flowVolumeVsThroughputinBytePerSecond = [( x[0].end.sum_received.bytes , x[0].end.sum_received.bits_per_second/8) for x in iperfResultsSortedBySuccessfulFlowVolume]
    print(flowVolumeVsThroughputinBytePerSecond)
    print(len(flowVolumeVsThroughputinBytePerSecond))







class PercentileSummaryResultForOneIterationOfTestCase(dict):
    def __init__(self, shortFlowPercentileBasedResults, largeFlowPercentileBasedResults):
        self.largeFlowPercentileBasedResults = largeFlowPercentileBasedResults
        self.shortFlowPercentileBasedResults = shortFlowPercentileBasedResults
        # dict.__init__(self, shortFlowPercentileBasedResults = shortFlowPercentileBasedResults, largeFlowPercentileBasedResults=largeFlowPercentileBasedResults )
        pass

def getSummaryForOneIteration(iPerfResultObjectsForOneIteration ):
    percentileStepSize= PERCENTILE_STEP_SIZE
    iperfResultsGroupedByFlowTypeForOneIteration = groupIperfResultsByFlowTypeBasedOnFlowVolume(iPerfResultObjectsForOneIteration)
    shortFlowPercentileBasedResults = processIPerfResultsFromOneFolderAndOneFlowTypeAndGetPercentileBasedSummary(
        iperfResultsGroupedByFlowTypeForOneIteration.get(CC.FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB[0]), percentileStepSize)
    largeFlowPercentileBasedResults = processIPerfResultsFromOneFolderAndOneFlowTypeAndGetPercentileBasedSummary(
        iperfResultsGroupedByFlowTypeForOneIteration.get(CC.FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB[1]), percentileStepSize)
    val = PercentileSummaryResultForOneIterationOfTestCase( shortFlowPercentileBasedResults, largeFlowPercentileBasedResults)
    return val



def collectResultOfAllIteratioOfTestCaseGroupedByFlowType(folderPath):
    onlyclientResultFolders = [f for f in listdir(folderPath) if ((not isfile(join(folderPath, f))) and ( (f.startswith("client-logs-"))))]   #SKip the files that are server logs
    percentileSummaryForResultsOfAllIteration = []
    for oneIterationResultFolder in onlyclientResultFolders:
        resultFolderPathForIteration = join(folderPath, oneIterationResultFolder)
        allIperfResultForOneIteration = parseIperfResultsFromFolder(folderPath = resultFolderPathForIteration)
        iperfPercentileResultsGroupedByFlowTypeForOneIteration = getSummaryForOneIteration(allIperfResultForOneIteration)
        percentileSummaryForResultsOfAllIteration.append(iperfPercentileResultsGroupedByFlowTypeForOneIteration)
    return percentileSummaryForResultsOfAllIteration

def getAverageOfAllIterationsGroupedByFlowType(allIterationResultOfATestCase):
    sumResult = PercentileSummaryResultForOneIterationOfTestCase(PercentileSummaryResultForOneFlowTypeAndOneIteration(), PercentileSummaryResultForOneFlowTypeAndOneIteration())
    shortCount = 0
    largeCount = 0

    for r in allIterationResultOfATestCase:
        # only short summary
        #print(r.shortFlowPercentileBasedResults)
        shortFlowAvgResult = PercentileSummaryResultForOneFlowTypeAndOneIteration()
        if( len(r.shortFlowPercentileBasedResults.fctPercentileList)> 0 ):
            shortCount = shortCount + 1
            if((len(sumResult.shortFlowPercentileBasedResults.fctPercentileList)<=0) and (len(r.shortFlowPercentileBasedResults.fctPercentileList) >0)): #Means first time. so need to allocate space
                for i in range(0,len(r.shortFlowPercentileBasedResults.fctPercentileList)): #Creating empty space
                    sumResult.shortFlowPercentileBasedResults.fctPercentileList.append(MyTuple(r.shortFlowPercentileBasedResults.fctPercentileList[i].percentile,0))
                    sumResult.shortFlowPercentileBasedResults.datalosspercentileList.append(MyTuple(r.shortFlowPercentileBasedResults.datalosspercentileList[i].percentile,0))
                    sumResult.shortFlowPercentileBasedResults.successfulDataPercentileList.append(MyTuple(r.shortFlowPercentileBasedResults.successfulDataPercentileList[i].percentile,0.0))
                    sumResult.shortFlowPercentileBasedResults.retransmitPercentileList.append(MyTuple(r.shortFlowPercentileBasedResults.retransmitPercentileList[i].percentile,0.0))
                    sumResult.shortFlowPercentileBasedResults.tcpThroughputInBPSList.append(MyTuple(r.shortFlowPercentileBasedResults.tcpThroughputInBPSList[i].percentile,0.0))
            for i in range(0,len(r.shortFlowPercentileBasedResults.fctPercentileList)):
                sumResult.shortFlowPercentileBasedResults.fctPercentileList[i].percentileValue =sumResult.shortFlowPercentileBasedResults.fctPercentileList[i].percentileValue + r.shortFlowPercentileBasedResults.fctPercentileList[i].percentileValue
                sumResult.shortFlowPercentileBasedResults.datalosspercentileList[i].percentileValue =sumResult.shortFlowPercentileBasedResults.datalosspercentileList[i].percentileValue + r.shortFlowPercentileBasedResults.datalosspercentileList[i].percentileValue
                sumResult.shortFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue =sumResult.shortFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue +  r.shortFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue
                sumResult.shortFlowPercentileBasedResults.retransmitPercentileList[i].percentileValue =sumResult.shortFlowPercentileBasedResults.retransmitPercentileList[i].percentileValue + r.shortFlowPercentileBasedResults.retransmitPercentileList[i].percentileValue
                sumResult.shortFlowPercentileBasedResults.tcpThroughputInBPSList[i].percentileValue =sumResult.shortFlowPercentileBasedResults.tcpThroughputInBPSList[i].percentileValue + r.shortFlowPercentileBasedResults.tcpThroughputInBPSList[i].percentileValue
            sumResult.shortFlowPercentileBasedResults.fctSTD = sumResult.shortFlowPercentileBasedResults.fctSTD  +r.shortFlowPercentileBasedResults.fctSTD
            sumResult.shortFlowPercentileBasedResults.dataLossSTD = sumResult.shortFlowPercentileBasedResults.dataLossSTD  + r.shortFlowPercentileBasedResults.dataLossSTD
            sumResult.shortFlowPercentileBasedResults.successfulDataSTD = sumResult.shortFlowPercentileBasedResults.successfulDataSTD + r.shortFlowPercentileBasedResults.successfulDataSTD
            sumResult.shortFlowPercentileBasedResults.retransmitSTD = sumResult.shortFlowPercentileBasedResults.retransmitSTD + r.shortFlowPercentileBasedResults.retransmitSTD
            sumResult.shortFlowPercentileBasedResults.tcpThroughoutSTD = sumResult.shortFlowPercentileBasedResults.tcpThroughoutSTD + r.shortFlowPercentileBasedResults.tcpThroughoutSTD
            #print(str(r.shortFlowPercentileBasedResults.fctPercentileList[i].percentile) + "-"+ str(r.shortFlowPercentileBasedResults.fctPercentileList[i].percentileValue))
            #print(shortCount)
        if (len(r.largeFlowPercentileBasedResults.fctPercentileList)> 0):
            largeCount = largeCount+1
            if((len(sumResult.largeFlowPercentileBasedResults.fctPercentileList)<=0) and (len(r.largeFlowPercentileBasedResults.fctPercentileList) >0)): #Means first time. so need to allocate space
                for i in range(0,len(r.largeFlowPercentileBasedResults.fctPercentileList)): #Creating empty space
                    sumResult.largeFlowPercentileBasedResults.fctPercentileList.append(MyTuple(r.largeFlowPercentileBasedResults.fctPercentileList[i].percentile,0))
                    sumResult.largeFlowPercentileBasedResults.datalosspercentileList.append(MyTuple(r.largeFlowPercentileBasedResults.datalosspercentileList[i].percentile,0))
                    sumResult.largeFlowPercentileBasedResults.successfulDataPercentileList.append(MyTuple(r.largeFlowPercentileBasedResults.successfulDataPercentileList[i].percentile,0.0))
                    sumResult.largeFlowPercentileBasedResults.retransmitPercentileList.append(MyTuple(r.largeFlowPercentileBasedResults.retransmitPercentileList[i].percentile,0.0))
                    sumResult.largeFlowPercentileBasedResults.tcpThroughputInBPSList.append(MyTuple(r.largeFlowPercentileBasedResults.tcpThroughputInBPSList[i].percentile,0.0))
            for i in range(0,len(r.largeFlowPercentileBasedResults.fctPercentileList)):
                sumResult.largeFlowPercentileBasedResults.fctPercentileList[i].percentileValue =sumResult.largeFlowPercentileBasedResults.fctPercentileList[i].percentileValue + r.largeFlowPercentileBasedResults.fctPercentileList[i].percentileValue
                sumResult.largeFlowPercentileBasedResults.datalosspercentileList[i].percentileValue =sumResult.largeFlowPercentileBasedResults.datalosspercentileList[i].percentileValue + r.largeFlowPercentileBasedResults.datalosspercentileList[i].percentileValue
                sumResult.largeFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue =sumResult.largeFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue +  r.largeFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue
                sumResult.largeFlowPercentileBasedResults.retransmitPercentileList[i].percentileValue =sumResult.largeFlowPercentileBasedResults.retransmitPercentileList[i].percentileValue + r.largeFlowPercentileBasedResults.retransmitPercentileList[i].percentileValue
                sumResult.largeFlowPercentileBasedResults.tcpThroughputInBPSList[i].percentileValue =sumResult.largeFlowPercentileBasedResults.tcpThroughputInBPSList[i].percentileValue + r.largeFlowPercentileBasedResults.tcpThroughputInBPSList[i].percentileValue
            #print(largeCount)
            sumResult.largeFlowPercentileBasedResults.fctSTD = sumResult.largeFlowPercentileBasedResults.fctSTD+ r.largeFlowPercentileBasedResults.fctSTD
            sumResult.largeFlowPercentileBasedResults.dataLossSTD = sumResult.largeFlowPercentileBasedResults.dataLossSTD+ r.largeFlowPercentileBasedResults.dataLossSTD
            sumResult.largeFlowPercentileBasedResults.successfulDataSTD =sumResult.largeFlowPercentileBasedResults.successfulDataSTD+ r.largeFlowPercentileBasedResults.successfulDataSTD
            sumResult.largeFlowPercentileBasedResults.retransmitSTD =sumResult.largeFlowPercentileBasedResults.retransmitSTD+ r.largeFlowPercentileBasedResults.retransmitSTD
            sumResult.largeFlowPercentileBasedResults.tcpThroughoutSTD = sumResult.largeFlowPercentileBasedResults.tcpThroughoutSTD+ r.largeFlowPercentileBasedResults.tcpThroughoutSTD

    #Taking the average of shortflow
    avgResult = PercentileSummaryResultForOneIterationOfTestCase(PercentileSummaryResultForOneFlowTypeAndOneIteration(), PercentileSummaryResultForOneFlowTypeAndOneIteration())
    if(shortCount >0):
        for i in range(0,len(sumResult.shortFlowPercentileBasedResults.fctPercentileList)):
            avgResult.shortFlowPercentileBasedResults.fctPercentileList.append(MyTuple(sumResult.shortFlowPercentileBasedResults.fctPercentileList[i].percentile, sumResult.shortFlowPercentileBasedResults.fctPercentileList[i].percentileValue / shortCount))
            avgResult.shortFlowPercentileBasedResults.datalosspercentileList.append(MyTuple(sumResult.shortFlowPercentileBasedResults.datalosspercentileList[i].percentile, sumResult.shortFlowPercentileBasedResults.datalosspercentileList[i].percentileValue / shortCount))
            avgResult.shortFlowPercentileBasedResults.successfulDataPercentileList.append(MyTuple(sumResult.shortFlowPercentileBasedResults.successfulDataPercentileList[i].percentile,sumResult.shortFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue/ shortCount))
            avgResult.shortFlowPercentileBasedResults.retransmitPercentileList.append(MyTuple(sumResult.shortFlowPercentileBasedResults.retransmitPercentileList[i].percentile, sumResult.shortFlowPercentileBasedResults.retransmitPercentileList[i].percentileValue / shortCount))
            avgResult.shortFlowPercentileBasedResults.tcpThroughputInBPSList.append(MyTuple(sumResult.shortFlowPercentileBasedResults.tcpThroughputInBPSList[i].percentile,sumResult.shortFlowPercentileBasedResults.tcpThroughputInBPSList[i].percentileValue / shortCount))
    #Taking the average of largeflows
        sumResult.shortFlowPercentileBasedResults.fctSTD = sumResult.shortFlowPercentileBasedResults.fctSTD  / shortCount
        sumResult.shortFlowPercentileBasedResults.dataLossSTD = sumResult.shortFlowPercentileBasedResults.dataLossSTD  / shortCount
        sumResult.shortFlowPercentileBasedResults.successfulDataSTD = sumResult.shortFlowPercentileBasedResults.successfulDataSTD / shortCount
        sumResult.shortFlowPercentileBasedResults.retransmitSTD = sumResult.shortFlowPercentileBasedResults.retransmitSTD / shortCount
        sumResult.shortFlowPercentileBasedResults.tcpThroughoutSTD = sumResult.shortFlowPercentileBasedResults.tcpThroughoutSTD / shortCount


    if(largeCount >0):
        for i in range(0,len(sumResult.largeFlowPercentileBasedResults.fctPercentileList)):
            avgResult.largeFlowPercentileBasedResults.fctPercentileList.append(MyTuple(sumResult.largeFlowPercentileBasedResults.fctPercentileList[i].percentile ,sumResult.largeFlowPercentileBasedResults.fctPercentileList[i].percentileValue / largeCount))
            avgResult.largeFlowPercentileBasedResults.datalosspercentileList.append(MyTuple(sumResult.largeFlowPercentileBasedResults.datalosspercentileList[i].percentile,sumResult.largeFlowPercentileBasedResults.datalosspercentileList[i].percentileValue / largeCount))
            avgResult.largeFlowPercentileBasedResults.successfulDataPercentileList.append(MyTuple(sumResult.largeFlowPercentileBasedResults.successfulDataPercentileList[i].percentile ,sumResult.largeFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue / largeCount))
            avgResult.largeFlowPercentileBasedResults.retransmitPercentileList.append(MyTuple(sumResult.largeFlowPercentileBasedResults.retransmitPercentileList[i].percentile,sumResult.largeFlowPercentileBasedResults.retransmitPercentileList[i].percentileValue / largeCount))
            avgResult.largeFlowPercentileBasedResults.tcpThroughputInBPSList.append(MyTuple(sumResult.largeFlowPercentileBasedResults.tcpThroughputInBPSList[i].percentile , sumResult.largeFlowPercentileBasedResults.tcpThroughputInBPSList[i].percentileValue / largeCount))
        sumResult.largeFlowPercentileBasedResults.fctSTD = sumResult.largeFlowPercentileBasedResults.fctSTD / largeCount
        sumResult.largeFlowPercentileBasedResults.dataLossSTD = sumResult.largeFlowPercentileBasedResults.dataLossSTD / largeCount
        sumResult.largeFlowPercentileBasedResults.successfulDataSTD =sumResult.largeFlowPercentileBasedResults.successfulDataSTD / largeCount
        sumResult.largeFlowPercentileBasedResults.retransmitSTD =sumResult.largeFlowPercentileBasedResults.retransmitSTD / largeCount
        sumResult.largeFlowPercentileBasedResults.tcpThroughoutSTD = sumResult.largeFlowPercentileBasedResults.tcpThroughoutSTD / largeCount
    #print(avgResult)
    # for r in avgResult.shortFlowPercentileBasedResults.fctPercentileList:
    #     print(str(r.percentile) + "-"+ str(r.percentileValue))

    return avgResult
def autolabel(axes, rects):
    """
    Attach a text label above each bar displaying its height
    """
    for rect in rects:
        height = rect.get_height()
        if(height > (0.9* axes.get_ylim()[1])):
            height = 0.9*height
        else:
            height = 1.01*height
        axes.text(rect.get_x() + rect.get_width()/2., height,
                '%d' % int(height),
                ha='center', va='bottom',fontsize=3,fontweight='bold',rotation=90,wrap=True)

def visualizeSinglePerformanceMetrics(shortFlowResultSet1, shortFlowResultSet2,
                                      shortFlowLegend1, shortFlowLegend2,
                                      largeFlowResutSet1,LargeFlowResultSet2,
                                      largeFlowLegend1, largeFlowLegend2,
                                      xlabel, ylabel,testCaseTitleName,
                                      destinationfolder, showShort, showLarge):
    barWidth = 3
    x=1.25
    # x1 = [p.percentile+(-2*barWidth+x) for p in shortFlowResultSet1]
    # y1 = [p.percentileValue for p in shortFlowResultSet1]
    # x2 = [p.percentile+(-barWidth+x)  for p in shortFlowResultSet2]
    # y2 = [p.percentileValue for p in shortFlowResultSet2]
    # x3 = [p.percentile+(0*barWidth+x) for p in largeFlowResutSet1]
    # y3 = [p.percentileValue for p in largeFlowResutSet1]
    # x4 = [p.percentile+(1*barWidth+x) for p in LargeFlowResultSet2]
    # y4 = [p.percentileValue for p in LargeFlowResultSet2]

    x1 = [p.percentile for p in shortFlowResultSet1]
    y1 = [p.percentileValue for p in shortFlowResultSet1]
    x2 = [p.percentile  for p in shortFlowResultSet2]
    y2 = [p.percentileValue for p in shortFlowResultSet2]
    x3 = [p.percentile for p in largeFlowResutSet1]
    y3 = [p.percentileValue for p in largeFlowResutSet1]
    x4 = [p.percentile for p in LargeFlowResultSet2]
    y4 = [p.percentileValue for p in LargeFlowResultSet2]
    # fig = plt.figure(constrained_layout=True)
    # gs0 = gridspec.GridSpec(1, 1, figure=fig)
    # gs1 = gridspec.GridSpecFromSubplotSpec(1, 1, subplot_spec=gs0[0])
    fig, axes = plt.subplots(1,constrained_layout = True)
    #size = fig.get_size_inches()*fig.dpi # size in pixels
    # size = fig.get_size_inches() # size in pixels
    #figsize=(size[0],size[1]*1.05)
    #fig.set_size_inches(w=size[0],h=size[1]*1.5)
    myLineWidth = 2
    if (showShort == True):
        axes.plot(x1, y1,'b--', label=shortFlowLegend1,linewidth=myLineWidth)
        axes.plot(x2, y2,'r--', label=shortFlowLegend2,linewidth=myLineWidth)
        for i_x, i_y in zip(x1, y1):
            #plt.text(i_x, i_y, '({:0.2f}, {:0.2f})'.format(i_x, i_y), fontsize=10)
            label = '({:0.2f}, {:0.2f})'.format(i_x, i_y)
            # plt.annotate(label, # this is the text
            #              (i_x,i_y), # this is the point to label
            #              textcoords="offset points", # how to position the text
            #              xytext=(30,-5), # distance from text to points (x,y)
            #              ha='center',fontsize=9,fontweight='bold',rotation=0,wrap=True) # horizontal alignment can be left, right or center
        for i_x, i_y in zip(x2, y2):
            #plt.text(i_x, i_y, '({:0.2f}, {:0.2f})'.format(i_x, i_y), fontsize=10)
            label = '({:0.2f}, {:0.2f})'.format(i_x, i_y)
            # plt.annotate(label, # this is the text
            #              (i_x,i_y), # this is the point to label
            #              textcoords="offset points", # how to position the text
            #              xytext=(-30,-5), # distance from text to points (x,y)
            #              ha='center',fontsize=9,fontweight='bold',rotation=0,wrap=True) # horizontal alignment can be left, right or center
    if(showLarge == True):
        axes.plot(x3, y3, 'g--', label=largeFlowLegend1,linewidth=myLineWidth)
        axes.plot(x4, y4, 'y--', label=largeFlowLegend2,linewidth=myLineWidth)
        for i_x, i_y in zip(x3, y3):
            #plt.text(i_x, i_y, '({:0.2f}, {:0.2f})'.format(i_x, i_y), fontsize=10)
            label = '({:0.2f}, {:0.2f})'.format(i_x, i_y)
            # plt.annotate(label, # this is the text
            #              (i_x,i_y), # this is the point to label
            #              textcoords="offset points", # how to position the text
            #              xytext=(30,-5), # distance from text to points (x,y)
            #              ha='center',fontsize=9,fontweight='bold',rotation=0,wrap=True) # horizontal alignment can be left, right or center
        for i_x, i_y in zip(x4, y4):
            #plt.text(i_x, i_y, '({:0.2f}, {:0.2f})'.format(i_x, i_y), fontsize=10)
            label = '({:0.2f}, {:0.2f})'.format(i_x, i_y)
            # plt.annotate(label, # this is the text
            #              (i_x,i_y), # this is the point to label
            #              textcoords="offset points", # how to position the text
            #              xytext=(-30,-5), # distance from text to points (x,y)
            #              ha='center',fontsize=9,fontweight='bold',rotation=0,wrap=True) # horizontal alignment can be left, right or center


    # axes.xaxis.set_ticks([])
    # axes.yaxis.set_ticks([])
    # for x,y in zip(x1,y1):
    #     label = f"({x},{y})"
    #
    #     plt.annotate(label, # this is the text
    #                  (x,y), # this is the point to label
    #                  textcoords="offset points", # how to position the text
    #                  xytext=(0,1), # distance from text to points (x,y)
    #                  ha='center',fontsize=3,fontweight='bold',rotation=0,wrap=True) # horizontal alignment can be left, right or center

    # if (showShort == True):
    #     bar1 = axes.bar(x1, y1, width = barWidth, label=shortFlowLegend1)
    #     bar2 = axes.bar(x2, y2, width = barWidth, label=shortFlowLegend2)
    #     autolabel(axes,bar1)
    #     autolabel(axes,bar2)
    # if(showLarge == True):
    #     bar3 = axes.bar(x3, y3, width = barWidth, label=largeFlowLegend1)
    #     bar4 = axes.bar(x4, y4, width = barWidth, label=largeFlowLegend2)
    #     autolabel(axes,bar3)
    #     autolabel(axes,bar4)


    # axes.legend(labels=[shortFlowLegend1, shortFlowLegend2, largeFlowLegend1, largeFlowLegend2])
    # axes.legend(loc='upper center', bbox_to_anchor=(0.46, -0.1), ncol=4)


    # axes.xaxis.set_ticks(fontsize=3,fontweight='bold')
    # axes.yaxis.set_ticks(fontsize=3,fontweight='bold')
    axes.tick_params(axis='both', which='major', labelsize=1)
    axes.tick_params(axis='both', which='minor', labelsize=1)
    # plt.plot(x1,y1,marker='.')
    # # axes.set_xticks(x1)
    # # axes.set_yticks(y1)
    # plt.plot(x2,y2,marker='.')
    # # axes.set_xticks(x2)
    # # axes.set_yticks(y2)
    # plt.plot(x3,y3,marker='.')
    # # axes.set_xticks(x3)
    # # axes.set_yticks(y3)
    # plt.plot(x4,y4,marker='.')
    # axes.set_xticks(x4)
    # axes.set_yticks(y4)
    # for i_x, i_y in zip(x1, y1):
    #     plt.text(i_x, i_y, '({}, {})'.format(i_x, i_y))
    # for i_x, i_y in zip(x2, y2):
    #     plt.text(i_x, i_y, '({}, {})'.format(i_x, i_y))
    # for i_x, i_y in zip(x3, y3):
    #     plt.text(i_x, i_y, '({}, {})'.format(i_x, i_y))
    # for i_x, i_y in zip(x4, y4):
    #     plt.text(i_x, i_y, '({}, {})'.format(i_x, i_y))
    axes.set_xlabel(xlabel,fontsize=20,fontweight='bold')
    axes.set_ylabel(ylabel,fontsize=20,fontweight='bold')
    axes.legend(loc="upper left", ncol=4)
    axes.legend( ncol=4)
    axes.legend(fontsize=10)
    #axes.set_title(testCaseTitleName)
    #plt.title(testCaseTitleName, x=-.75, y =-.15)
    if(showShort==True) and (showLarge == True):
        plt.savefig(str(destinationfolder)+"/"+testCaseTitleName.replace(" ", "")+".pdf")
    elif(showShort == True) :
        plt.savefig(str(destinationfolder)+"/"+testCaseTitleName.replace(" ", "")+"ForShortFlow.pdf")
    elif(showLarge == True) :
        plt.savefig(str(destinationfolder)+"/"+testCaseTitleName.replace(" ", "")+"ForLargeFlow.pdf")
    #Write a function for exporting in file
    pass

def generateTimeByThroughputGraphForOneIteration(iPerfResultsFolder1,iPerfResultsFolder2,resultSet1, resultSet2, avgResultSet1, avgResultSet2,algorithm1, algorithm2, folderToSaveResult):
    # resultForFolder1 = parseIperfResultsFromFolder(folderPath = iPerfResultsFolder1+"/client-logs-0")[2]
    # resultForFolder2 = parseIperfResultsFromFolder(folderPath = iPerfResultsFolder2+"/client-logs-0")[2]
    #
    # iperfResultsSortedByFinishTime1 = sorted(resultForFolder1.iperfResults, key=lambda x: x[0].getEndTimeInSec()) # sort by starting time stamp
    # iperfResultsSortedByFinishTime2 = sorted(resultForFolder2.iperfResults, key=lambda x: x[0].getEndTimeInSec()) # sort by starting time stamp
    # timeByThroughputList1 = getTimeByThroughPutInKB(iperfResultsSortedByFinishTime1)
    # timeByThroughputList2 = getTimeByThroughPutInKB(iperfResultsSortedByFinishTime2)
    # x1 = [p[0] for p in timeByThroughputList1]
    # y1 = [p[1] for p in timeByThroughputList1]
    # x2 = [p[0] for p in timeByThroughputList2]
    # y2 = [p[1] for p in timeByThroughputList2]
    #
    # fig, axes = plt.subplots(1,constrained_layout = True)
    # myLineWidth = 1
    # axes.plot(x1, y1,'b--', label=str(algorithm1),linewidth=myLineWidth)
    # axes.plot(x2, y2,'r--', label=str(algorithm2),linewidth=myLineWidth)
    # axes.set_xlabel("Time ", fontsize=3,fontweight='bold')
    # axes.set_ylabel("Cumulative Throughput",fontsize=3,fontweight='bold')
    # axes.legend(loc="upper left")
    # plt.savefig(str(folderToSaveResult)+"/"+"ToalThrougputpdf")

    startTime, end,resultForFolder1 = parseIperfResultsFromFolder(folderPath = iPerfResultsFolder1+"/client-logs-0")
    startTime, end,resultForFolder2 = parseIperfResultsFromFolder(folderPath = iPerfResultsFolder2+"/client-logs-0")
    iperfResultsgrouedByflowTypeForFolder1 = groupIperfResultsDirectlyByFlowTypeBasedOnFlowVolume(resultForFolder1)
    iperfResultsgrouedByflowTypeForFolder2 =  groupIperfResultsDirectlyByFlowTypeBasedOnFlowVolume(resultForFolder2)
    # valTobeSorted = iperfResultsgrouedByflowTypeForFolder1.get(CC.FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB[0]).iperfResults
    # sortedVal = sorted(valTobeSorted, key=lambda x: x[0].getEndTimeInSec())
    shortFlowSortedByEndtimeFolder1 = sorted(iperfResultsgrouedByflowTypeForFolder1.get(CC.FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB[0]).iperfResults, key=lambda x: x.getEndTimeInSec())
    shortFlowSortedByEndtimeFolder2 = sorted(iperfResultsgrouedByflowTypeForFolder2.get(CC.FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB[0]).iperfResults, key=lambda x: x.getEndTimeInSec())
    largeFlowSortedByEndtimeFolder1 = sorted(iperfResultsgrouedByflowTypeForFolder1.get(CC.FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB[1]).iperfResults, key=lambda x: x.getEndTimeInSec())
    largeFlowSortedByEndtimeFolder2 = sorted(iperfResultsgrouedByflowTypeForFolder2.get(CC.FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB[1]).iperfResults, key=lambda x: x.getEndTimeInSec())
    timeByThroughputListForShortFlowFolder1 = getTimeByThroughPutInKB(shortFlowSortedByEndtimeFolder1)
    timeByThroughputListForShortFlowFolder2 = getTimeByThroughPutInKB(shortFlowSortedByEndtimeFolder2)
    timeByThroughputListForLargeFlowFolder1 = getTimeByThroughPutInKB(largeFlowSortedByEndtimeFolder1)
    timeByThroughputListForLargeFlowFolder2 = getTimeByThroughPutInKB(largeFlowSortedByEndtimeFolder2)

    x11 = [p[0] for p in timeByThroughputListForShortFlowFolder1]
    y11 = [p[1] for p in timeByThroughputListForShortFlowFolder1]
    x21 = [p[0] for p in timeByThroughputListForShortFlowFolder2]
    y21 = [p[1] for p in timeByThroughputListForShortFlowFolder2]

    x12 = [p[0] for p in timeByThroughputListForLargeFlowFolder1]
    y12 = [p[1] for p in timeByThroughputListForLargeFlowFolder1]
    x22 = [p[0] for p in timeByThroughputListForLargeFlowFolder2]
    y22 = [p[1] for p in timeByThroughputListForLargeFlowFolder2]

    fig, axes = plt.subplots(1,constrained_layout = True)
    myLineWidth = 2
    axes.plot(x11, y11,'b--', label=str(algorithm1),linewidth=myLineWidth)
    axes.plot(x21, y21,'r--', label=str(algorithm2),linewidth=myLineWidth)

    axes.set_xlabel("Time ", fontsize=3,fontweight='bold')
    axes.set_ylabel("Cumulative Throughput",fontsize=5,fontweight='bold')
    axes.legend(loc="upper left")
    plt.savefig(str(folderToSaveResult)+"/"+"ShortFlowTimebyToalThrougputpdf")
    fig, axes = plt.subplots(1,constrained_layout = True)
    myLineWidth = 2
    axes.plot(x12, y12,'b--', label=str(algorithm1),linewidth=myLineWidth)
    axes.plot(x22, y22,'r--', label=str(algorithm2),linewidth=myLineWidth)
    axes.set_xlabel("Time ", fontsize=3,fontweight='bold')
    axes.set_ylabel("Cumulative Throughput",fontsize=5,fontweight='bold')
    axes.legend(loc="upper left")
    plt.savefig(str(folderToSaveResult)+"/"+"LArgeFlowTimebyToalThrougputpdf")

def plotNthPercenTileFCTVsTotalThroughout(iPerfResultsFolder1,iPerfResultsFolder2,resultSet1, resultSet2, avgResultSet1, avgResultSet2,algorithm1, algorithm2, folderToSaveResult):
    xAxisValuesForShortFlows1 = []
    xAxisValuesForShortFlows2 = []
    yAxisValuesForShortFlows1 = []
    yAxisValuesForLargeFlows1 = []
    shortFlowYAxisTotal1 = 0
    LargeFlowYAxisTotal1 = 0
    xAxisValuesForLargeFlows1 = []
    xAxisValuesForLargeFlows2 = []
    yAxisValuesForShortFlows2 = []
    yAxisValuesForLargeFlows2 = []
    shortFlowYAxisTotal2 = 0
    LargeFlowYAxisTotal2 = 0
    for i in range (0, len(avgResultSet1.shortFlowPercentileBasedResults.fctPercentileList)):
        #xAxisValuesForShortFlows1.append(i*PERCENTILE_STEP_SIZE)
        # xAxisValuesForShortFlows1.append(avgResultSet1.shortFlowPercentileBasedResults.fctPercentileList[i].percentileValue)
        # shortFlowYAxisTotal1 = shortFlowYAxisTotal1 + (avgResultSet1.shortFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue/avgResultSet1.shortFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue)
        # xAxisValuesForLargeFlows1.append(avgResultSet1.largeFlowPercentileBasedResults.fctPercentileList[i].percentileValue)
        # LargeFlowYAxisTotal1 = LargeFlowYAxisTotal1 + (avgResultSet1.largeFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue/avgResultSet1.largeFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue)
        # xAxisValuesForShortFlows2.append(avgResultSet2.shortFlowPercentileBasedResults.fctPercentileList[i].percentileValue)
        # shortFlowYAxisTotal2 = shortFlowYAxisTotal2 + (avgResultSet2.shortFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue/avgResultSet1.shortFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue)
        # xAxisValuesForLargeFlows2.append(avgResultSet2.largeFlowPercentileBasedResults.fctPercentileList[i].percentileValue)
        # LargeFlowYAxisTotal2 = LargeFlowYAxisTotal2 + (avgResultSet2.largeFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue/avgResultSet1.largeFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue)

        xAxisValuesForShortFlows1.append(avgResultSet1.shortFlowPercentileBasedResults.fctPercentileList[i].percentileValue)
        shortFlowYAxisTotal1 =  (avgResultSet1.shortFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue)/1024
        xAxisValuesForLargeFlows1.append(avgResultSet1.largeFlowPercentileBasedResults.fctPercentileList[i].percentileValue)
        LargeFlowYAxisTotal1 =  (avgResultSet1.largeFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue)/1024
        xAxisValuesForShortFlows2.append(avgResultSet2.shortFlowPercentileBasedResults.fctPercentileList[i].percentileValue)
        shortFlowYAxisTotal2 =  (avgResultSet2.shortFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue)/1024
        xAxisValuesForLargeFlows2.append(avgResultSet2.largeFlowPercentileBasedResults.fctPercentileList[i].percentileValue)
        LargeFlowYAxisTotal2 =  (avgResultSet2.largeFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue)/1024

        # shortFlowYAxisTotal1 = shortFlowYAxisTotal1 + (avgResultSet1.shortFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue)
        # LargeFlowYAxisTotal1 = LargeFlowYAxisTotal1 + (avgResultSet1.largeFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue)
        # shortFlowYAxisTotal2 = shortFlowYAxisTotal2 + (avgResultSet2.shortFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue)
        # LargeFlowYAxisTotal2 = LargeFlowYAxisTotal2 + (avgResultSet2.largeFlowPercentileBasedResults.successfulDataPercentileList[i].percentileValue)
        yAxisValuesForShortFlows1.append(shortFlowYAxisTotal1)
        yAxisValuesForLargeFlows1.append(LargeFlowYAxisTotal1)
        yAxisValuesForShortFlows2.append(shortFlowYAxisTotal2)
        yAxisValuesForLargeFlows2.append(LargeFlowYAxisTotal2)
    fig, axes = plt.subplots(1,constrained_layout = True)
    myLineWidth = 2
    axes.plot(xAxisValuesForShortFlows1, yAxisValuesForShortFlows1,'b--', label=str(algorithm1+"short-flow"),linewidth=myLineWidth)
    axes.plot(xAxisValuesForShortFlows2, yAxisValuesForShortFlows2,'r--', label=str(algorithm2+"short-flow"),linewidth=myLineWidth)
    for i_x, i_y in zip(xAxisValuesForShortFlows1, yAxisValuesForShortFlows1):
        #plt.text(i_x, i_y, '({:0.2f}, {:0.2f})'.format(i_x, i_y), fontsize=10)
        label = '({:0.2f}, {:0.2f})'.format(i_x, i_y)
        # plt.annotate(label, # this is the text
        #          (i_x,i_y), # this is the point to label
        #          textcoords="offset points", # how to position the text
        #          xytext=(35,0), # distance from text to points (x,y)
        #          ha='center',fontsize=9,fontweight='bold',rotation=0,wrap=True) # horizontal alignment can be left, right or center
    for i_x, i_y in zip(xAxisValuesForShortFlows2, yAxisValuesForShortFlows2):
        #plt.text(i_x, i_y, '({:0.2f}, {:0.2f})'.format(i_x, i_y), fontsize=10)
        label = '({:0.2f}, {:0.2f})'.format(i_x, i_y)
        # plt.annotate(label, # this is the text
        #              (i_x,i_y), # this is the point to label
        #              textcoords="offset points", # how to position the text
        #              xytext=(-30,0), # distance from text to points (x,y)
        #              ha='center',fontsize=9,fontweight='bold',rotation=0,wrap=True) # horizontal alignment can be left, right or center


    axes.set_xlabel("Time ",fontweight='bold',fontsize=20)
    axes.set_ylabel("Data (KB)",fontweight='bold',fontsize=20)
    axes.legend(loc="upper left")
    axes.legend(fontsize=10)
    plt.savefig(str(folderToSaveResult)+"/"+"ShortFlowNthPercentileTimebyToalThrougput.pdf")
    fig, axes = plt.subplots(1,constrained_layout = True)
    myLineWidth = 2
    axes.plot(xAxisValuesForLargeFlows1, yAxisValuesForLargeFlows1,'g.-', label=str(algorithm1+"large-flow"),linewidth=myLineWidth)
    axes.plot(xAxisValuesForLargeFlows2, yAxisValuesForLargeFlows2,'y.-', label=str(algorithm2+"large-flow"),linewidth=myLineWidth)
    for i_x, i_y in zip(xAxisValuesForLargeFlows1, yAxisValuesForLargeFlows1):
        #plt.text(i_x, i_y, '({:0.2f}, {:0.2f})'.format(i_x, i_y), fontsize=10)
        label = '({:0.2f}, {:0.2f})'.format(i_x, i_y)
        # plt.annotate(label, # this is the text
        #              (i_x,i_y), # this is the point to label
        #              textcoords="offset points", # how to position the text
        #              xytext=(35,0), # distance from text to points (x,y)
        #              ha='center',fontsize=9,fontweight='bold',rotation=0,wrap=True) # horizontal alignment can be left, right or center
    for i_x, i_y in zip(xAxisValuesForLargeFlows2, yAxisValuesForLargeFlows2):
        #plt.text(i_x, i_y, '({:0.2f}, {:0.2f})'.format(i_x, i_y), fontsize=10)
        label = '({:0.2f}, {:0.2f})'.format(i_x, i_y)
        # plt.annotate(label, # this is the text
        #              (i_x,i_y), # this is the point to label
        #              textcoords="offset points", # how to position the text
        #              xytext=(30,0), # distance from text to points (x,y)
        #              ha='center',fontsize=9,fontweight='bold',rotation=0,wrap=True) # horizontal alignment can be left, right or center
        #


        #     label = f"({x},{y})"
    #
    #     plt.annotate(label, # this is the text
    #                  (x,y), # this is the point to label
    #                  textcoords="offset points", # how to position the text
    #                  xytext=(0,1), # distance from text to points (x,y)
    #                  ha='center',fontsize=3,fontweight='bold',rotation=0,wrap=True) # horizontal alignment can be left, right or center
    axes.set_xlabel("Time ", fontweight='bold',fontsize=20)
    axes.set_ylabel("Data (KB)",fontweight='bold',fontsize=20)
    axes.legend(loc="upper left")
    axes.legend(fontsize=10)
    plt.savefig(str(folderToSaveResult)+"/"+"LargeFlowNthPercentileTimebyToalThrougput.pdf")






def generateGraphFor2Scenario(iPerfResultsFolder1,iPerfResultsFolder2,resultSet1, resultSet2, avgResultSet1, avgResultSet2,algorithm1, algorithm2, folderToSaveResult):
    #ResultSet1 and 2 contains the Standard deviations. We will use them in diagram for duscussing fairness
    visualizeSinglePerformanceMetrics(shortFlowResultSet1=avgResultSet1.shortFlowPercentileBasedResults.fctPercentileList,
                                      shortFlowResultSet2=avgResultSet2.shortFlowPercentileBasedResults.fctPercentileList,
                                      shortFlowLegend1=str(algorithm1+"-short-flow"), shortFlowLegend2=str(algorithm2+"-short-flow"),
                                      largeFlowResutSet1=avgResultSet1.largeFlowPercentileBasedResults.fctPercentileList,
                                      LargeFlowResultSet2=avgResultSet2.largeFlowPercentileBasedResults.fctPercentileList,
                                      largeFlowLegend1=str(algorithm1+"-large-flow"), largeFlowLegend2=str(algorithm2+"-large-flow"),
                                      xlabel="Percentile", ylabel="FCT",testCaseTitleName="FCT comparison",
                                      destinationfolder=folderToSaveResult,showShort= True, showLarge = True)
    visualizeSinglePerformanceMetrics(shortFlowResultSet1=avgResultSet1.shortFlowPercentileBasedResults.datalosspercentileList,
                                      shortFlowResultSet2=avgResultSet2.shortFlowPercentileBasedResults.datalosspercentileList,
                                      shortFlowLegend1=str(algorithm1+"-short-flow"), shortFlowLegend2=str(algorithm2+"-short-flow"),
                                      largeFlowResutSet1=avgResultSet1.largeFlowPercentileBasedResults.datalosspercentileList,
                                      LargeFlowResultSet2=avgResultSet2.largeFlowPercentileBasedResults.datalosspercentileList,
                                      largeFlowLegend1=str(algorithm1+"-large-flow"), largeFlowLegend2=str(algorithm2+"-large-flow"),
                                      xlabel="Percentile", ylabel="Total Data Lost (KB)",testCaseTitleName="Data Loss comparison",
                                      destinationfolder=folderToSaveResult,showShort= True, showLarge = True)
    visualizeSinglePerformanceMetrics(shortFlowResultSet1=avgResultSet1.shortFlowPercentileBasedResults.successfulDataPercentileList,
                                      shortFlowResultSet2=avgResultSet2.shortFlowPercentileBasedResults.successfulDataPercentileList,
                                      shortFlowLegend1=str(algorithm1+"-short-flow"), shortFlowLegend2=str(algorithm2+"-short-flow"),
                                      largeFlowResutSet1=avgResultSet1.largeFlowPercentileBasedResults.successfulDataPercentileList,
                                      LargeFlowResultSet2=avgResultSet2.largeFlowPercentileBasedResults.successfulDataPercentileList,
                                      largeFlowLegend1=str(algorithm1+"-large-flow"), largeFlowLegend2=str(algorithm2+"-large-flow"),
                                      xlabel="Percentile", ylabel="Total Volume of Data Sent Sucessfully (KB)",testCaseTitleName="Total Data Sucessfully Sent Comparison",
                                      destinationfolder=folderToSaveResult,showShort=True, showLarge=False)
    visualizeSinglePerformanceMetrics(shortFlowResultSet1=avgResultSet1.shortFlowPercentileBasedResults.successfulDataPercentileList,
                                      shortFlowResultSet2=avgResultSet2.shortFlowPercentileBasedResults.successfulDataPercentileList,
                                      shortFlowLegend1=str(algorithm1+"-short-flow"), shortFlowLegend2=str(algorithm2+"-short-flow"),
                                      largeFlowResutSet1=avgResultSet1.largeFlowPercentileBasedResults.successfulDataPercentileList,
                                      LargeFlowResultSet2=avgResultSet2.largeFlowPercentileBasedResults.successfulDataPercentileList,
                                      largeFlowLegend1=str(algorithm1+"-large-flow"), largeFlowLegend2=str(algorithm2+"-large-flow"),
                                      xlabel="Percentile", ylabel="Total Volume of Data Sent Sucessfully (KB)",testCaseTitleName="Total Data Sucessfully Sent Comparison",
                                      destinationfolder=folderToSaveResult,showShort=False, showLarge=True)
    visualizeSinglePerformanceMetrics(shortFlowResultSet1=avgResultSet1.shortFlowPercentileBasedResults.retransmitPercentileList,
                                      shortFlowResultSet2=avgResultSet2.shortFlowPercentileBasedResults.retransmitPercentileList,
                                      shortFlowLegend1=str(algorithm1+"-short-flow"), shortFlowLegend2=str(algorithm2+"-short-flow"),
                                      largeFlowResutSet1=avgResultSet1.largeFlowPercentileBasedResults.retransmitPercentileList,
                                      LargeFlowResultSet2=avgResultSet2.largeFlowPercentileBasedResults.retransmitPercentileList,
                                      largeFlowLegend1=str(algorithm1+"-large-flow"), largeFlowLegend2=str(algorithm2+"-large-flow"),
                                      xlabel="Percentile", ylabel="No of Retransmission",testCaseTitleName="Retransmission Comparison",
                                      destinationfolder=folderToSaveResult,showShort= True, showLarge = True)
    visualizeSinglePerformanceMetrics(shortFlowResultSet1=avgResultSet1.shortFlowPercentileBasedResults.tcpThroughputInBPSList,
                                      shortFlowResultSet2=avgResultSet2.shortFlowPercentileBasedResults.tcpThroughputInBPSList,
                                      shortFlowLegend1=str(algorithm1+"-short-flow"), shortFlowLegend2=str(algorithm2+"-short-flow"),
                                      largeFlowResutSet1=avgResultSet1.largeFlowPercentileBasedResults.tcpThroughputInBPSList,
                                      LargeFlowResultSet2=avgResultSet2.largeFlowPercentileBasedResults.tcpThroughputInBPSList,
                                      largeFlowLegend1=str(algorithm1+"-large-flow"), largeFlowLegend2=str(algorithm2+"-large-flow"),
                                      xlabel="Percentile", ylabel="TCP Throughput ",testCaseTitleName="TCP Throughput Comparison",
                                      destinationfolder=folderToSaveResult,showShort= True, showLarge = True)


def getTimeByThroughPutInKB(iperfResultsSortedByFinishTime):
    totalthroughputInKB = 0.0
    timeByThroughputList = []
    temp = iperfResultsSortedByFinishTime[0]
    startTimne  = temp.getEndTimeInSec()
    for r in iperfResultsSortedByFinishTime:
        #print(iperfResultsSortedByFinishTime)
        totalthroughputInKB = totalthroughputInKB + float(r.end.sum_received.bytes/1024)
        timeByThroughputList.append((r.getEndTimeInSec()-startTimne,totalthroughputInKB))
    return timeByThroughputList


def processResults(iPerfResultsFolder1, iPerfResultsFolder2, algorithm1, algorithm2, folderToSaveResult, topologyConfigFile=CC.TOPOLOGY_CONFIG_FILE):
    #testFunction()
    # Generate axis. then pass file and axes to the function
    config = rp.ConfigLoader(topologyConfigFile)
    totalNumOfSwitches = len(config.nameToSwitchMap)
    squareRootOftotalNumOfSwitches = math.sqrt(totalNumOfSwitches)
    nRow = math.ceil(squareRootOftotalNumOfSwitches)
    nColumn = math.ceil(totalNumOfSwitches/nRow)



    # For each test config there should be a folder Name
    # all logs relevant to that test case will be written to that folder.
    # So assume for same configuration we have 2 algo. there will be 2 folder with ouput.
    # INside each folder there will be a special file where the time when the test will be started is written down.
    # We will use that time while processing and visualiing the server logs

    # to compare, we have to make sure inside 2 folder we have same set of file. each file will be name src-dst.json.
    #then we will compare 2 algo perfprmance
    # Basocally we do not need testconfig here. From the iperf result we wil find results. and from the name we will get src-dest and total data sent
    # also from the iPEerf result we can fund src and dest.



    #    print("TCP incast scenario tester without explicit rate setting \n \n \n \n")
    try:
        shutil.rmtree(folderToSaveResult)
    except OSError as err:
        print("Failed to clear the destionation folder: {0}".format(err))

    try:
        if not os.path.exists(folderToSaveResult):
            os.mkdir(folderToSaveResult)
    except OSError as err:
        print("Failed to create directory for saving result: {0}".format(err))
    except Exception as ve :
        print("Exception occured :{}".format(ve))

    resultSet1 = collectResultOfAllIteratioOfTestCaseGroupedByFlowType(iPerfResultsFolder1)
    resultSet2 = collectResultOfAllIteratioOfTestCaseGroupedByFlowType(iPerfResultsFolder2)
    avgResultSet1 = getAverageOfAllIterationsGroupedByFlowType(resultSet1)
    avgResultSet2 = getAverageOfAllIterationsGroupedByFlowType(resultSet2)


    #This part Generates graph
    generateGraphFor2Scenario(iPerfResultsFolder1,iPerfResultsFolder2,resultSet1,resultSet2, avgResultSet1, avgResultSet2,algorithm1, algorithm2, folderToSaveResult)
    generateTimeByThroughputGraphForOneIteration(iPerfResultsFolder1,iPerfResultsFolder2,resultSet1, resultSet2, avgResultSet1, avgResultSet2,algorithm1, algorithm2, folderToSaveResult)
    plotNthPercenTileFCTVsTotalThroughout(iPerfResultsFolder1,iPerfResultsFolder2,resultSet1, resultSet2, avgResultSet1, avgResultSet2,algorithm1, algorithm2, folderToSaveResult)
    #This part prints result in file
    print("\n\n====================================================================================")
    print("FCT of short flows ")
    print("For :"+algorithm1)
    json.dump(avgResultSet1.shortFlowPercentileBasedResults.fctPercentileList, sys.stdout)
    print("\nStandard Deviation: "+str(resultSet1[0].shortFlowPercentileBasedResults.fctSTD))
    print("For :"+algorithm2)
    print(avgResultSet2.shortFlowPercentileBasedResults.fctPercentileList)
    print("\nStandard Deviation: "+str(resultSet2[0].shortFlowPercentileBasedResults.fctSTD))
    print("FCT of large flows ")
    print("For :"+algorithm1)
    print(avgResultSet1.largeFlowPercentileBasedResults.fctPercentileList)
    print("\nStandard Deviation: "+str(resultSet1[0].largeFlowPercentileBasedResults.fctSTD))
    print("For :"+algorithm2)
    print(avgResultSet2.largeFlowPercentileBasedResults.fctPercentileList)
    print("\nStandard Deviation: "+str(resultSet2[0].largeFlowPercentileBasedResults.fctSTD))

    print("\n\n====================================================================================")
    print("Total Data Loss of short flows ")
    print("For :"+algorithm1)
    print(avgResultSet1.shortFlowPercentileBasedResults.datalosspercentileList)
    print("\nStandard Deviation: "+str(resultSet1[0].shortFlowPercentileBasedResults.dataLossSTD))
    print("For :"+algorithm2)
    print(avgResultSet2.shortFlowPercentileBasedResults.datalosspercentileList)
    print("\nStandard Deviation: "+str(resultSet2[0].shortFlowPercentileBasedResults.dataLossSTD))
    print("Total Data Loss  of large flows ")
    print("For :"+algorithm1)
    print(avgResultSet1.largeFlowPercentileBasedResults.datalosspercentileList)
    print("\nStandard Deviation: "+str(resultSet1[0].largeFlowPercentileBasedResults.dataLossSTD))
    print("For :"+algorithm2)
    print(avgResultSet2.largeFlowPercentileBasedResults.datalosspercentileList)
    print("\nStandard Deviation: "+str(resultSet2[0].largeFlowPercentileBasedResults.dataLossSTD))

    print("\n\n====================================================================================")
    print("Total Sucessfully Sent volume of data of short flows ")
    print("For :"+algorithm1)
    print(avgResultSet1.shortFlowPercentileBasedResults.successfulDataPercentileList)
    print("\nStandard Deviation: "+str(resultSet1[0].shortFlowPercentileBasedResults.successfulDataSTD))
    print("For :"+algorithm2)
    print(avgResultSet2.shortFlowPercentileBasedResults.successfulDataPercentileList)
    print("\nStandard Deviation: "+str(resultSet2[0].shortFlowPercentileBasedResults.successfulDataSTD))
    print("Total Sucessfully Sent volume of data  of large flows ")
    print("For :"+algorithm1)
    print(avgResultSet1.largeFlowPercentileBasedResults.successfulDataPercentileList)
    print("\nStandard Deviation: "+str(resultSet1[0].largeFlowPercentileBasedResults.successfulDataSTD))
    print("For :"+algorithm2)
    print(avgResultSet2.largeFlowPercentileBasedResults.successfulDataPercentileList)
    print("\nStandard Deviation: "+str(resultSet2[0].largeFlowPercentileBasedResults.successfulDataSTD))


    print("\n\n====================================================================================")
    print("Total Number of retranmits of short flows ")
    print("For :"+algorithm1)
    print(avgResultSet1.shortFlowPercentileBasedResults.retransmitPercentileList)
    print("\nStandard Deviation: "+str(resultSet1[0].shortFlowPercentileBasedResults.retransmitSTD))
    print("For :"+algorithm2)
    print(avgResultSet2.shortFlowPercentileBasedResults.retransmitPercentileList)
    print("\nStandard Deviation: "+str(resultSet2[0].shortFlowPercentileBasedResults.retransmitSTD))
    print("Total Number of retranmits  of large flows ")
    print("For :"+algorithm1)
    print(avgResultSet1.largeFlowPercentileBasedResults.retransmitPercentileList)
    print("\nStandard Deviation: "+str(resultSet1[0].largeFlowPercentileBasedResults.retransmitSTD))
    print("For :"+algorithm2)
    print(avgResultSet2.largeFlowPercentileBasedResults.retransmitPercentileList)
    print("\nStandard Deviation: "+str(resultSet2[0].largeFlowPercentileBasedResults.retransmitSTD))


    print("\n\n====================================================================================")
    print("TCP Throughput of short flows ")
    print("For :"+algorithm1)
    print(avgResultSet1.shortFlowPercentileBasedResults.tcpThroughputInBPSList)
    print("\nStandard Deviation: "+str(resultSet1[0].shortFlowPercentileBasedResults.tcpThroughoutSTD))
    print("For :"+algorithm2)
    print(avgResultSet2.shortFlowPercentileBasedResults.tcpThroughputInBPSList)
    print("\nStandard Deviation: "+str(resultSet2[0].shortFlowPercentileBasedResults.tcpThroughoutSTD))
    print("TCP Throughput of large flows ")
    print("For :"+algorithm1)
    print(avgResultSet1.largeFlowPercentileBasedResults.tcpThroughputInBPSList)
    print("\nStandard Deviation: "+str(resultSet1[0].largeFlowPercentileBasedResults.tcpThroughoutSTD))
    print("For :"+algorithm2)
    print(avgResultSet2.largeFlowPercentileBasedResults.tcpThroughputInBPSList)
    print("\nStandard Deviation: "+str(resultSet2[0].largeFlowPercentileBasedResults.tcpThroughoutSTD))

    # start1 , end1   = getMinMaxtimeStampForLInkVisulationforAFolder(iPerfResultsFolder1)
    # upwardLinkUtilizationAnalyzer(config = config)
    # start2 , end2   = getMinMaxtimeStampForLInkVisulationforAFolder(iPerfResultsFolder2)
    # print(start2)
    # print(end2)
    # val = upwardLinkUtilizationAnalyzer(config = config)
    # print(val)

    #percentileValuesToComapre = [50,75,90,99]

    # print("\n\n====================================================================================")
    # print("FCT of short flows ")
    # print("For :"+algorithm1)
    # for r in percentileValuesToComapre:
    #     print(avgResultSet1.shortFlowPercentileBasedResults.fctPercentileList[r])
    # print("For :"+algorithm2)
    # for r in percentileValuesToComapre:
    #     print(avgResultSet2.shortFlowPercentileBasedResults.fctPercentileList[r])
    #
    # print("FCT of large flows ")
    # for r in percentileValuesToComapre:
    #     print(avgResultSet1.largeFlowPercentileBasedResults.fctPercentileList[r])
    # print("For :"+algorithm2)
    # for r in percentileValuesToComapre:
    #     print(avgResultSet2.largeFlowPercentileBasedResults.fctPercentileList[r])
    #
    # print("\n\n====================================================================================")
    # print("Total Data Loss of short flows ")
    # print("For :"+algorithm1)
    # for r in percentileValuesToComapre:
    #     print(avgResultSet1.shortFlowPercentileBasedResults.datalosspercentileList[r])
    # print("For :"+algorithm2)
    # for r in percentileValuesToComapre:
    #     print(avgResultSet2.shortFlowPercentileBasedResults.datalosspercentileList[r])
    # print("Total Data Loss  of large flows ")
    # print("For :"+algorithm1)
    # for r in percentileValuesToComapre:
    #     print(avgResultSet1.largeFlowPercentileBasedResults.datalosspercentileList[r])
    # print("For :"+algorithm2)
    # for r in percentileValuesToComapre:
    #     print(avgResultSet2.largeFlowPercentileBasedResults.datalosspercentileList[r])
    #
    # print("\n\n====================================================================================")
    # print("Total Sucessfully Sent volume of data of short flows ")
    # print("For :"+algorithm1)
    # for r in percentileValuesToComapre:
    #     print(avgResultSet1.shortFlowPercentileBasedResults.successfulDataPercentileList[r])
    # print("For :"+algorithm2)
    # for r in percentileValuesToComapre:
    #     print(avgResultSet2.shortFlowPercentileBasedResults.successfulDataPercentileList[r])
    # print("Total Sucessfully Sent volume of data  of large flows ")
    # print("For :"+algorithm1)
    # for r in percentileValuesToComapre:
    #     print(avgResultSet1.largeFlowPercentileBasedResults.successfulDataPercentileList[r])
    # print("For :"+algorithm2)
    # for r in percentileValuesToComapre:
    #     print(avgResultSet2.largeFlowPercentileBasedResults.successfulDataPercentileList[r])
    #
    #
    # print("\n\n====================================================================================")
    # print("Total Number of retranmits of short flows ")
    # print("For :"+algorithm1)
    # for r in percentileValuesToComapre:
    #     print(avgResultSet1.shortFlowPercentileBasedResults.retransmitPercentileList[r])
    # print("For :"+algorithm2)
    # for r in percentileValuesToComapre:
    #     print(avgResultSet2.shortFlowPercentileBasedResults.retransmitPercentileList[r])
    # print("Total Number of retranmits  of large flows ")
    # print("For :"+algorithm1)
    # for r in percentileValuesToComapre:
    #     print(avgResultSet1.largeFlowPercentileBasedResults.retransmitPercentileList[r])
    # print("For :"+algorithm2)
    # for r in percentileValuesToComapre:
    #     print(avgResultSet2.largeFlowPercentileBasedResults.retransmitPercentileList[r])
    #
    #
    # print("\n\n====================================================================================")
    # print("TCP Throughput of short flows ")
    # print("For :"+algorithm1)
    # for r in percentileValuesToComapre:
    #     print(avgResultSet1.shortFlowPercentileBasedResults.tcpThroughputInBPSList[r].getMyselfInKBPS())
    # print("For :"+algorithm2)
    # for r in percentileValuesToComapre:
    #     print(avgResultSet2.shortFlowPercentileBasedResults.tcpThroughputInBPSList[r].getMyselfInKBPS())
    # print("TCP Throughput of large flows ")
    # print("For :"+algorithm1)
    # for r in percentileValuesToComapre:
    #     print(avgResultSet1.largeFlowPercentileBasedResults.tcpThroughputInBPSList[r].getMyselfInKBPS())
    # print("For :"+algorithm2)
    # for r in percentileValuesToComapre:
    #     print(avgResultSet2.largeFlowPercentileBasedResults.tcpThroughputInBPSList[r].getMyselfInKBPS())
    #
    # start1 , end1   = getMinMaxtimeStampForLInkVisulationforAFolder(iPerfResultsFolder1)
    # upwardLinkUtilizationAnalyzer(config = config)
    # start2 , end2   = getMinMaxtimeStampForLInkVisulationforAFolder(iPerfResultsFolder2)
    # print(start2)
    # print(end2)
    # val = upwardLinkUtilizationAnalyzer(config = config)
    # print(val)
    # print("Finally printingn the both result set summary")
    # newResult = PercentileSummaryResultForOneIterationOfTestCase(resultSet1[0].shortFlowPercentileBasedResults, resultSet1[0].largeFlowPercentileBasedResults)
    # print(return_class_variables(resultSet1[0].largeFlowPercentileBasedResults))
    # print(return_class_variables(resultSet1[0].shortFlowPercentileBasedResults))

def return_class_variables(A):
    return(A.__dict__)

def compare2Resultfolder(folder1, folder2):
    iperfResultForFolder1 =  parseIperfResultsFromFolder(folder1)
    iperfResultForFolder2 =  parseIperfResultsFromFolder(folder2)
    iperfResultsSortedByFlowVolume1 = sorted(iperfResultForFolder1[2].iperfResults, key=lambda x: getattr(x[0].end.sum_received, 'bytes')) # sort by number of bytes sent
    iperfResultsSortedByFlowVolume2 = sorted(iperfResultForFolder2[2].iperfResults, key=lambda x: getattr(x[0].end.sum_received, 'bytes')) # sort by number of bytes sent

    x1 = [p[0].end.sum_received.bytes/p[0].end.sum_sent.bytes for p in iperfResultsSortedByFlowVolume1]
    # y1 = [p[0].end.sum_received.seconds for p in iperfResultsSortedByFlowVolume1]
    # x2 = [p[0].end.sum_received.bytes/(8*1024) for p in iperfResultsSortedByFlowVolume2]
    # y2 = [p[0].end.sum_received.seconds for p in iperfResultsSortedByFlowVolume2]
    # x2 = [p.percentile for p in shortFlowResultSet2]
    # y2 = [p.percentileValue for p in shortFlowResultSet2]
    # x3 = [p.percentile for p in largeFlowResutSet1]
    # y3 = [p.percentileValue for p in largeFlowResutSet1]
    # x4 = [p.percentile for p in LargeFlowResultSet2]
    # y4 = [p.percentileValue for p in LargeFlowResultSet2]
    fig, axes = plt.subplots(1)
    # myLineWidth = .1
    # axes.plot(x1, y1,'b.')
    # axes.plot(x1, y1,'r.')

    axes.hist(x1, .01)
    #axes.xaxis.zoom(3)
    #axes.plot(x2, y2,'r.', label="leg1",linewidth=myLineWidth)
    plt.savefig("/home/deba/Desktop/test.pdf")
    #axes.plot(x2, y2,'ro-', label="leg2",linewidth=myLineWidth)
    # axes.plot(x3, y3, 'g--', label=largeFlowLegend1,linewidth=myLineWidth)
    # axes.plot(x4, y4, 'y--', label=largeFlowLegend2,linewidth=myLineWidth)

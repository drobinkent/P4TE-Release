import logging
import threading
import time
import os
import subprocess

import ConfigConst
import InternalConfig
import P4Runtime.shell as sh
from P4Runtime.context import Context
from P4Runtime.p4runtime import P4RuntimeClient, P4RuntimeException, parse_p4runtime_error
import P4Runtime.leafSwitchUtils as leafUtils
import P4Runtime.spineSwitchUtils as spineUtils
import P4Runtime.superSpineSwitchUtils as superSpineUtils
import P4Runtime.SwitchUtils as swUtils
import ConfigConst as ConfConst
import P4Runtime.JsonParser as jp
import P4Runtime.PortStatistics as ps
import P4Runtime.packetUtils as pktUtil
import P4Runtime.StatisticsJsonWrapper as statJsonWrapper
import matplotlib.pyplot as plot
import numpy as np
import math
import json

import logging.handlers

logger = logging.getLogger('StatisticsPuller')
logger.handlers = []
hdlr = logging.handlers.RotatingFileHandler(ConfConst.STATISTICS_LOG_FILE_PATH, maxBytes = ConfConst.MAX_LOG_FILE_SIZE , backupCount= ConfConst.MAX_LOG_FILE_BACKUP_COUNT)
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)


class StatisticsPuller:
    '''
    This class contains all the code for pulling various statistics from switch. Mainly using register and counter
    '''


    def __init__(self, nameToSwitchMap, devName):
        self.isRunning = True
        self.nameToSwitchMap = nameToSwitchMap
        self.devName = devName
        self.p4dev  = self.nameToSwitchMap.get(devName)
        f =  open(ConfConst.CONTROLLER_STATISTICS_RESULT_FILE_PATH+self.p4dev .devName+".json", mode='a', buffering=1024)
        self.nameToSwitchMap.get(devName).controllerStatsFile = f
        x = threading.Thread(target=self.thread_function, args=())
        self.statisticPullerthread = x
        logger.info("Stiatisticspuller thread for device: "+str(self.p4dev.devName)+" is being started")
        x.start()
        logger.info("Stiatisticspuller thread for device: "+str(self.p4dev .devName)+" has started")





    def thread_function(self):
        # logger.info("Sta: starting", "StatisticsPuller",str(self.p4dev.devName))
        # totalNumOfSwitches = len(self.nameToSwitchMap)
        # squareRootOftotalNumOfSwitches = math.sqrt(totalNumOfSwitches)
        # nRow = math.ceil(squareRootOftotalNumOfSwitches)
        # nColumn = math.ceil(totalNumOfSwitches/nRow)
        # fig, axes = plot.subplots(nrows=nRow, ncols=nColumn, sharex=True, sharey=True)
        # for dev in self.nameToSwitchMap:
        #     f =  open(ConfConst.CONTROLLER_STATISTICS_RESULT_FILE_PATH+dev+".json", mode='a', buffering=1024)
        #     self.nameToSwitchMap.get(dev).controllerStatsFile = f
        switchObject = self.p4dev
        self.oldLinkUtilStats = self.pullStatsFromSwitch(dev=switchObject)
        while(self.isRunning):
            time.sleep(ConfConst.STATISTICS_PULLING_INTERVAL)
            index=0
            switchObject = self.p4dev
            linkUtilStats = self.pullStatsFromSwitch(dev=switchObject)
            self.useLinkUtilForPathReconfigure(linkUtilStats, self.oldLinkUtilStats)
            self.oldLinkUtilStats = linkUtilStats
            # switchObject.controllerStatsFile.write(json.dumps(statJson, cls=statJsonWrapper.PortStatisticsJSONWrapper))
            # switchObject.controllerStatsFile.flush()
        logger.info("Thread %s: finishing", "StatisticsPuller", str(self.p4dev.devName))

    def useLinkUtilForPathReconfigure(self, linkUtilStats,oldLinkUtilStats):
        if (self.p4dev.dpAlgorithm == ConfConst.DataplnaeAlgorithm.DP_ALGO_BASIC_ECMP) : # do nothing
            logger.info("ECMP ALGORITHM: For switch "+ self.p4dev.devName+ "new Utilization data is  "+str(linkUtilStats))
            logger.info("ECMP ALGORITHM: For switch "+ self.p4dev.devName+ "old Utilization data is  "+str(oldLinkUtilStats))
            return
        if ((self.p4dev.dpAlgorithm == ConfConst.DataplnaeAlgorithm.DP_ALGO_BASIC_HULA) and (self.p4dev.fabric_device_config.switch_type == jp.SwitchType.LEAF)):
            logger.info("HULA ALGORITHM: For switch "+ self.p4dev.devName+ "new Utilization data is  "+str(linkUtilStats))
            logger.info("HULA ALGORITHM: For switch "+ self.p4dev.devName+ "old Utilization data is  "+str(oldLinkUtilStats))
            self.p4dev.hulaUtilBasedReconfigureForLeafSwitches(linkUtilStats,oldLinkUtilStats)
            pass # dohuyla logic
        if ((self.p4dev.dpAlgorithm == ConfConst.DataplnaeAlgorithm.DP_ALGO_BASIC_CLB)  and (self.p4dev.fabric_device_config.switch_type == jp.SwitchType.LEAF)):
            # if(ConfConst.CLB_TESTER_DEVICE_NAME in self.p4dev.devName):
            logger.info("CLB ALGORITHM: For switch "+ self.p4dev.devName+ "new Utilization data is  "+str(linkUtilStats))
            logger.info("CLB ALGORITHM: For switch "+ self.p4dev.devName+ "old Utilization data is  "+str(oldLinkUtilStats))
            self.clbUtilBasedReconfigureForLeafSwitches(linkUtilStats, self.oldLinkUtilStats)
            pass # do CLB logic
        pass

    def clbUtilBasedReconfigureForLeafSwitches(self, linkUtilStats,oldLinkUtilStats):
        # for all leafswitch get their 16-31 th bit and convert it to int
        # multply that with the upword port nubers
        # get the resultindex th position in the pulled results.
        # use that for that tor

        # logger.info(" For switch "+ self.p4dev.devName+ "new Utilization data is  "+str(linkUtilStats))
        # logger.info(" For switch "+ self.p4dev.devName+ "old Utilization data is  "+str(oldLinkUtilStats))
        for lswitch in self.p4dev.allLeafSwitchesInTheDCN:
            e = lswitch.fabric_device_config.switch_host_subnet_prefix.index("/")
            leafSubnetAsIP = lswitch.fabric_device_config.switch_host_subnet_prefix[0:e]
            leafSubnetPrefixLength = lswitch.fabric_device_config.switch_host_subnet_prefix[e+1:len(lswitch.fabric_device_config.switch_host_subnet_prefix)]
            r1 = lswitch.fabric_device_config.switch_host_subnet_prefix.rindex(":")
            r2 = lswitch.fabric_device_config.switch_host_subnet_prefix[0:r1].rindex(":")
            torID = int(lswitch.fabric_device_config.switch_host_subnet_prefix[r2+1:r1])

            upwardPortList = list(self.p4dev.portToSpineSwitchMap.keys())
            pathAndUtilist = []
            totalUtil = 0
            # if(torID !=3):
            #     continue
            # print("ToirId is "+str(torID))

            for uPort in upwardPortList:
                index = int(uPort) + (torID*ConfConst.MAX_PORTS_IN_SWITCH) -1
                # print("Index to be accessed "+str(index))
                # print("New util is "+str(linkUtilStats[index]))
                # print("Old util is "+str(oldLinkUtilStats[index]))
                utilInLastInterval = linkUtilStats[index] -  oldLinkUtilStats[index]
                if(utilInLastInterval >0):
                    pathAndUtilist.append((uPort,utilInLastInterval))
                    totalUtil = totalUtil + utilInLastInterval
                    # print("for port "+str(uPort)+" Util is "+str(utilInLastInterval))
                else:
                    pathAndUtilist.append((uPort,1))
                    totalUtil = totalUtil + 1
                    # print("for port "+str(uPort)+" Util is "+str(1))
            # print("Total Util is "+str(totalUtil))
            perUnitWeight = totalUtil/ConfConst.BITMASK_LENGTH
            totalWeight = ConfConst.BITMASK_LENGTH
            weightDistro = []
            portDistribInverse = []
            total=0
            for pUtil in pathAndUtilist:
                port = pUtil[0]
                util = pUtil[1]
                portWeight =  (util/totalUtil)
                total = total+ portWeight
                portDistribInverse.append((port,portWeight))
                # print("for port "+str(port)+" inverse util is "+str(portWeight))
            # print("Total Weight is "+str(total))
            wSum = 0
            oneUnit = total/ConfigConst.BITMASK_LENGTH
            accumDistrib2 = []
            newTotal = 0
            for pUtil in portDistribInverse:
                port = pUtil[0]
                util = pUtil[1]
                wSum = wSum + util
                times = int(wSum/oneUnit)
                if ((wSum - (times*oneUnit)) > 0 ):
                    portWeight = times + 1
                else:
                    portWeight = times
                accumDistrib2.append((port,portWeight))
                # print("Final weight for port "+str(port)+"  uis "+str(portWeight))


            # accumDistrib2 = []
            # newTotal=0
            # for pUtil in portDistribInverse:
            #     port = pUtil[0]
            #     util = pUtil[1]
            #     newTotal = newTotal+ int((util/total) * ConfConst.BITMASK_LENGTH)
            #     accumDistrib2.append((port,newTotal))
            #     print("Final weight for port "+str(port)+"  uis "+str(newTotal))
            self.p4dev.ctrlPlaneLogic.processStatisticsPulledFromSwitch(torID,accumDistrib2)
            # if(ConfConst.CLB_TESTER_DEVICE_NAME in self.p4dev.devName):
            #     print("Newly installed distrib is "+str(accumDistrib2))


        pass

# Conditions needed to be checked before assigning weight
# a) any weight can not be 0-- at least 1
# b) If at someplace the weight crosses bitmask legnth it should be asigned to max weight and others should be discarded.

    def indexToRowColumn(self, index, totalColumns):
        row = int(math.floor(index/float(totalColumns)))
        column = index % totalColumns
        return row, column  # TODO we may need to subtract 1 t match the index number(as index starts from zero)

    def pullStatsFromSwitch(self, dev):
        # this method will pull various counter and register values from the switches and plot data accordingly.
        # Also save the collected statistics for each device in corresponding data structure.

        #logger.info("Pulling record from device:"+ str(dev.devName))
        # recordPullingtime = time.time()
        # egressPortStats, ingressPortStats , ctrlPkttoCPStats,  p2pFeedbackStats, lbMissedPackets = swUtils.readAllCounters(dev)
        # # logger.info(egressPortStats)
        # # logger.info(ingressPortStats)
        # # logger.info(ctrlPkttoCPStats)
        # # logger.info(p2pFeedbackStats)
        # # Store records
        # #In port to leaf.spine, super spine map, we can find which port maps to what kind of connected devices. From there we can find relevan ports. And we will
        # #create a obejct for statistics. And we will keep all the info there.
        #
        # portStatistics = ps.PortStatistics()
        #
        # #s = Device()
        # # Keeep data separate data structure for statistics on upward and downward ports
        # # pull records. TODO Instead of pulling record for all the ports, we can pull record for host, leaf or spine switches and collect infos here. And also0 save them
        # # We are already doing the filtering.  So we can actually skip the earlier part  of recording all stats and only call the readcounter function in the
        # #below if-else part
        # #print("If we want to collect the link utilization rate, simple pop the last portStatistics form the que , get diff from current value. let's assume the ")
        # # print("is delta. now if the stats collection interval is t sec. and dev.PortToQueueRateMap.get(port) (this gives the processing rate of the port")
        # # print("(delta)/ (t* p[rocessing rate) is the real link utilizatin rate ")
        # # try:
        # #     lastStats = dev.portStatisticsCollection[-1]
        # #     if(lastStats ==None):
        # #         lastStats = ps.PortStatistics()
        # # except Exception as e:
        # #     lastStats = ps.PortStatistics()
        #
        # # if(dev.devName == "device:p0l0"):
        # #     print("Gotcha")
        # # tempPortStats = ps.PortStatistics()
        # if (dev.fabric_device_config.switch_type == jp.SwitchType.LEAF ):
        #     for sPort in dev.portToSpineSwitchMap:
        #         egressPortCounterValueForSpine =egressPortStats.get(sPort)
        #         portStatistics.setUpwardPortEgressPacketCounter(sPort,egressPortCounterValueForSpine)
        # portStatistics.setLBMissedPackets(lbMissedPackets)
        #
        # statJson = statJsonWrapper.PortStatisticsJSONWrapper()
        # statJson.setData(recordPullingtime,portStatistics, dev.devName)
        # # logger.info("Stat is "+ json.dumps(statJson,cls=statJsonWrapper.PortStatisticsJSONWrapper))
        # # logging.info("Inserted Port Statistics to device history record")
        # return statJson
        # logger.info("Reading LinkUtil for switch "+ (str(dev.devName)))
        val = swUtils.collectDestinationBasedLinkeUtilization(dev, "destination_util_counter")
        # logger.info(val)
        return val





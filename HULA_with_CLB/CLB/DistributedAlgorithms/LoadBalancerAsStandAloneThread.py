import json
import logging
import threading
import time
import P4Runtime.shell as sh
from p4.v1 import p4runtime_pb2

import ConfigConst as ConfConst
logger = logging.getLogger('LoadBalancer')
logger.handlers = []
hdlr = logging.handlers.RotatingFileHandler(ConfConst.CONTROLLER_LOG_FILE_PATH, maxBytes = ConfConst.MAX_LOG_FILE_SIZE , backupCount= ConfConst.MAX_LOG_FILE_BACKUP_COUNT)
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)
def modifyBit( n,  p,  b):
    '''
    # Python3 program to modify a bit at position
# p in n to b.

# Returns modified n.
    :param n:
    :param p:
    :param b:
    :return:
    '''
    mask = 1 << p
    return (n & ~mask) | ((b << p) & mask)

class LoadBalanacer:

    def __init__(self,  allLinksAsList, bitMaskLength, nameToSwitchMap ):
        self.linkToCurrentLevel={}
        self.bitMaskLength = bitMaskLength
        self.bitMaskArray = []
        self.nameToSwitchMap = nameToSwitchMap
        for l in allLinksAsList:
            self.linkToCurrentLevel[l] = 0
        for i in range(0,self.bitMaskLength):
            #Initializing all the bit masks with 0
            self.bitMaskArray.append(0)
        self.isRunning =True
        x = threading.Thread(target=self.load_balancer_config_thread_function, args=())
        x.start()
        logger.info("load_balancer_config_thread_function thread started")

    def initMAT(self, switchObject, bitMaskLength):
        allOneMAsk = BinaryMask(bitMaskLength)
        allOneMAsk.setAllBitOne()
        allOneMAskBinaryString = allOneMAsk.getBinaryString()
        for j in range(0, bitMaskLength):
            mask = BinaryMask(bitMaskLength)
            mask.setNthBitWithB(n=j,b=1)
            maskAsString = mask.getBinaryString()
            switchObject.addTernaryEntriesForCLBTMAt( packetBitmaskValueWithMaskAsString = allOneMAskBinaryString+"&&&"+maskAsString,
                                                     actionParamValue=  j , priority= bitMaskLength-j+1) #1 added in the prioity bcz  0 priority doesn;t work
            # switchObject.addTernaryEntriesForCLBTMAt( packetBitmaskArrayIndex = i, packetBitmaskValueWithMaskAsString = allOneMAskBinaryString+"&&&"+maskAsString,
            #                                           actionParamValue=i * bitMaskLength + j ,
            #                                           priority= (bitMaskArrayMaxIndex * bitMaskLength)-(i * bitMaskLength + j)) #1 added in the prioity bcz  0 priority doesn;t work

    def initMATOld(self, switchObject, bitMaskLength, bitMaskArrayMaxIndex):
        allZeroMAsk = BinaryMask(bitMaskLength)
        allZeroMAskBinaryStrings = allZeroMAsk.getBinaryString()
        for i in range (0, bitMaskArrayMaxIndex):
            for j in range(0, bitMaskLength):
                mask = BinaryMask(bitMaskLength)
                mask.setAllBitOne()
                mask.setNthBitWithB(n=j,b=0)
                maskAsString = mask.getBinaryString()
                switchObject.addTernaryEntriesForCLBTMAt( packetBitmaskArrayIndex = i, packetBitmaskValueWithMaskAsString = allZeroMAskBinaryStrings+"&&&"+maskAsString,
                                                          actionParamValue=i * bitMaskLength + j , priority=i * bitMaskLength + j+1) #1 added in the prioity bcz  0 priority doesn;t work
                # switchObject.addTernaryEntriesForCLBTMAt( packetBitmaskArrayIndex = i, packetBitmaskValueWithMaskAsString = allOneMAskBinaryString+"&&&"+maskAsString,
                #                                           actionParamValue=i * bitMaskLength + j ,
                #                                           priority= (bitMaskArrayMaxIndex * bitMaskLength)-(i * bitMaskLength + j)) #1 added in the prioity bcz  0 priority doesn;t work

    def load_balancer_config_thread_function(self):
        logger.info("Thread %s: starting", "load_balancer_config_thread_function")
        start = time.time()
        switchObject = self.nameToSwitchMap.get(ConfConst.CLB_TESTER_DEVICE_NAME)  # we will test with only one switch. so no need to consider others
        distr1InstallFlag = False #This means this distribution is not installed
        distr2InstallFlag = False
        # Here we will insert tcam entries
        print("Initializinf the MAT")
        self.initMAT(switchObject = switchObject, bitMaskLength = ConfConst.BITMASK_LENGTH)
        while(self.isRunning):
            currentTime = time.time()
            if ( (currentTime - start) > ConfConst.DISTRO1_INSTALL_DELAY) and ( (currentTime - start) < ConfConst.DISTRO2_INSTALL_DELAY) and (distr1InstallFlag == False):
                accumulatedDistribution = self.getAccumulatedDistribution(ConfConst.LOAD_DISTRIBUTION_1)
                print("Old distrib was "+str(json.dumps(ConfConst.LOAD_DISTRIBUTION_1)))
                print("accumulated distrib is "+str(json.dumps(accumulatedDistribution)))
                packetOutList = self.installDistributionInCPAndGeneratePacketOutMessages(accumulatedDistribution, firstTimeFlag=True)
                for p in packetOutList:
                    switchObject.send_already_built_control_packet_for_load_balancer(p)
                distr1InstallFlag = True
            if ( (currentTime - start) > ConfConst.DISTRO2_INSTALL_DELAY) and (distr2InstallFlag == False):
                accumulatedDistribution = self.getAccumulatedDistribution(ConfConst.LOAD_DISTRIBUTION_2)
                print("Old distrib was "+str(json.dumps(ConfConst.LOAD_DISTRIBUTION_2)))
                print("accumulated distrib is "+str(json.dumps(accumulatedDistribution)))
                packetOutList = self.installDistributionInCPAndGeneratePacketOutMessages(accumulatedDistribution)
                for p in packetOutList:
                    switchObject.send_already_built_control_packet_for_load_balancer(p)
                distr2InstallFlag = True
            time.sleep(1)
            #Now reset the counter
            pktForCounterReset = self.buildMetadataBasedPacketOut( clabFlag=128,  linkID=0,
                                                                   bitmask=0, level_to_link_id_store_index = 0) # Here only lcabFlag matters others not
            switchObject.send_already_built_control_packet_for_load_balancer(pktForCounterReset)
        pass



    def buildMetadataBasedPacketOut(self,  clabFlag,   linkID, bitmask, level_to_link_id_store_index , port = 255):
        '''

        port_num_t  egress_port;
        bit<7>      _pad;
        //Previous all fields are not necessary for CLB. TODO  at sometime we will trey to clean up them. But at this moment we are not focusing on that
        bit<8> clb_flags; //Here we will keep various falgs for CLB
        //--------bit-7--------|| If this bit is set then reet the counter
        //--------bit-6--------|| If this bit is set then this is a port delete packet
        //--------bit-5--------|| If this bit is set then this is a port insert packet
        //--------bit-4--------|| Other bits are ununsed at this moment
        //--------bit-3--------||
        //--------bit-2--------||
        //--------bit-1--------||
        //--------bit-0--------||


        bit<32> link_id;
        bit<32> bitmask; //Here we are keeping all 32 bit to avoid compile time configuration complexity. At apply blo0ck we will slice necesssary bits.
        bit<32> level_to_link_id_store_index;  //
        '''

        rawPktContent = (255).to_bytes(2,'big') # first 2 byte egressport and padding
        rawPktContent = rawPktContent + (clabFlag).to_bytes(1,'big')
        rawPktContent = rawPktContent + (linkID).to_bytes(4,'big')
        rawPktContent = rawPktContent + (bitmask).to_bytes(4,'big')
        rawPktContent = rawPktContent + (level_to_link_id_store_index).to_bytes(4,'big')

        packet_out_req = p4runtime_pb2.StreamMessageRequest()
        port_hex = port.to_bytes(length=2, byteorder="big")
        packet_out = p4runtime_pb2.PacketOut()
        egress_physical_port = packet_out.metadata.add()
        egress_physical_port.metadata_id = 1
        egress_physical_port.value = port_hex

        clb_flag_metadata_field = packet_out.metadata.add()
        clb_flag_metadata_field.metadata_id = 3
        clb_flag_metadata_field.value = (clabFlag).to_bytes(1,'big')

        linkID_metadata_field = packet_out.metadata.add()
        linkID_metadata_field.metadata_id = 4
        linkID_metadata_field.value = (linkID).to_bytes(4,'big')

        bitmask_metadata_field = packet_out.metadata.add()
        bitmask_metadata_field.metadata_id = 5
        bitmask_metadata_field.value = (bitmask).to_bytes(4,'big')

        level_to_link_id_store_index_metadata_field = packet_out.metadata.add()
        level_to_link_id_store_index_metadata_field.metadata_id = 6
        level_to_link_id_store_index_metadata_field.value = (level_to_link_id_store_index).to_bytes(4,'big')

        packet_out.payload = rawPktContent
        packet_out_req.packet.CopyFrom(packet_out)
        return packet_out_req


    def installDistributionInCPAndGeneratePacketOutMessages(self, weightDistribution, firstTimeFlag=False):
        '''
        This function process the whole distribution and generates all the pcaket_out messages to be sent to DP
        and store them in a list. And return the list
        :param weightDistribution:
        :return:
        '''
        packetOutList = []
        for e in weightDistribution:
            link = e[0]
            if(firstTimeFlag == False): # At the first time we do not need to delete any distribution. If we delte link i+1 may delete Link i th newly installed distribution
                oldLevel = self.linkToCurrentLevel.get(link)
                #index = int(oldLevel / self.bitMaskLength)
                index = 0 #For fat bitmask index is always 0
                position = oldLevel % self.bitMaskLength
                #modify the bitmask
                self.bitMaskArray[index] = modifyBit(self.bitMaskArray[index], position, 0)
                #make a packet_out message
                # 64 = 01000000--> pkt delete
                pktForDeletelink = self.buildMetadataBasedPacketOut( clabFlag=64, linkID=0,
                                                       bitmask=self.bitMaskArray[index], level_to_link_id_store_index = oldLevel)
                packetOutList.append(pktForDeletelink)
            newLevel = e[1]
            self.linkToCurrentLevel[link] = newLevel
            #index = int(newLevel / self.bitMaskLength)
            index = 0 #For fat bitmask index is always 0
            position = newLevel % self.bitMaskLength
            #make a packet_out message now and insert In List parallely modify the self.bitMaskArray[index]
            self.bitMaskArray[index] = modifyBit(self.bitMaskArray[index], position, 1)
            pktForInsertlink = self.buildMetadataBasedPacketOut( clabFlag=64,  linkID=link,
                                                   bitmask=self.bitMaskArray[index], level_to_link_id_store_index = newLevel)
            packetOutList.append(pktForInsertlink)
        return packetOutList

    def getAccumulatedDistribution(self, disrtibution):
        accumulatedDistribution = []
        sum =0
        for e in disrtibution:
            sum = sum + e[1]
            accumulatedDistribution.append((e[0],sum-1))
        return accumulatedDistribution

class BinaryMask:
    def __init__(self, length):
        self.bits=[]
        self.length = length
        for i in range(0,self.length):
            self.bits.append(0)

    def setNthBitWithB(self,n,b):
        self.bits[(len(self.bits) - 1 )-n] = b
    def setAllBitOne(self):
        for i in range(0,self.length):
            self.bits[i]  = 1

    def setAllBitMinuxOneEqualX(self):
        for i in range(0,self.length):
            self.bits[i]  = -1

    def getBinaryString(self):
        val = "0b"
        for i in range(0, self.length):
            if(self.bits[i] == 0):
                val = val + "0"
            elif (self.bits[i] == 1):
                val = val + "1"
            else:
                val = val + "X"
        return  val

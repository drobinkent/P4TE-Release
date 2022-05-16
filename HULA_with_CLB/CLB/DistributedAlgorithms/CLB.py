'''
Here we will implement the generic data structure for load balancer and K-path problem
'''
import copy

import bitarray as ba
import bitarray.util as bautil
import ConfigConst as CC


INVALID_NEXT_BLOCK = -1

class CLB:
    # This class is basically for imeplementing the capacity extension mechanism of CLB.
    #Still not tested and some features are incomplete
    def __init__(self,allLinksAsList, totalWeightGroups, bitMaskLength):
        self.totalWeightGroups = totalWeightGroups
        self.bitMaskLength = bitMaskLength
        self.linkToCurrentLevel={}
        self.bitMaskArray= []
        self.isBitMaskBlockEmpty= []
        self.nextBlockIndex = []
        self.linkToCurrentWeightGroupMap={}
        self.weightGroupToLinkMap={}
        for l in allLinksAsList:
            self.linkToCurrentWeightGroupMap[l] = 0
        for i in range (0, int(self.totalWeightGroups/self.bitMaskLength)):
            bitArray = ba.bitarray(bitMaskLength, endian = 'big')
            bitArray.setall(0)
            self.bitMaskArray.append(bitArray)
            self.isBitMaskBlockEmpty.append(True)
            self.nextBlockIndex.append(INVALID_NEXT_BLOCK)

    def print(self):
        print("linkToCurrentWeightGroupMap is ")
        for k in self.linkToCurrentWeightGroupMap.keys():
            print(self.linkToCurrentWeightGroupMap)
        print("linkToCurrentWeightGroup is ")
        for k in self.weightGroupToLinkMap.keys():
            print(self.weightGroupToLinkMap)
        print("BitMaskArray Details")
        print("Index-------Bitmask------isEmpty --- Nextblock")
        for i in range (0, len(self.bitMaskArray)):
            print("---" + str(i) +"-------" + str(self.bitMaskArray[i].to01()) + " ------" + str(self.isBitMaskBlockEmpty[i]) + "--------: " + str(self.nextBlockIndex[i]))

    def getAccumulatedDistribution(self, disrtibution):
        accumulatedDistribution = []
        sum =0
        for e in disrtibution:
            sum = sum + e[1]
            accumulatedDistribution.append((e[0],sum-1))
        return accumulatedDistribution

    def installDistributionInCPAndGeneratePacketOutMessages(self, weightDistribution, firstTimeFlag=False):
        weightDistribution = self.getAccumulatedDistribution(weightDistribution)
        lastPositionCheckerBitMask = ba.bitarray(self.bitMaskLength)
        lastPositionCheckerBitMask.setall(0)
        lastPositionCheckerBitMask[len(lastPositionCheckerBitMask)-1] =1

        #TODO : from the weight distribution we must have to identify who can be our possible next block of a group.
        # that's why we will use the isEmptyBlock member
        #Iterate over the distribution and set eachblocks isEmpty
        for l in range(0, len(weightDistribution)) :
            e= weightDistribution[l]
            newWeightGroup = e[1]
            newBitMaskArrayIndex = int(newWeightGroup/self.bitMaskLength)
            self.isBitMaskBlockEmpty[newBitMaskArrayIndex] = False

        for l in range(0, len(weightDistribution)) :
            e= weightDistribution[l]
            link = e[0]
            if(firstTimeFlag == False): # At the first time we do not need to delete any distribution. If we delet link i+1 may delete Link i th newly installed distribution
                oldWeightGroup = self.linkToCurrentWeightGroupMap.get(link)
                bitMaskArrayIndex = int(oldWeightGroup/ self.bitMaskLength)
                positionInbitMask = oldWeightGroup % self.bitMaskLength
                self.bitMaskArray[bitMaskArrayIndex][positionInbitMask] = 0
                if (bautil.ba2int((self.bitMaskArray[bitMaskArrayIndex] and lastPositionCheckerBitMask)) ==0):
                    print("last position empty")
                    print(self.bitMaskArray[bitMaskArrayIndex])
                    self.nextBlockIndex[bitMaskArrayIndex] =  self.getNextBlock(currenntIndex = bitMaskArrayIndex)
                else:
                    print("last position non-empty")
                    print(self.bitMaskArray[bitMaskArrayIndex])
                #Generate a message here for delete

            newWeightGroup = e[1]
            self.linkToCurrentWeightGroupMap[link] = newWeightGroup
            newBitMaskArrayIndex = int(newWeightGroup/self.bitMaskLength)
            newPositionInbitMask = newWeightGroup % self.bitMaskLength
            self.bitMaskArray[newBitMaskArrayIndex][newPositionInbitMask] = 1
            oldNextBlock = self.nextBlockIndex[newBitMaskArrayIndex]
            newNextblock = self.getNextBlock(currenntIndex = newBitMaskArrayIndex)
            print("oldNextBlock is ", oldNextBlock, "newNextblock is ",newNextblock)
            if (oldNextBlock != newNextblock):
                self.nextBlockIndex[newBitMaskArrayIndex] = newNextblock

            if (bautil.ba2int((self.bitMaskArray[newBitMaskArrayIndex] & lastPositionCheckerBitMask)) ==0):
                print("last position empty")
                print(self.bitMaskArray[newBitMaskArrayIndex])
            else:
                print("last position non-empty")
                print(self.bitMaskArray[newBitMaskArrayIndex])


    def getNextBlock(self, currenntIndex):
        for i in range (currenntIndex+1, len(self.bitMaskArray)):
            if(self.isBitMaskBlockEmpty[i] == False):
                return i
        else:
            return -1


def tester():
    clb = CLB(allLinksAsList= [5,6,7,8], totalWeightGroups=32, bitMaskLength=8)
    clb.print()
    clb.installDistributionInCPAndGeneratePacketOutMessages(CC.LOAD_DISTRIBUTION_1, firstTimeFlag=True)
    print("Weight Distribution is ",clb.getAccumulatedDistribution(CC.LOAD_DISTRIBUTION_1))
    clb.print()
    clb.installDistributionInCPAndGeneratePacketOutMessages(CC.LOAD_DISTRIBUTION_2, firstTimeFlag=False)
    print("Weight Distribution is ",clb.getAccumulatedDistribution(CC.LOAD_DISTRIBUTION_2))
    clb.print()
tester()
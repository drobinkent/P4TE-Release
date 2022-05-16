import zlib
from netaddr import IPNetwork
import crc16
TOTAL_TOR_SWITCHES=10000 # we want to


experimantTableSize=1048576
experimentPrecision=10240
experimentTotalPaths=256
experimentIteration = 1
experimentHashTableSize = 65536
experimentDestinationNumbers=1
experimentIPv6Prefix = "192:0:0:1::/64"
# Assuem a leaf spine topologu where each leaf switch has N upword ports. Hence between each pair of leaf switch
# there will be at least N distinct paths (totaly edge disjoint paths between a pair a leaf siwthc can be much more larger ).
# Now, for each of the destination
#
#
#
#
#     flow tuple to hash --> then destination IP as match field and hashcode as action. these actions will be must filled upto there limit.
#
# look at figure 3 of dash paper. that's how  the wcmp will work. add a picture of it in our paper.
#
# Now in our simulation the wcmp table size is a limiting factor.
# Assume for a single destination total upward ports availalbe is P. and we can assign traffic on these
#     P ports according to some distribution. then we will convert this distribution to feasible path-weight distribution.
# at time t0 , we have to keep record how many weight is assigned on a path. assume it is w0
# at time t1 if the weight assigned on this path is w1. then we have to modify w1-w0 entries.
#
# Now assume we have a table size T. with increase in T the number should obviously change.
#
#
# How to convert to a feasible distribution. Assume we have table sizze T and precision = K .
# Then simple asuem table size as T/K. then generate the values according to some distribution in the range 1 to T/K. then simply multiple by K each value.
# and we are done.

# sum of the values have to be C/K. and each value have to be in range 0 to C/K. -- to accomodate K precision. so that after generation each alue will be multiplied by K.
# we need total tableSize number of entries.
#
#
# def wcmp(tableSize, totalPath, precision, C ):
#     we have to fit total range of C using totalPath number of data with each one multiple of K.
#     so we can say sum will be C/K (to handle precision) and total entry will be totalPath.
#
#     now generate totalpath number of data with their sum = tablesize/k.
#
#     http://sunny.today/generate-random-integers-with-fixed-sum/
#
#     import random
# random.sample(range(low, high), n)
#
# to put the probability in range 0-1. we need to try another case where instead of simply random sample the probabillity ofthe numbers will be drawn from
#     some other distribution
import numpy as np

# def generateWCMPWeights(C, tableSize, precision, totalPaths):
#     mean = C / (tableSize * totalPaths)
#     variance = int(0.85 * mean)
#
#     # min_v = variance
#     # max_v = int(C/(precision*totalPaths))
#     min_v = int(mean - variance)
#     max_v = int(mean + variance)
#     array = [min_v] * (totalPaths)
#
#     diff = int(C/(totalPaths)) - min_v * tableSize
#     while diff > 0:
#         a = np.random.randint(0, tableSize - 1)
#         if array[a] > max_v:
#             continue
#         array[a] = int(array[a]) + 1
#         diff -= 1
#     print (array)

def getTotalControlMessageForUpdatingWCMPTable(oldPathWeightDistribution, newPathWeightDistribution):
    if (len(oldPathWeightDistribution) != len(newPathWeightDistribution)):
        print("Error: Elngth of 2 path-weight distribution must have to be equal.. Exiting")
        exit(1)
    totalOldEntryDeleteRequiredInWCMPTable = 0
    totalNewEntryInsertRequiredInWCMPTable = 0

    for i in range (0, len(oldPathWeightDistribution)):
        oldWeightOfThePAth = int(oldPathWeightDistribution[i])
        newWeightOfThePath = int(newPathWeightDistribution[i])
        if (oldWeightOfThePAth == newWeightOfThePath):
            print("Old and new weight of the path is same. Hence no entry is required to be deleted or entered in the WCMP Table")
        else:
            if(oldWeightOfThePAth > newWeightOfThePath):
                print("Old weight of the path is ", str(oldWeightOfThePAth)+ " and new weight of the path is ", str(newWeightOfThePath))
                print(str(oldWeightOfThePAth-newWeightOfThePath)+ " entries have to be deleted for the path ")
                totalOldEntryDeleteRequiredInWCMPTable = oldWeightOfThePAth-newWeightOfThePath
            else:
                print("Old weight of the path is ", str(oldWeightOfThePAth)+ " and new weight of the path is ", str(newWeightOfThePath))
                print(str(newWeightOfThePath-oldWeightOfThePAth)+ " entries have to be inserted for the path ")
                totalNewEntryInsertRequiredInWCMPTable = newWeightOfThePath-oldWeightOfThePAth
    print("Total update (both insert and delete) required for the iteration is "+str(totalOldEntryDeleteRequiredInWCMPTable+totalNewEntryInsertRequiredInWCMPTable))
    return totalOldEntryDeleteRequiredInWCMPTable+totalNewEntryInsertRequiredInWCMPTable

def generatePathWeights(tableSize, precision, totalPaths, iteration):
    # mean = C / (tableSize * totalPaths)
    _sum = tableSize / precision
    n = totalPaths

    rnd_array = np.random.multinomial(_sum, np.ones(n)/n, size=iteration)
    rnd_array = rnd_array*precision
    # print(rnd_array)
    # print("Sum is ", np.sum(rnd_array))
    # print(list(rnd_array))
    total = 0
    for i in range (0,len(rnd_array[0])):
        rnd_array[0][i] = rnd_array[0][i]+total
        total = rnd_array[0][i]


    return  rnd_array




def wcmpUpdateCalculation(tableSize, precision, totalPaths, iteration):
    pathWeights = list(generatePathWeights(tableSize, precision, totalPaths, iteration ))
    oldPathWeightDistribution  = np.zeros(shape = experimentTotalPaths,dtype="int")
    print(oldPathWeightDistribution)
    newPathWeightDistribution =  pathWeights[0]
    total = 0
    for i in range (0, experimentIteration-1):
        total = total + (getTotalControlMessageForUpdatingWCMPTable(oldPathWeightDistribution, newPathWeightDistribution))
        oldPathWeightDistribution = pathWeights[i]
        newPathWeightDistribution =  pathWeights[i+1]
        print("Total is "+str(total))

#wcmpUpdateCalculation(tableSize=experimantTableSize, precision=experimentPrecision, totalPaths=experimentTotalPaths, iteration = experimentIteration)

class CrcHashTable:
    def __init__(self, tableSize):
        self.table = []
        self.tableSize = tableSize
        self.totalInsertion =  0
        self.collisionNumer = 0
        self.existingEntriesInTable = 0
        for i in range (0, self.tableSize):
                self.table.append(-1)

    def insert(self, ipaddress, port):
        bytesFromIP = bytes(ipaddress)
        # print("bytes from ip address is "+str(bytesFromIP))
        # bytesFromPort = bytes(int(port))
        port = int(port)
        bytesFromPort = port.to_bytes(8, byteorder = 'big')
        # print("bytes from ip port is "+str((bytesFromPort)))
        bytesData = bytesFromIP + bytesFromPort
        # hashCode = crc16.crc16xmodem(bytesData,0x1D0F)
        hashCode = crc16.crc16xmodem(bytesData,0x1D0F)%experimentHashTableSize
        print("hashcode is "+str(hashCode))
        # hashCode = zlib.crc32(bytesData,0x1D0F) % experimentHashTableSize
        # hashCode = hash(bytesData)
        # hashCode = hashCode % experimentHashTableSize
        if(self.table[hashCode] != -1):
            self.collisionNumer = self.collisionNumer+1
            self.table[hashCode] = port
        else:
            self.table[hashCode] = port
            self.totalInsertion = self.totalInsertion+1
        self.existingEntriesInTable = self.existingEntriesInTable +1
    def delete(self, ipaddress, port):
        bytesFromIP = bytes(ipaddress)
        bytesFromPort = bytes(port)
        bytesData = bytesFromIP + bytesFromPort
        # hashCode = crc16.crc16xmodem(bytesData,0x1D0F)
        hashCode = crc16.crc16xmodem(bytesData,0x1D0F)%experimentHashTableSize
        # hashCode = zlib.crc32(bytesData,0x1D0F) % experimentHashTableSize
        # hashCode = hash(bytesData)
        # hashCode = hashCode % experimentHashTableSize
        self.table[hashCode]  = -1
        self.existingEntriesInTable = self.existingEntriesInTable -1
        return


# for ip in IPNetwork('10:0:1::/64'):
#     print ('%s' % ip)
#     print(zlib.crc32(bytes(ip)))


# generate specific number of ip address. for each one of them calculate a distribution.
#     according to that distribution get what is the weightlevel of the ports.
# then for all of the ip-port combination calculate hashtable collision


def calculateHashCollision():
    ipaddressList = []
    i = 0
    # hTable =CrcHashTable(experimentHashTableSize)
    for ip in IPNetwork(experimentIPv6Prefix):
        # print ('%s' % ip)
        # print(zlib.crc32(bytes(ip)))
        weightList = []
        for j in range (0,experimentIteration):
            pathWeightBeforeAccumulation = list(generatePathWeights(tableSize=experimantTableSize, precision=experimentPrecision, totalPaths=experimentTotalPaths, iteration = experimentIteration))
            weightList.append(pathWeightBeforeAccumulation)
        ipaddressList.append((ip,weightList))
        i =i+1
        if (i>=experimentDestinationNumbers):
            break
    for j in range (0,experimentIteration):
        hTable =CrcHashTable(experimentHashTableSize)
        for e in ipaddressList:
            ip = e[0]
            pathWeights = e[1]
            # if(j>0):
            #     for k in range(0,len(pathWeights[j-1][0])):
            #         pWeight = pathWeights[j-1][0][k]
            #         hTable.delete(ip,k*pWeight*experimentPrecision)
            for k in range(0,len(pathWeights[j][0])):
                pWeight = pathWeights[j][0][k]
                print("Inerting IP: "+str(ip)+" and weight "+str(pWeight))
                print("Inerting IP: "+str(ip)+" and port "+str(pWeight))
                hTable.insert(ip,pWeight*experimentPrecision)

        print("Total Collision is "+str(hTable.collisionNumer))
        print("Total insertion is "+str(hTable.totalInsertion))
        print("Total entries in the table is "+str(hTable.existingEntriesInTable))


calculateHashCollision()


# def generate_random_integers(_sum, n):
#     mean = int(_sum / n)
#     variance = int(0.55 * mean)
#
#     min_v = mean - variance
#     max_v = mean + variance
#     array = [min_v] * n
#
#     diff = _sum - min_v * n
#     while diff > 0:
#         a = np.random.randint(0, n - 1)
#         # np.random.normal(mu, sigma, 1000)
#         if array[a] >= max_v:
#             continue
#         array[a] += 1
#         diff -= 1
#     print (array)
#     print(sum(array))
#     print(min(array))
#     print(max(array))
#
# generate_random_integers(128000, 128)

# from scipy.stats import truncnorm
#
# def get_truncated_normal(mean=0, sd=1, low=0, upp=10):
#     return truncnorm(
#         (low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd)
# X = get_truncated_normal(mean=8, sd=2, low=1, upp=20)
# val = X.rvs(4000).astype(int)
# print(val)
# print(sum(val))
import zlib

import crc16
import numpy as np
from netaddr import IPNetwork
from scipy.stats import truncnorm





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
        hashCode = crc16.crc16xmodem(bytesData,0x000) % self.tableSize
        # hashCode = zlib.crc32(bytesData,0x1D0F) % self.tableSize
        # print("hashcode is "+str(hashCode))
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
        hashCode = crc16.crc16xmodem(bytesData,0x1D0F) % self.tableSize
        # hashCode = zlib.crc32(bytesData,0x1D0F) % self.tableSize
        # hashCode = hash(bytesData)
        # hashCode = hashCode % experimentHashTableSize
        self.table[hashCode]  = -1
        self.existingEntriesInTable = self.existingEntriesInTable -1
        return



def get_truncated_normal(mean=0, sd=1, low=0, upp=10):
    return truncnorm(
        (low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd)
# X = get_truncated_normal(mean=8, sd=2, low=1, upp=10)



def generate_random_integers(peakLoad, totalPaths, standardDeviationOfPAthWeights, iteration, precision):
    mean = int((peakLoad / totalPaths)/precision)
    # variance = int(0.55 * mean)
    standardDeviationOfPAthWeightsVal= int(mean*standardDeviationOfPAthWeights)

    min_v = mean - standardDeviationOfPAthWeightsVal
    max_v = mean + standardDeviationOfPAthWeightsVal

    pathweights = []
    for i in range (0, iteration):
        array = [min_v] * totalPaths

        diff = int((peakLoad / precision)) - min_v * totalPaths
        X = get_truncated_normal(mean=mean, sd=standardDeviationOfPAthWeights, low=min_v, upp=max_v)
        val = X.rvs(int(peakLoad/precision)).astype(int)
        while diff > 0:
            a = np.random.randint(1, totalPaths)

            if array[a] >= max_v:
                continue
            array[a] += 1
            diff -= 1
        # print (array)
        # print(sum(array))
        # print(min(array))
        # print(max(array))
        # print(np.std(array))
        for a in array:
            a=a*precision
        total = 0
        for i in range (0,len(array)):
            array[i] = array[i]+total
            total = array[i]
        pathweights.append(array)
    return  pathweights


def calculateHashCollision(experimentIPv6Prefix, experimentDestinationNumbers, experimentIteration, peakLoad,  totalPaths, precision,standardDeviationOfPAthWeights,hashtableSize):
    ipaddressList = []
    i = 0
    for ip in IPNetwork(experimentIPv6Prefix):
        # print ('%s' % ip)
        # print(zlib.crc32(bytes(ip)))
        weightList = []
        # for j in range (0,experimentIteration):
        #     pathWeightBeforeAccumulation = generate_random_integers(peakLoad, totalPaths, standardDeviationOfPAthWeights, experimentIteration, precision)
        #     weightList.append(pathWeightBeforeAccumulation)
        weightList.append(generate_random_integers(peakLoad, totalPaths, standardDeviationOfPAthWeights, experimentIteration, precision))
        ipaddressList.append((ip,weightList))
        i =i+1
        if (i>=experimentDestinationNumbers):
            break
    collision = 0
    for j in range (0,experimentIteration):
        hTable =CrcHashTable(hashtableSize)
        for e in ipaddressList:
            ip = e[0]
            pathWeights = e[1]
            # if(j>0):
            #     for k in range(0,len(pathWeights[j-1][0])):
            #         pWeight = pathWeights[j-1][0][k]
            #         hTable.delete(ip,k*pWeight*experimentPrecision)
            for k in range(0,len(pathWeights[0][j])):
                pWeight = pathWeights[0][j][k]
                # print("Inerting IP: "+str(ip)+" and weight "+str(pWeight))
                # print("Inerting IP: "+str(ip)+" and port "+str(pWeight))
                hTable.insert(ip,pWeight*precision)
        collision = collision + hTable.collisionNumer
        # print("Total Collision is "+str(hTable.collisionNumer))
        # print("Total insertion is "+str(hTable.totalInsertion))
        # print("Total entries in the table is "+str(hTable.existingEntriesInTable))
    print("Hashtable size and Average collision number is ("+str(hashtableSize)+","+str(collision/experimentIteration)+")")
    print("Total Stateful Memory location requiremnt in storing the path information without using the hashcode is : "+str((peakLoad/precision)*experimentDestinationNumbers))

# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=10, experimentIteration=10, peakLoad= 1048576,  totalPaths=256, precision=4,standardDeviationOfPAthWeights=.8, hashtableSize = 1024)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=10, experimentIteration=10, peakLoad= 1048576,  totalPaths=256, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 2048)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=10, experimentIteration=10, peakLoad= 1048576,  totalPaths=256, precision=32,standardDeviationOfPAthWeights=.8, hashtableSize = 3072)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=10, experimentIteration=10, peakLoad= 1048576,  totalPaths=256, precision=32,standardDeviationOfPAthWeights=.4, hashtableSize = 3072)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=10, experimentIteration=10, peakLoad= 1048576,  totalPaths=256, precision=32,standardDeviationOfPAthWeights=.4, hashtableSize = 4096)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=10, experimentIteration=10, peakLoad= 1048576,  totalPaths=256, precision=32,standardDeviationOfPAthWeights=.4, hashtableSize = 8192)


# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=24, experimentIteration=10, peakLoad= 1048576,  totalPaths=256, precision=32,standardDeviationOfPAthWeights=.2, hashtableSize = 65536)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=48, experimentIteration=10, peakLoad= 1048576,  totalPaths=256, precision=32,standardDeviationOfPAthWeights=.2, hashtableSize = 65536)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=72, experimentIteration=10, peakLoad= 1048576,  totalPaths=256, precision=32,standardDeviationOfPAthWeights=.2, hashtableSize = 65536)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=96, experimentIteration=10, peakLoad= 1048576,  totalPaths=256, precision=32,standardDeviationOfPAthWeights=.2, hashtableSize = 65536)
# print("\n\n\n\n")
print("I Tbps ")
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=32, precision=4,standardDeviationOfPAthWeights=.2, hashtableSize = 1024)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=32, precision=16,standardDeviationOfPAthWeights=.2, hashtableSize = 2048)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=32, precision=32,standardDeviationOfPAthWeights=.2, hashtableSize = 3072)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=64, precision=4,standardDeviationOfPAthWeights=.2, hashtableSize = 1024)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=64, precision=16,standardDeviationOfPAthWeights=.2, hashtableSize = 2048)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=64, precision=32,standardDeviationOfPAthWeights=.2, hashtableSize = 3072)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=64, precision=4,standardDeviationOfPAthWeights=.2, hashtableSize = 1024)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=64, precision=16,standardDeviationOfPAthWeights=.2, hashtableSize = 2048)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=64, precision=32,standardDeviationOfPAthWeights=.2, hashtableSize = 3072)

print("\n\n\n\n")


# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=32, precision=4,standardDeviationOfPAthWeights=.5, hashtableSize = 1024)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=32, precision=16,standardDeviationOfPAthWeights=.5, hashtableSize = 2048)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=32, precision=32,standardDeviationOfPAthWeights=.5, hashtableSize = 3072)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=64, precision=4,standardDeviationOfPAthWeights=.5, hashtableSize = 1024)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=64, precision=16,standardDeviationOfPAthWeights=.5, hashtableSize = 2048)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=64, precision=32,standardDeviationOfPAthWeights=.5, hashtableSize = 3072)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=64, precision=4,standardDeviationOfPAthWeights=.5, hashtableSize = 1024)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=64, precision=16,standardDeviationOfPAthWeights=.5, hashtableSize = 2048)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=64, precision=32,standardDeviationOfPAthWeights=.5, hashtableSize = 3072)


#
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=32, precision=4,standardDeviationOfPAthWeights=.8, hashtableSize = 1024)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=32, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 2048)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=32, precision=32,standardDeviationOfPAthWeights=.8, hashtableSize = 3072)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=64, precision=4,standardDeviationOfPAthWeights=.8, hashtableSize = 1024)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=64, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 2048)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=64, precision=32,standardDeviationOfPAthWeights=.8, hashtableSize = 3072)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=64, precision=4,standardDeviationOfPAthWeights=.8, hashtableSize = 1024)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=64, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 2048)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=64, precision=32,standardDeviationOfPAthWeights=.8, hashtableSize = 3072)
#



# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=512, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 1024)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=512, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 2048)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=512, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 3072)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=512, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 4096)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=512, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 8192)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=512, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 10240)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=512, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 12800)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=512, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 2048)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=512, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 3072)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=512, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 1024)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=512, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 2048)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=512, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 3072)

# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=256, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 1024)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=256, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 2048)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=256, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 3072)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=256, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 4096)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=256, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 8192)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=256, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 10240)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1048576,  totalPaths=256, precision=16,standardDeviationOfPAthWeights=.8, hashtableSize = 12800)
#

print("Load balancing 1 Tbps (1*1024*1024*1024*1024 bps incoming load at precision of 4 Mb (4*1048576) using various length of arrray for WeightLevelToPathIDMapping")
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=4*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 1024)
calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=4*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 2048)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=4*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 3072)
calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=4*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 4096)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=4*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 5120)
calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=4*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 6144)
calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=4*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 8192)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=4*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 7168)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=4*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 8192)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=4*1048576,standardDeviationOfPAthWeights=.8, hashtableSize = 10240)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=4*1048576,standardDeviationOfPAthWeights=.8, hashtableSize = 12800)


print("Load balancing 1 Tbps (1*1024*1024*1024*1024 bps incoming load at precision of 8 Mb (8*1048576) using various length of arrray for WeightLevelToPathIDMapping")
print("Deviation 0.5")

# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=8*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 1024)
calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=8*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 2048)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=8*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 3072)
calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=8*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 4096)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=8*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 5120)
calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=8*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 6144)
calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=8*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 8192)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=8*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 7168)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=8*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 8192)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=4*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 10240)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=4*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 12800)


print("Load balancing 1 Tbps (1*1024*1024*1024*1024 bps incoming load at precision of 16 Mb (16*1048576) using various length of arrray for WeightLevelToPathIDMapping")
print("Deviation 0.5")

# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=16*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 1024)
calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=16*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 2048)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=16*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 3072)
calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=16*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 4096)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=16*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 5120)
calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=16*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 6144)
calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=16*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 8192)
calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=16*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 8192*2)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=16*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 7168)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=16*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 8192)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=4*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 10240)
# calculateHashCollision(experimentIPv6Prefix= "10:0:42:5::/96", experimentDestinationNumbers=1, experimentIteration=100, peakLoad= 1*1024*1024*1024*1024,  totalPaths=128, precision=4*1048576,standardDeviationOfPAthWeights=.5, hashtableSize = 12800)



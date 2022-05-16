import numpy as np
from scipy.stats import truncnorm


def get_truncated_normal(mean=0, sd=1, low=0, upp=10):
    return truncnorm(
        (low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd)
# X = get_truncated_normal(mean=8, sd=2, low=1, upp=10)



def generate_random_integers(wcmpTableSize, totalPaths, standardDeviationOfPAthWeights, iteration,precision):
    mean = int(wcmpTableSize / totalPaths)
    # variance = int(0.55 * mean)
    standardDeviationOfPAthWeights= (mean*standardDeviationOfPAthWeights)

    min_v = mean - standardDeviationOfPAthWeights
    max_v = mean + standardDeviationOfPAthWeights

    pathweights = []
    for i in range (0, iteration):
        array = [min_v] * totalPaths

        diff = wcmpTableSize - min_v * totalPaths
        X = get_truncated_normal(mean=mean, sd=standardDeviationOfPAthWeights, low=min_v, upp=max_v)
        val = X.rvs(wcmpTableSize).astype(int)
        while diff > 0:
            a = np.random.randint(0, totalPaths - 1)

            if array[a] >= max_v:
                continue
            array[a] += 1
            diff -= 1
        # print (array)
        # print(sum(array))
        # print(min(array))
        # print(max(array))
        # print(np.std(array))
        # for a in array:
        #     a=a*precision
        pathweights.append(array)
        # print(array)
    return  pathweights

# generate_random_integers(wcmpTableSize=3200,totalPaths=32,standardDeviationOfPAthWeights=.5)


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
            # print("Old and new weight of the path is same. Hence no entry is required to be deleted or entered in the WCMP Table")
            pass
        else:
            if(oldWeightOfThePAth > newWeightOfThePath):
                # print("Old weight of the path is ", str(oldWeightOfThePAth)+ " and new weight of the path is ", str(newWeightOfThePath))
                # print(str(oldWeightOfThePAth-newWeightOfThePath)+ " entries have to be deleted for the path ")
                totalOldEntryDeleteRequiredInWCMPTable = totalOldEntryDeleteRequiredInWCMPTable+(oldWeightOfThePAth-newWeightOfThePath)
            else:
                # print("Old weight of the path is ", str(oldWeightOfThePAth)+ " and new weight of the path is ", str(newWeightOfThePath))
                # print(str(newWeightOfThePath-oldWeightOfThePAth)+ " entries have to be inserted for the path ")
                totalNewEntryInsertRequiredInWCMPTable = totalNewEntryInsertRequiredInWCMPTable+( newWeightOfThePath-oldWeightOfThePAth)
    # print("Total update (both insert and delete) required for the iteration is "+str(totalOldEntryDeleteRequiredInWCMPTable+totalNewEntryInsertRequiredInWCMPTable))
    return totalOldEntryDeleteRequiredInWCMPTable+totalNewEntryInsertRequiredInWCMPTable

def wcmpUpdateCalculation(tableSize, precision, totalPaths, sigma, iteration):
    if (sigma >= 1) or (sigma <= 0):
        print("Standard deviation of the paths must be in between 0 and 1")
        exit(1)
    pathWeights = generate_random_integers(wcmpTableSize=int(tableSize/precision), totalPaths=totalPaths, standardDeviationOfPAthWeights=sigma, iteration=iteration, precision=precision)

    oldPathWeightDistribution  = np.zeros(shape = totalPaths,dtype="int")
    # print(oldPathWeightDistribution)
    newPathWeightDistribution =  pathWeights[0]
    total = 0
    for i in range (0, iteration-1):
        total = total + (getTotalControlMessageForUpdatingWCMPTable(oldPathWeightDistribution, newPathWeightDistribution))
        oldPathWeightDistribution = pathWeights[i]
        newPathWeightDistribution =  pathWeights[i+1]
    # print("Average update message required "+str(total/iteration))
    mean = int((tableSize/precision)/totalPaths)
    print("WCMP table size: "+str(tableSize)+ " Total paths: "+str(totalPaths)+" Precision of load balancing: "+str(precision)+
          " Mean value of the path weights: "+str(mean) + " signma for the path weights: "+str(sigma )
            +" For total iteration: "+ str(iteration)+
          " Average number of update message required "+str(total/iteration))

print("Experiments for evaluating convergence time for different lengths of WCMP table size, different number of paths, ")
wcmpUpdateCalculation(tableSize=4096, precision=16,totalPaths=32, sigma=.8, iteration=10)
wcmpUpdateCalculation(tableSize=4096, precision=16,totalPaths=64, sigma=.8, iteration=10)
wcmpUpdateCalculation(tableSize=4096, precision=16,totalPaths=64, sigma=.8, iteration=10)
wcmpUpdateCalculation(tableSize=8192, precision=16,totalPaths=128, sigma=.8, iteration=10)
wcmpUpdateCalculation(tableSize=10240, precision=16,totalPaths=256, sigma=.8, iteration=10)
wcmpUpdateCalculation(tableSize=12800, precision=16,totalPaths=256, sigma=.8, iteration=10)
print("\n\n\n\n")
print("Experiments for evaluating convergence time for different precision of load balancing, ")
wcmpUpdateCalculation(tableSize=10240, precision=2, totalPaths=64, sigma=.8, iteration=10)
wcmpUpdateCalculation(tableSize=10240, precision=4, totalPaths=64, sigma=.8, iteration=10)
wcmpUpdateCalculation(tableSize=10240, precision=8, totalPaths=64, sigma=.8, iteration=10)
wcmpUpdateCalculation(tableSize=10240, precision=16, totalPaths=64, sigma=.8, iteration=10)
wcmpUpdateCalculation(tableSize=10240, precision=32, totalPaths=64, sigma=.8, iteration=10)
wcmpUpdateCalculation(tableSize=10240, precision=32, totalPaths=64, sigma=.8, iteration=10)
# wcmpUpdateCalculation(tableSize=24800, precision=32, totalPaths=128, sigma=.8, iteration=10



# wcmpUpdateCalculation(tableSize=12800, precision=2,totalPaths=32, standardDeviationOfPAthWeights=.8, iteration=10)
# wcmpUpdateCalculation(tableSize=12800, precision=4,totalPaths=32, standardDeviationOfPAthWeights=.8, iteration=10)
# wcmpUpdateCalculation(tableSize=12800, precision=4,totalPaths=32, standardDeviationOfPAthWeights=.1, iteration=10)
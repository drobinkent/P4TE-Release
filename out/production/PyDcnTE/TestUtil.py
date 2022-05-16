

def getLocationIndexes(self):
    hostIndex=self.basic.name[self.basic.name.index("h")+1: self.basic.name.index("p")]
    podIndex = self.basic.name[self.basic.name.index("p")+1: self.basic.name.index("l")]
    leafSwitchIndex=self.basic.name[self.basic.name.index("l")+1: len(self.basic.name)]
    return hostIndex, leafSwitchIndex, podIndex

def getPeerHostName(hostIndex, leafSwitchIndex, podIndex , portCount):
    peerHostIndex = int((int(hostIndex)+1+ int(portCount)/2) % (int(portCount)/2))
    peerLeafSwitchIndex = int( (int(leafSwitchIndex)+1+ (int(portCount)/2)) % int((portCount)/2))
    peerPodIndex = int((int(podIndex)+1+ (int(portCount)/2)) % int((portCount)))
    peerHostName = "h"+str(peerHostIndex)+"p"+str(peerPodIndex)+"l"+str(peerLeafSwitchIndex)
    return peerHostName
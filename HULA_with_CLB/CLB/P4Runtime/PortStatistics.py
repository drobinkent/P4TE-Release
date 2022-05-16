

class PortStatistics:

    def __init__(self):
        self._upwardPortEgressPacketCounter= {}  # This will keeep counter for how many packets have been emitted through this port. Which is the CDF of upward plink utilization
        self._downwardPortEgressPacketCounter= {}
        self._upwardPortIngressPacketCounter= {}  # This will keeep counter for how many packets have been recived through this port. Which is the CDF of downward plink utilization
        self._downwardPortInressPacketCounter= {}
        self._CPUPortIngressPacketCounter= 0 # This will keeep counter for how many packets have been recived through CPU port.
        self._CPUPortEgressPacketCounter= 0
        self._LBMissedPackets =0
        return
    def setLBMissedPackets(self, lBMissedPackets):
        self._LBMissedPackets = lBMissedPackets
    def getLBMissedPackets(self):
        return self._LBMissedPackets

    def setUpwardPortEgressPacketCounter(self, port, value=0):
        self._upwardPortEgressPacketCounter[port] = value

    def getUpwardPortEgressPacketCounter(self, port):
        return self._upwardPortEgressPacketCounter.get(port) if self._upwardPortEgressPacketCounter.get(port) is not None else 0

    def setDownwardPortEgressPacketCounter(self, port, value=0):
        self._downwardPortEgressPacketCounter[port] = value

    def getDownwardPortEgressPacketCounter(self, port):
        return self._downwardPortEgressPacketCounter.get(port) if self._downwardPortEgressPacketCounter.get(port) is not None else 0

    def setUpwardPortIngressPacketCounter(self, port, value=0):
        self._upwardPortIngressPacketCounter[port] = value

    def getUpwardPortIngressPacketCounter(self, port):
        return self._downwardPortInressPacketCounter.get(port)  if self._downwardPortInressPacketCounter.get(port) is not None else 0

    def setDownwardPortIngressPacketCounter(self, port, value=0):
        self._downwardPortInressPacketCounter[port] = value

    def getDownwardPortIngressPacketCounter(self, port):
        return self._downwardPortInressPacketCounter.get(port) if self._downwardPortInressPacketCounter.get(port)  is not None else 0

    def setCPUPortIngressPacketCounter(self, value=0):
        self._CPUPortIngressPacketCounter = value

    def getCPUPortIngressPacketCounter(self):
        return self._CPUPortIngressPacketCounter  if self._CPUPortIngressPacketCounter   is not None else 0

    def setCPUPortEgressPacketCounter(self, value=0):
        self._CPUPortEgressPacketCounter = value

    def getCPUPortEgressPacketCounter(self):
        return self._CPUPortEgressPacketCounter if self._CPUPortEgressPacketCounter   is not None else 0

    def setQueueRateAnDepthInfo(self,queueRates, queueDepths):
        self.queueRates = queueRates
        self.queueDepths = queueDepths
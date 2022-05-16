
class RoutingInfo:

    def __init__(self, name):
        self.idToGroupMap = {}
        self.idToMetricsLevelRangeLowerValueMap = {}
        self.idToMetricsLevelRangeHigherValueMap = {}
        self.idToTernaryTableEntryPriorityValueMap = {}
        self.portNumToGroupMap = {}
        self.portNumToPreviousMetricsValueMap = {}   #This gives us way to decide without relying on the threshold based evnet decided by data plane. If
        # sometimes we think that, though the data plane have decided that the moving avg is increased and decreased, control plane can use it's own history to decide.
        self.portNumToActionProfileMemberMap={}
        self.name = name
        return

    def addPortToActionProfileMemberMap(self, port, actionProfileObject):
        if (self.portNumToActionProfileMemberMap.get(port) == None):
            self.portNumToActionProfileMemberMap[port] = actionProfileObject
        else:
            raise Exception("Action Profile member already for port-"+str(port)+ "already exists in "+self.name)
    def getMemberFromPortToActionProfileMemberMap(self, port): # we can not raise exception here. Because event can happen for any port. we only handle for the upstream ports.
        actionProfileMemberObject = self.portNumToActionProfileMemberMap.get(port)
        return  actionProfileMemberObject


    def addGroup(self, id, group, metricsLevelRangeLowerValue, metricsRangeHigherValue, ternaryMatchPriority):
        if (self.idToGroupMap.get(id) == None):
            self.idToGroupMap[id] = group
            self.idToMetricsLevelRangeLowerValueMap[id] = metricsLevelRangeLowerValue
            self.idToMetricsLevelRangeHigherValueMap[id] = metricsRangeHigherValue
            self.idToTernaryTableEntryPriorityValueMap[id] = ternaryMatchPriority

        else:
            raise Exception("Action Profile group already created for the device. Exiting")


    def getGroup(self, id):
        return self.idToGroupMap.get(id)

    def getMetricsLevelRangeLowerValueMap(self, id):
        return self.idToMetricsLevelRangeLowerValueMap.get(id)
    def getMetricsLevelRangeHigherValueMap(self, id):
        return self.idToMetricsLevelRangeHigherValueMap.get(id)

    def getTernaryTableEntryPriorityValueForTheGroup(self, id):
        return self.idToTernaryTableEntryPriorityValueMap.get(id)

    def addPortNumToGroupMapping(self, port, actionProfileGroupObject, prevMetricsValue = 0):
        if (self.portNumToGroupMap.get(port) == None):
            self.portNumToGroupMap[port] = actionProfileGroupObject
            self.portNumToPreviousMetricsValueMap[port] = prevMetricsValue
        else :
            raise Exception(" : Action Profile group for port-"+str(port)+" already exists in "+self.name)

    def getGroupByPortNumber(self, port):  # we can not raise exception here. Because event can happen for any port. we only handle for the upstream ports.
        # if (self.__portNumToGroupMap.get(port) == None):
        #     raise Exception(" : Action Profile group for port-"+str(port)+" not exists in "+self.name)
        # else :
        #     actionProfileGroupObject = self.__portNumToGroupMap.get(port)
        #     return  actionProfileGroupObject
        actionProfileGroupObject = self.portNumToGroupMap.get(port)
        return  actionProfileGroupObject

    def deletePortNumToActionProfileGroupMapping(self, port):
        del self.portNumToGroupMap[port]

    def deletePortNumToGroupMapping(self, port):
        del self.portNumToGroupMap[port]

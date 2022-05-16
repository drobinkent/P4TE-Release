#this file contains all classes related to dumping statistics in files in json format

import P4Runtime.PortStatistics as PortStatistics
from json import JSONEncoder

class PortStatisticsJSONWrapper(JSONEncoder):

    def setData(self, time, portStats, devName):
        self.portStats = portStats
        self.time = time
        self.devName = devName

    def default(self, o):
        return o.__dict__
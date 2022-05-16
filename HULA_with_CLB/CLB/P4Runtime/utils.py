import re


# See https://stackoverflow.com/a/32997046


import P4Runtime.JsonParser as jp


def my_partialmethod(func, *args1, **kwargs1):
    def method(self, *args2, **kwargs2):
        return func(self, *args1, *args2, **kwargs1, **kwargs2)
    return method


class UserError(Exception):
    def __init__(self, info=""):
        self.info = info

    def __str__(self):
        return self.info

    # TODO(antonin): is this the best way to get a custom traceback?
    def _render_traceback_(self):
        return [str(self)]


class InvalidP4InfoError(Exception):
    def __init__(self, info=""):
        self.info = info

    def __str__(self):
        return "Invalid P4Info message: {}".format(self.info)

    def _render_traceback_(self):
        return [str(self)]


def getDeviceTypeFromName(deviceName):
    #txt = "The rain in Spain"
    #x = re.search("^The.*Spain$", txt)
    if re.search("^h[0-9]+.*", deviceName):
        return jp.DeviceType.HOST
    elif re.search("^p[0-9]+.*l[0-9]+$", deviceName):
        return jp.DeviceType.LEAF_SWITCH
    elif re.search("^p[0-9]+.*s[0-9]+$", deviceName):
        return jp.DeviceType.SPINE_SWITCH
    elif re.search("^ss[0-9]+", deviceName):
        return jp.DeviceType.SUPER_SPINE_SWITCH
    else:
        return jp.DeviceType.INVALID

    return None

def reverseAndCreateNewLink(l):
    nLink = jp.Link(node1= l.node2, node2= l.node1, port1= l.port2, port2= l.port1, bw = l.bw )
    return nLink


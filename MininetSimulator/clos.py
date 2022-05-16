
import argparse

import mininet.link as MNLink
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import Host
from mininet.topo import Topo
from bmv2 import  ONOSBmv2Switch
#import jsonpickle
import json





try:
    from cStringIO import StringIO
except:
    from io import StringIO
import json
import ClosConstants as CC

CPU_PORT = 255

class IPv6Host(Host):
    def __init__(self, name, mac, ipv6, ipv6_gw,**params):
        self.name = name
        self.mac = mac
        self.ipv6 = ipv6
        self.ipv6_gw = ipv6_gw
        print("HOst name is : ", name)
        Host.__init__(self, name,inNamespace= True, **params)

    def config(self, **params):
        #super(IPv6Host, self).config(mac= self.mac, ip=self.ipv6, **params)
        self.setIP(self.ipv6)
        self.setMAC(self.mac)
        super(IPv6Host, self).config(**params)

        self.cmd('ip -4 addr flush dev %s' % self.defaultIntf())
        self.cmd('ip -6 addr flush dev %s' % self.defaultIntf())
        self.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=0")
        self.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=0")
        self.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=0")
        self.cmd('ip -6 addr add %s dev %s' % (self.ipv6, self.defaultIntf()))
        #print('ip -6 route add default via %s' % self.ipv6_gw)
        self.cmd('ip -6 route add ::/0  dev %s' %self.defaultIntf())
        self.cmd('sysctl -w net.ipv4.tcp_congestion_control=dctcp')
        #ip -6 route add ::/0  dev  interface_name
        # if self.ipv6_gw:
        #     self.cmd('ip -6 route add default via %s' % self.ipv6_gw)
        #     print('ip -6 route add default via %s' % self.ipv6_gw)
        # # Disable offload
        for attr in ["rx", "tx", "sg"]:
            cmd = "/sbin/ethtool --offload %s %s off" % (self.defaultIntf(), attr)
            self.cmd(cmd)

        def updateIP():
            return self.ipv6.split('/')[0]
        self.defaultIntf().updateIP = updateIP
        # self.cmd("./testAndMeasurement/iperf3Server.sh ")
        # self.cmd("python3 ./testAndMeasurement/iperf3_test.py "+self.name+" basic 4 &")
        print(self)
        self.cmd('/usr/sbin/sshd')
        # print("python3 ./MininetSimulator/CommandExecutor.py "+ CC.HOST_COMMAND_FOLDER+" "+self.name+ " &")
        self.cmd("python3 ./MininetSimulator/CommandExecutor.py "+ CC.HOST_COMMAND_FOLDER+" "+self.name+ " &")
        print("python3 ./MininetSimulator/TrafficDeployer.py "+ " "+self.name+ " &")
        # self.cmd("sudo python3 ./MininetSimulator/TrafficDeployer.py "+ " "+self.name+ " 0 &")
        # self.cmd("sudo python3 ./MininetSimulator/TrafficDeployer.py "+ " "+self.name+ " 1 &")

        print("Deployed comand executor")





    # def addIntf( self, intf, rename=False, **kwargs ):
    #     "Add (and reparent) an interface"
    #     self.addIntf()
    #     intf.node = self
    #     if rename:
    #         self.renameIntf( intf )

    def terminate(self):
        super(IPv6Host, self).terminate()


class ClosDCN(Topo):
    '''DCN Tuype = 2 if you want a layer 2 dcn, 3 if you want a layer 3 dcn
    But at this moment we will onyl focus on 3 layer. we will later check how can we do the 3 layer things
    =========================================================
    We will follow the pod model to build the 3-tier clos topology. The virtual chasis model is more uniform in  path length. so less challenging. That's why we will at first experiment with the
    pod model. A 3-tier clos topology based DCN built from "n" port switch can support, "n/2" hots is a leaf switch. Rest of the n/2 ports are reserved for connecting with the
    spine switches. So each leaf connects with n/2 spine switches. for each spine switch n/2 ports are reserved for connecting with leaf switches. As a result inside a single pod with n port
    switch, there are n/2 spine switch, each connected with n/2 leaf switch. there for in each pod n^2/4 hosts are supported. At layer-3, a single n port spine switch can connect with
    n such pods. there for total number hosts supported are n * (n^2/4) = n^3/4. total number of switches required for a pod are :  (for each pod (n/2 spine switch + n/2 leaf switch) = n switches
    n super spine switch each connects with a pod. so for these n pods total switches required are : n *n = n^2. With them adds the n spine switches. so in total : n+ n^2 switches

    In this topology building at first we will check the number of ports, whther they all are equal or not. Though theoretically they can be varried. but for our code we will at first assert
    them. So that on later stage we can just remove the verification part and make the connection generic.
    '''

    def __init__(self, dcnType=CC.DCN_TYPE,
                 numberOfSuperSpines=CC.CLOS_MAX_PORT_NUMBER,
                 numberOfPortsPerSuperSpine=CC.CLOS_MAX_PORT_NUMBER,
                 numberOfSpinesPerPod=CC.CLOS_MAX_PORT_NUMBER / 2,
                 numberOfPortsPerSpine=CC.CLOS_MAX_PORT_NUMBER,
                 numberOfLeavesPerSpine=CC.CLOS_MAX_PORT_NUMBER / 2,
                 numberOfPortsPerLeaf=CC.CLOS_MAX_PORT_NUMBER,
                 numberOfHostsPerLeaf=CC.CLOS_MAX_PORT_NUMBER / 2,
                 numberOfLinksBetweenLeafAndSpine=CC.CLOS_MAX_PORT_NUMBER / 2,
                 onosRestJsonFileName="./MininetSimulator/Build/netcfg.json",
                 onosMyAppCfgJson="./MininetSimulator/Build/Internalnetcfg.json",
                 autoSetMacs=False, autoStaticArp=False, *args, **kwargs):
        Topo.__init__(self, *args, **kwargs)
        self.jsonFileName = onosRestJsonFileName
        self.onosMyAppCfgJson = onosMyAppCfgJson
        self.dcnType = dcnType
        self.numberOfLinksBetweenLeafAndSpine = numberOfLinksBetweenLeafAndSpine
        self.numberOfHostsPerLeaf = numberOfHostsPerLeaf
        self.numberOfPortsPerLeaf = numberOfPortsPerLeaf
        self.numberOfLeavesPerSpine = numberOfLeavesPerSpine
        self.numberOfPortsPerSpine = numberOfPortsPerSpine
        self.numberOfSpinesPerPod = numberOfSpinesPerPod
        self.numberOfPortsPerSuperSpine = numberOfPortsPerSuperSpine
        self.numberOfSuperSpines = numberOfSuperSpines
        self.pods = []
        self.superSpineSwitches =[]
        self.mininetSuperSpineSwitches = []
        print("Creating ", self.dcnType, "-layer CLOS based DCN network with follwoing parameters", self.dcnType)
        if(self.dcnType==3):
            print(
                "numberOfSuperSpines=", self.numberOfSuperSpines, "- numberOfPortsPerSuperSpine= ",
                self.numberOfPortsPerSpine,
                " - numberOfSpinesPerPod=", self.numberOfSpinesPerPod,
                " - numberOfPortsPerSpine=", self.numberOfPortsPerSpine, " - numberOfLeavesPerSpine=",
                self.numberOfLeavesPerSpine, "numberOfPortsPerLeaf=", self.numberOfPortsPerLeaf,
                " - numberOfHostsPerLeaf=", self.numberOfHostsPerLeaf, " - numberOfLinksBetweenLeafAndSpine=",
                self.numberOfLinksBetweenLeafAndSpine)
            self.buildDCN()
            self.initiateMininet()
            self.buildONOSJson(self.jsonFileName, onosMyAppCfgJson)
        elif(self.dcnType ==2):
            print(
                "numberOfSuperSpines=", self.numberOfSuperSpines, "- numberOfPortsPerSuperSpine= ",
                self.numberOfPortsPerSpine,
                " - numberOfSpinesPerPod=", self.numberOfSpinesPerPod,
                " - numberOfPortsPerSpine=", self.numberOfPortsPerSpine, " - numberOfLeavesPerSpine=",
                self.numberOfLeavesPerSpine, "numberOfPortsPerLeaf=", self.numberOfPortsPerLeaf,
                " - numberOfHostsPerLeaf=", self.numberOfHostsPerLeaf, " - numberOfLinksBetweenLeafAndSpine=",
                self.numberOfLinksBetweenLeafAndSpine)
            self.numberOfSuperSpines =1
            self.buildDCN()
            self.initiateMininet()
            self.buildONOSJson(self.jsonFileName, onosMyAppCfgJson)



        return


    def initiateMininetOld(self):
        for i in range (0, len(self.pods)):
            self.pods[i].initiateMininetPod(self)



    def initiateMininet(self):
        # This memthod will create the real mininet network
        hostcounter = 0

        for i in range (0, len(self.pods)):
            for j in range (0, len(self.pods[i].spineSwitches)):
                print("spine switch thrift Port is ", self.pods[i].spineSwitches[j].thirftPort)
                spineSwitch = self.addSwitch(self.pods[i].spineSwitches[j].switchName, cls=ONOSBmv2Switch, pipeline_json =CC.STRATUM_SPINE_PIPELINE,
                                             cpuport=self.pods[i].spineSwitches[j].cpuPort, grpcport=self.pods[i].spineSwitches[j].grpcPort,
                                             gateway = self.pods[i].spineSwitches[j].swGateway, thriftport = self.pods[i].spineSwitches[j].thirftPort)
                self.pods[i].spineSwitches[j].addMyMininetInstance(spineSwitch)
                self.pods[i].mininetSpineSwtiches.append(spineSwitch)
                self.pods[i].mininetSpineSwtiches.append(spineSwitch)
            for j in range (0, len(self.pods[i].leafSwitches)):
                print("leaf switch thrift Port is ", self.pods[i].leafSwitches[j].thirftPort)

                leafSwitch = self.addSwitch(self.pods[i].leafSwitches[j].switchName, cls=ONOSBmv2Switch, pipeline_json =CC.STRATUM_LEAF_PIPELINE,
                                            cpuport=self.pods[i].leafSwitches[j].cpuPort, grpcport=self.pods[i].leafSwitches[j].grpcPort,
                                            gateway = self.pods[i].leafSwitches[j].swGateway, thriftport =self.pods[i].leafSwitches[j].thirftPort)
                self.pods[i].mininetLeafSwtiches.append(leafSwitch)
                self.pods[i].leafSwitches[j].addMyMininetInstance(leafSwitch)
                for k in range (0, len( self.pods[i].leafSwitches[j].hosts)):
                    print("Adding following host: ", self.pods[i].leafSwitches[j].hosts[k].name)
                    print("It's mac is :|"+self.pods[i].leafSwitches[j].hosts[k].hostMAC+"|")
                    print("It's mac is :|"+self.pods[i].leafSwitches[j].hosts[k].hostMAC+"|")
                    print("It's ip is :|"+str( self.pods[i].leafSwitches[j].hosts[k].hostIPv6) +
                          CC.FLAT_IPV6_PREFIX)
                    print("Its gateway is :"+str(self.pods[i].leafSwitches[j].swGateway +
                                                 CC.FLAT_IPV6_PREFIX))
                    h = self.addHost(self.pods[i].leafSwitches[j].hosts[k].name, cls=IPv6Host,
                                     mac=str(self.pods[i].leafSwitches[j].hosts[k].hostMAC), ipv6=str( self.pods[i].leafSwitches[j].hosts[k].hostIPv6) +
                                                                                                  CC.FLAT_IPV6_PREFIX,
                                     ipv6_gw = str(self.pods[i].leafSwitches[j].swGateway +
                                                   CC.FLAT_IPV6_PREFIX), neigh_lladdr= (self.pods[i].leafSwitches[j].hosts[k].neigh_lladdr ))
                    #self.addLink(leafSwitch,h)
                    self.pods[i].leafSwitches[j].hosts[k].addMyMininetInstance(h)
                    self.pods[i].leafSwitches[j].mininetHosts.append(h)
                    print("adding host to switch link")
                    print("node 1 "+str(self.pods[i].leafSwitches[j].getMyMininetInstance() ))
                    print("local port "+str(self.pods[i].leafSwitches[j].ports[k].getPortLocalID() ))
                    print("node 2 "+str(self.pods[i].leafSwitches[j].getMyMininetInstance()))
                    print("local port "+str(self.pods[i].leafSwitches[j].ports[k].getPortRemoteID()+1))

                    self.addLink(self.pods[i].leafSwitches[j].ports[k].getRemoteEnd().getMyMininetInstance(), self.pods[i].leafSwitches[j].getMyMininetInstance(),
                                 self.pods[i].leafSwitches[j].ports[k].getPortRemoteID(), self.pods[i].leafSwitches[j].ports[k].getPortLocalID() + 1,
                                 cls=MNLink.TCLink, bw=CC.HOST_TO_LEAF_BW)
            #this loop is for adding link between spine and leaf switch inside a pod
            print("Adding spine and leaf switch of pod "+str(i))
            for j in range (0, (len(self.pods[i].spineSwitches))):
                for k in range (0, (int(len(self.pods[i].spineSwitches[j].ports)/2))):  #Because last of the ports are already connected to superspine
                    if(self.pods[i].spineSwitches[j].ports[k].getRemoteEnd() == None):
                        print("This port is not connected. Port Details:", str(self.superSpineSwitches[i].ports[j]))
                    else:
                        print("Port info:",str(self.pods[i].spineSwitches[j].ports[k]))
                        print("src: ",self.pods[i].spineSwitches[j].getMyMininetInstance())
                        print("dest: ",self.pods[i].spineSwitches[j].ports[k].getRemoteEnd().getMyMininetInstance())
                        print("local port:",str(self.pods[i].spineSwitches[j].ports[k].getPortLocalID()+1+1))
                        print("dest port:",str((self.pods[i].spineSwitches[j].ports[k].getPortRemoteID())+1))
                        k=self.addLink(self.pods[i].spineSwitches[j].getMyMininetInstance(), self.pods[i].spineSwitches[j].ports[k].getRemoteEnd().getMyMininetInstance(),
                                           self.pods[i].spineSwitches[j].ports[k].getPortLocalID()+1, self.pods[i].spineSwitches[j].ports[k].getPortRemoteID()+1,
                                       cls=MNLink.TCLink, bw=CC.LEAF_TO_SPINE_BW) #1+1 ; first one is because already lowre layer hsas connected with you. and extra add 1 for present level 1 +
        #Building spuer spine switches
        for i in range(0, len(self.superSpineSwitches)):
            superSpineSwitch = self.addSwitch(self.superSpineSwitches[i].switchName, cls=ONOSBmv2Switch, pipeline_json =CC.STRATUM_SUPER_SPINE_PIPELINE,
                                              cpuport=self.superSpineSwitches[i].cpuPort, grpcport=self.superSpineSwitches[i].grpcPort,
                                              thriftport =self.superSpineSwitches[i].thirftPort,
                                              gateway = self.superSpineSwitches[i].swGateway)
            self.mininetSuperSpineSwitches.append(superSpineSwitch)
            self.superSpineSwitches[i].addMyMininetInstance(superSpineSwitch)

        for i in range(0, len(self.superSpineSwitches)):
            print("Adding link of superspine and spine switches:",str(self.superSpineSwitches[i]))

            for j in range (0, len(self.superSpineSwitches[i].ports)):
                if(self.superSpineSwitches[i].ports[j].getRemoteEnd() == None):
                    print("This port is not connected. Port Details:", str(self.superSpineSwitches[i].ports[j]))
                else:
                    print("Port info: ", str(self.superSpineSwitches[i].ports[j]))
                    x = self.superSpineSwitches[i].ports[j].connectedDeviceAtOtherEnd
                    print("Printing remote end info:",str(x.getMyMininetInstance()))
                    print("Port local id:",self.superSpineSwitches[i].ports[j].getPortLocalID())
                    print("Port Remote  id:", self.superSpineSwitches[i].ports[j].getPortRemoteID())

                    self.addLink(self.superSpineSwitches[i].getMyMininetInstance(), self.superSpineSwitches[i].ports[j].getRemoteEnd().getMyMininetInstance(),
                             self.superSpineSwitches[i].ports[j].getPortLocalID()+1, self.superSpineSwitches[i].ports[j].getPortRemoteID()+1,
                                 cls=MNLink.TCLink, bw=CC.SPINE_TO_SUPER_SPINE_BW)


    def findLinkDetgails(self):
        alllink= self.links(withKeys=True, withInfo=True)
        for i in range (0, len(alllink)):
            print(alllink[i])




    def buildONOSJson(self, onosRestJson, onosMyAppInternalJson):
        '''In the ONOS netcfg, the json file is a flat heirarchicy json. Where all the switches listed toghether, then ports of switches and then the hosts.
        So we will have 3 stringio buffers for these 3 types contents. While traversing the DCN tree, we will concat elements in the buffer whenever necessary
        '''
        switchBbuf = StringIO()
        portsBbuf = StringIO()
        hostBbuf = StringIO()
        nestedWhiteSpaceBuffer = StringIO()
        nestedWhiteSpaceBuffer = '     '

        switchBbuf.write('    "devices": {')
        portsBbuf.write(   '    "ports": {')
        hostBbuf.write(   '    "hosts": {')

        allswitchListForDump=[]
        allPortListForDump=[]
        allHostListForDump=[]


        for i in range(0, len(self.superSpineSwitches)):
            ssTempBuf = self.superSpineSwitches[i].buildONOSJson(nestedWhiteSpaceBuffer)
            allswitchListForDump.append(self.superSpineSwitches[i])
            switchBbuf.write( ssTempBuf.getvalue()+ ',')
            for k in range (0, len( self.superSpineSwitches[i].ports)):
                ssPortTempBuf =  self.superSpineSwitches[i].ports[k].buildONOSJson(nestedWhiteSpaceBuffer)
                allPortListForDump.append( self.superSpineSwitches[i].ports[k])
                portsBbuf.write( ssPortTempBuf.getvalue()+ ',')

        #Building Json for each pod
        for i in range (0, len(self.pods)):
            for j in range (0, len(self.pods[i].spineSwitches)):
                spTempBuf = self.pods[i].spineSwitches[j].buildONOSJson(nestedWhiteSpaceBuffer)
                allswitchListForDump.append(self.pods[i].spineSwitches[j])
                switchBbuf.write( spTempBuf.getvalue()+ ',')
                for k in range (0, len( self.pods[i].spineSwitches[j].ports)):
                    spPortTempBuf =  self.pods[i].spineSwitches[j].ports[k].buildONOSJson(nestedWhiteSpaceBuffer)
                    allPortListForDump.append(self.pods[i].spineSwitches[j].ports[k])
                    portsBbuf.write(  spPortTempBuf.getvalue()+ ',')

            for j in range (0, len(self.pods[i].leafSwitches)):
                lsTempBuf = self.pods[i].leafSwitches[j].buildONOSJson(nestedWhiteSpaceBuffer)
                allswitchListForDump.append(self.pods[i].leafSwitches[j])
                switchBbuf.write(  lsTempBuf.getvalue()+ '%s' % ('' if ((i== (len(self.pods)-1)) and (j == (len(self.pods[i].leafSwitches) - 1))) else ','))
                for k in range (0, len( self.pods[i].leafSwitches[j].ports)):
                    lsPortTempBuf =  self.pods[i].leafSwitches[j].ports[k].buildONOSJson(nestedWhiteSpaceBuffer)
                    allPortListForDump.append(self.pods[i].leafSwitches[j].ports[k])
                    portsBbuf.write( lsPortTempBuf.getvalue()+ '%s' % ('' if ( (i== (len(self.pods)-1)) and  (j == (len(self.pods[i].leafSwitches) - 1)) and
                        (k== (len( self.pods[i].leafSwitches[j].ports)-1) )) else ','))
                for k in range (0, len( self.pods[i].leafSwitches[j].hosts)):
                    lshPortTempBuf =  self.pods[i].leafSwitches[j].hosts[k].buildONOSJson(nestedWhiteSpaceBuffer)
                    allHostListForDump.append(self.pods[i].leafSwitches[j].hosts[k])
                    hostBbuf.write( lshPortTempBuf.getvalue()+ '%s' % ('' if ((i== (len(self.pods)-1)) and  (j == (len(self.pods[i].leafSwitches) - 1)) and
                    (k== ( len( self.pods[i].leafSwitches[j].hosts) -1))) else ','))
        #print>> switchBbuf, '  },'
        switchBbuf.write(  '  }')
        portsBbuf.write(  '  },')
        hostBbuf.write(  '  }')


        # with open(onosRestJson, mode='w') as f:
        #     grandBuf = StringIO()
        #     print >> grandBuf, '{'
        #     print>> grandBuf, switchBbuf.getvalue()
        #     print >> grandBuf, '}'
        #     f.write(str(grandBuf.getvalue()))
        #     grandBuf.close()
        #     f.close()
        with open(onosRestJson, mode='w+') as f1:
            grandBuf = StringIO()
            grandBuf.write(  '{')
            grandBuf.write( switchBbuf.getvalue())
            grandBuf.write(  ',')
            grandBuf.write( portsBbuf.getvalue())
            grandBuf.write( hostBbuf.getvalue())
            grandBuf.write( '}')
            f1.write(str(grandBuf.getvalue()))
            grandBuf.close()
            f1.close()
        print("Printing all link info")
        links = self.links(sort=True, withKeys=True, withInfo=True)
        # output format is ('p0s0', 'p0l0', 1, {'node1': 'p0s0', 'node2': 'p0l0', 'port2': 3, 'port1': 1})
        # so we will dump the 3 rd element. {'node1': 'p0s0', 'node2': 'p0l0', 'port2': 3, 'port1': 1}
        #this will give us the connectivity info. We will dump that in Internalnetcfg.
        allLinkInfo = []
        linkBuf = StringIO()

        for i in range (0, len(links)):
            val = {}
            val["node1"]= links[i][3]["node1"]
            val["node2"]= links[i][3]["node2"]
            val["port1"]= links[i][3]["port1"]
            val["port2"]= links[i][3]["port2"]
            val["bw"]= links[i][3]["bw"]
            allLinkInfo.append(val)

        linkBuf.write(   ',  "alllinks":  { "links": ')
        linkBuf.write(  json.dumps(allLinkInfo, skipkeys=True) )
        linkBuf.write(   '}')

        #print(jsonpickle.encode(allLinkInfo))
        with open(onosMyAppInternalJson, mode='w') as f1:
            grandBuf = StringIO()
            grandBuf.write( '{')
            grandBuf.write( switchBbuf.getvalue())
            grandBuf.write( ',')
            grandBuf.write( portsBbuf.getvalue())
            grandBuf.write( hostBbuf.getvalue())
            grandBuf.write( linkBuf.getvalue())
            grandBuf.write ( '}')
            f1.write(str(grandBuf.getvalue()))
            #print("All value in grandbuf id "+str(grandBuf.getvalue()))
            grandBuf.close()
            f1.close()
            


        # with open(onosDumpFileName, mode='w') as f:
        #     # f.write(json.dumps(allswitchListForDump., sort_keys=True))
        #     # f.write(json.dumps(allPortListForDump.__dict__, sort_keys=True))
        #     # f.write(json.dumps(allHostListForDump.__dict__, sort_keys=True))
        #     f.write(jsonpickle.encode(allswitchListForDump))
        # f.close()
        return None

    def buildDCN(self):
        # This method will create the data structure
        for i in range(0, self.numberOfSuperSpines):
            print("Building ", i, "th pod ")
            p =Pod(i, self.numberOfSpinesPerPod,
                   self.numberOfPortsPerSpine,
                   self.numberOfLeavesPerSpine,
                   self.numberOfPortsPerLeaf,
                   self.numberOfHostsPerLeaf,
                   self.numberOfLinksBetweenLeafAndSpine,
                   podIpPrefix=CC.DCN_CORE_IPv6_PREFIX+str('{:04x}'.format(int(i))+":"))
            self.pods.append(p)
        for i in range(0, self.numberOfSuperSpines):
            suSpSwitch = mySwitch(switchId= i, swtichType=CC.SWITCH_TYPE_SUPER_SPINE,
                                  switchName=(CC.SUPER_SPINE_SWITCH_NAME_PREFIX + str(i)),
                                  grpcPort=(CC.SUPER_SPINE_SWITCH_GRPC_PORT_START + i), deviceIndex=i,
                                  thirftPort=CC.SUPER_SPINE_SWITCH_THRIFT_PORT_START+i,
                                  driver=CC.DRIVER_STRATUM_BMV2,
                                  pipeconf=CC.PIPECONF_DCN_TE_SUPER_SPINE, cls=ONOSBmv2Switch,
                                  cpuPort=CC.CPU_PORT,
                                  myStationMac=(
                                      CC.SUPER_SPINE_SWITCH_MAC_PREFIX +   '{:02x}'.format(int(i))),
                                  subnetPrefix=(CC.DCN_CORE_IPv6_PREFIX  ),
                                  swGateway=(CC.DCN_CORE_IPv6_PREFIX   +":"+"ff"),
                                  numberOfPorts=self.numberOfPortsPerSuperSpine, numberOfHosts=self.numberOfHostsPerLeaf, parentPod=None, prefixLength=CC.IP_PREFIX_80)
            self.superSpineSwitches.append(suSpSwitch)
            print(suSpSwitch)
        #For each of the (n/2) spine switches in a pod, we will make 2 connections to super spines. therefor in total there will be n connection between a pod and superspine
        # so for n pods, total n * n  ports required for super spine layer.  Now there are n super spine with each n ports. therefore n^2 ports are avaialble.
        # Now, how to connect these switches.
        # Pod i's (0 <= i <= n-1)
        #   j th spine's (0 <= j <= n/2-1)
        #       k th port (k can be any of between (n/2) and n-1 )
        #           connects to
        #               i th port of superspine j and j+(n/2)
        #Example : Assume 8 port switches:
        # pod-0's , 0-th spine will be connected to 0 and (0+4) = 4 th super spine's 0 th port. through local port (8/2) 4 and (8/2)+1 =  6 th port
        #         , 1-th spine will be connected to 1 and (1+4) = 5 th super spine's 0 th port   same
        #         , 2-th spine will be connected to 2 and (2+4) = 6 th super spine's 0 th port   same
        #         , 3-th spine will be connected to 3 and (3+4) = 7 th super spine's 0 th port   same
        # pod-1's , 0-3 spine will be connected to 0 and (0+4) th super spine's 0 th port
        # same way as previous
        if(self.dcnType == 3):
            for i in range (0, len(self.pods)):
                for j in range (0, len(self.pods[i].spineSwitches)):  #extra +1 because mininet adds switch port index from 1. weird
                    if (self.numberOfPortsPerSpine<=2):
                        #If there are only two ports per switch then redundant path can not be created abetween spine and supoerspine. We will handle thi spart later
                        print("If there are only two ports per switch then redundant path can not be created between spine and supoerspine. We will handle thi spart later")
                        pass
                    else:
                        localIndex1 = int((self.numberOfPortsPerSpine/2) + 0 )  # (8/2) + 0 = 4+1
                        localIndex2 = int((self.numberOfPortsPerSpine/2) + (self.numberOfPortsPerSpine/4))  # (8/2) + (8/4) = 4+ 2 = 6 +1 #TODO this might be wrong. For 2 port switch it will break
                        self.superSpineSwitches[j].ports[i].addPortRemoteEnd(self.pods[i].spineSwitches[j],localIndex1)
                        self.pods[i].spineSwitches[j].ports[localIndex1].addPortRemoteEnd(self.superSpineSwitches[j], i)
                        self.superSpineSwitches[int(j+self.numberOfSuperSpines/2)].ports[i].addPortRemoteEnd(self.pods[i].spineSwitches[j],localIndex2)
                        self.pods[i].spineSwitches[j].ports[int(localIndex2)].addPortRemoteEnd(self.superSpineSwitches[int(j+self.numberOfSuperSpines/2)], i) #index -1 because in array they starts with 0
        print("Printing All SuperSpine Switch's connectivity")
        for i in range (0, len(self.superSpineSwitches)):
            print("Printing superspine connectivity of: ", str(self.superSpineSwitches[i]))
            for j in range (0, len(self.superSpineSwitches[i].ports)):
                print(self.superSpineSwitches[i].ports[j])

        for i in range (0, len(self.pods)):
            print("Printing connectivity of Pod:"+str(self.pods[i]))
            for j in range (0, len(self.pods[i].spineSwitches)):
                print("Connectivity of:",str(self.pods[i].spineSwitches[j]))
                for k in range (0, len(self.pods[i].spineSwitches[j].ports)):
                    print(self.pods[i].spineSwitches[j].ports[k])
            for j in range (0, len(self.pods[i].leafSwitches)):
                print("Connectivity of:",str(self.pods[i].leafSwitches[j]))
                for k in range (0, len(self.pods[i].leafSwitches[j].ports)):
                    print(self.pods[i].leafSwitches[j].ports[k])

        return






class Pod():
    def __init__(self, podId, numberOfSpinesPerPod,
                 numberOfPortsPerSpine,
                 numberOfLeavesPerSpine,
                 numberOfPortsPerLeaf,
                 numberOfHostsPerLeaf,
                 numberOfLinksBetweenLeafAndSpine,podIpPrefix):
        '''

        :param podId:
        :param numberOfSpinesPerPod:
        :param numberOfPortsPerSpine:
        :param numberOfLeavesPerSpine:
        :param numberOfPortsPerLeaf:
        :param numberOfHostsPerLeaf:
        :param numberOfLinksBetweenLeafAndSpine:
        :param podIpPrefix: This must should be a a prefix of length (128-16-16) bits. 16 foir leaf switch id, 16 for host id.
        '''
        self.podId = podId
        self.podName = CC.POD_NAME_PREFIX+"-"+str(podId)
        self.numberOfLinksBetweenLeafAndSpine = numberOfLinksBetweenLeafAndSpine
        self.numberOfHostsPerLeaf = numberOfHostsPerLeaf
        self.numberOfPortsPerLeaf = numberOfPortsPerLeaf
        self.numberOfLeavesPerSpine = numberOfLeavesPerSpine
        self.numberOfPortsPerSpine = numberOfPortsPerSpine
        self.numberOfSpinesPerPod = numberOfSpinesPerPod
        self.podIpPrefix = podIpPrefix
        self.spineSwitches = []
        self.leafSwitches = []
        self.mininetSpineSwtiches = []
        self.mininetLeafSwtiches = []
        if (self.numberOfSpinesPerPod != self.numberOfLeavesPerSpine):
            print("Cant build the pod. self.numberOfSpinesPerPod != self.numberOfLeavesPerSpine")
            exit(-1)
        if (self.numberOfSpinesPerPod != (self.numberOfPortsPerSpine/2)):  #ensuring the n and n/2 relation
            print("Cant build the pod. self.numberOfSpinesPerPod != self.numberOfPortsPerSpine")
            exit(-1)
        for i in range(0, int(self.numberOfSpinesPerPod)):
            spSwitch = mySwitch(switchId= i, swtichType=CC.SWITCH_TYPE_SPINE,
                                switchName=(CC.POD_NAME_PREFIX + str(self.podId) + CC.SPINE_SWITCH_NAME_PREFIX + str(i)),
                                grpcPort=(CC.SPINE_SWITCH_GRPC_PORT_START + int(self.podId)* self.numberOfPortsPerSpine+ i),
                                thirftPort=(CC.SPINE_SWITCH_THRIFT_PORT_START + int(self.podId)* self.numberOfPortsPerSpine+ i),deviceIndex=i,
                                driver=CC.DRIVER_STRATUM_BMV2,
                                pipeconf=CC.PIPECONF_DCN_TE_SPINE, cls=ONOSBmv2Switch,
                                cpuPort=CC.CPU_PORT,
                                myStationMac=(
                                     CC.SPINE_SWITCH_MAC_PREFIX + '{:02x}'.format(int(self.podId))  +  ":" +  '{:02x}'.format(
                                 int(i))),
                                subnetPrefix=self.podIpPrefix,
                                swGateway=(self.podIpPrefix+":"+"ff"),
                                numberOfPorts=self.numberOfPortsPerSpine, numberOfHosts=self.numberOfHostsPerLeaf, parentPod=self, prefixLength=CC.IP_PREFIX_96)
            self.spineSwitches.append(spSwitch)
            print(spSwitch)
        for i in range(0, int(self.numberOfLeavesPerSpine)):
            lSwitch = mySwitch(switchId= i, swtichType=CC.SWITCH_TYPE_LEAF,
                               switchName=(CC.POD_NAME_PREFIX + str(self.podId) + CC.LEAF_SWITCH_NAME_PREFIX + str(i)),
                               grpcPort=(CC.LEAF_SWITCH_GRPC_PORT_START + int(self.podId)* self.numberOfPortsPerSpine+ i),
                               thirftPort=(CC.LEAF_SWITCH_THRIFT_PORT_START + int(self.podId)* self.numberOfPortsPerSpine+ i),deviceIndex=i,
                               driver=CC.DRIVER_STRATUM_BMV2,
                               pipeconf=CC.PIPECONF_DCN_TE_LEAF, cls=ONOSBmv2Switch,
                               cpuPort=CC.CPU_PORT,
                               myStationMac=(
                                         CC.LEAF_SWITCH_MAC_PREFIX + '{:02x}'.format(int(self.podId))  +  ":" +  '{:02x}'.format(
                                     int(i))),
                               subnetPrefix=(self.podIpPrefix+'{:04x}'.format(int(i))),
                               swGateway=(self.podIpPrefix+'{:04x}'.format(int(i)) +":"+"ff"),
                               numberOfPorts=self.numberOfPortsPerLeaf, numberOfHosts=self.numberOfHostsPerLeaf, parentPod=self, prefixLength=CC.IP_PREFIX_112)
            self.leafSwitches.append(lSwitch)
            print(lSwitch)
        #all leaf's port (n/2)+1 to n are resereved for connecting with spine switches.
        #Assume Leaf switch id -i (0 <= i <= (n/2)) is going to be connected with spine j (0 <= i <= (n/2)) , Then the ports will be
        # leaf i's port - (n/2+ i)  will be connected to j'th spine switches i-th port
        # first leaf switch, which is l0, this will be connected to all the spine switches, 0 th port.
        #update: switch port starts from 1. so updated accordingly
        for i in range (0, len(self.leafSwitches)):
            for j in range (0, len(self.spineSwitches)):
                self.leafSwitches[i].ports[int(self.leafSwitches[i].numberOfPorts/2+j)].addPortRemoteEnd(self.spineSwitches[j],i)
                self.spineSwitches[j].ports[i].addPortRemoteEnd(self.leafSwitches[i],int(self.leafSwitches[i].numberOfPorts/2+j))


        pass

    def __str__(self):
        val= ""+self.podName
        return val

    def getName(self):
        return self.podName



# ========================================================================================
class mySwitch:

    def __init__(self,switchId,  swtichType, switchName, grpcPort,thirftPort, deviceIndex, driver, pipeconf, cls,
                 cpuPort=CC.CPU_PORT,
                 myStationMac=None, subnetPrefix=None, swGateway=None,
                 numberOfPorts=2, numberOfHosts=2, parentPod=None, prefixLength=CC.IP_PREFIX_80,**params):
        '''

        :param switchId:
        :param swtichType:
        :param switchName:
        :param grpcPort:
        :param thirftPort:
        :param deviceIndex:
        :param driver:
        :param pipeconf:
        :param cls:
        :param cpuPort:
        :param myStationMac:
        :param subnetPrefix: This must should be a prefix of length 112 bit. 97-112 th bits must should identify the leaf index. and rest of the last 16 bits are kept for host indexing
        :param swGateway:
        :param numberOfPorts:
        :param numberOfHosts:
        :param parentPod:
        :param params:
        '''

        self.swGateway = swGateway
        self.numberOfPorts = numberOfPorts
        self.numberOfHosts = numberOfHosts
        self.switchId = switchId
        self.deviceIndex = deviceIndex
        self.swtichType = swtichType
        self.ports = []
        self.hosts = []
        self.switchName = switchName
        self.grpcPort = grpcPort
        self.thirftPort =thirftPort
        self.driver = driver
        self.pipeconf = pipeconf
        self.cls = cls
        self.cpuPort = cpuPort
        self.myStationMac = myStationMac
        self.parentPod = parentPod
        self.prefixLength = prefixLength;
        self.mininetHosts = []
        self.myMininetInstance = None # this is the object returned by mininet addSwitch method. We will keep track of this because it helps adding link


        if ((self.swtichType == CC.SWITCH_TYPE_LEAF) and (subnetPrefix == None)):
            print(
                "Lead switch without subnet prefix can not be build. Because wll the hosts hets ip based on this . And in our scheme it is the base of all IP address allocation")
            exit(-1)
        if ((self.swtichType == CC.SWITCH_TYPE_LEAF) or (self.swtichType == CC.SWITCH_TYPE_SPINE) ):
            if(self.parentPod == None):
                print("Trying to create switch-",self.switchName+" with out parentpod. Without parentPod such switch has no existence. Exiting!!!!");
                exit(1)
        if (self.numberOfHosts> (self.numberOfPorts/2)):
            print("numberOfHosts is :"+str(self.numberOfPorts)+" and self.numberOfPorts/2 is:"+ str(self.numberOfPorts/2)+". Can't comfigure switch:"+self.switchName)
            exit(-1)

        self.subnetPrefix = subnetPrefix
        self.numberOfPorts = numberOfPorts
        self.numberOfHosts = numberOfHosts
        self.middlePortIndex = self.numberOfPorts / 2
        for i in range(0, self.numberOfPorts):
            p = Port(i, (self.switchName + CC.PORT_NAME_PREFIX + str(i)), self)
            self.ports.append(p)
        counter = 0
        if(self.swtichType!=CC.SWITCH_TYPE_LEAF):
            print("Non leaf Switches are not required to configure hosts. So Returning...")
            return
        #=============these part is onle leaf switch specific===============
        if(self.numberOfHosts> (self.numberOfPorts/2)):
            print("A leaf switch can not contain more than half of it's total port count. Exiting")
            exit(-1)
        for i in range (0, int(self.numberOfHosts)):
            counter = counter + 1
            #Here we are assuming that, for each host with index j (1<= j <= portCount/2) inside a leaf,, jth host will be connected to the leaf switches (j) th port
            # and its self port will be always 0. because we are configuring only one ip per host
            # newHost = MyHost(hostID=(i+1),
            #                  hostName=(CC.HOST_NAME_PREFIX + str(i+1)+self.switchName  ),
            #                  hostMAC= (
            #                        CC.HOST_MAC_PREFIX + '{:02x}'.format(int(self.parentPod.podId))  +  ":" +  '{:02x}'.format(
            #                    int(self.switchId))+":"+ '{:02x}'.format(int(i+1))),
            #                  hostIPv6=(self.subnetPrefix)+ '{:04x}'.format(int(i+1)), parentSwitch=self,
            #                  parentSwitchPortIndex = (i+1), neigh_lladdr=self.myStationMac)
            newHost = MyHost(hostID=(i),
                          hostName=(CC.HOST_NAME_PREFIX + str(i)+self.switchName  ),
                          hostMAC= (
                                CC.HOST_MAC_PREFIX + '{:02x}'.format(int(self.parentPod.podId))  +  ":" +  '{:02x}'.format(
                            int(self.switchId))+":"+ '{:02x}'.format(int(i))),
                          hostIPv6=(self.subnetPrefix)+ ":"+'{:04x}'.format(int(i)), parentSwitch=self,
                          parentSwitchPortIndex = (i),ipv6_gw=self.myStationMac, neigh_lladdr = self.myStationMac )
            self.ports[i].addPortRemoteEnd( newHost, 0) # For these indexing look at comment after the start of for loop
            self.ports[i].addPortRemoteEnd( newHost, 0) # For these indexing look at comment after the start of for loop
            self.hosts.append(newHost)
            print(newHost)

        return None

    def getSwitchTypeAsName(self):
        if(self.swtichType==None):
            print("A switch without its type can not be built at this moment. So exiting!!!")
            exit(-1)
        if(self.swtichType==CC.SWITCH_TYPE_SUPER_SPINE):
            return CC.SWITCH_TYPE_SUPER_SPINE_AS_NAME
        elif(self.swtichType==CC.SWITCH_TYPE_SPINE):
            return CC.SWITCH_TYPE_SPINE_AS_NAME
        elif(self.swtichType==CC.SWITCH_TYPE_LEAF):
            return CC.SWITCH_TYPE_LEAF_AS_NAME

    def __str__(self):
        val= ""
        val= val + self.switchName + ": subnetprefix :"+self.subnetPrefix
        val= val + ", stationMac:"+str(self.myStationMac)
        val = val+ ", gateway:"+str(self.swGateway)
        return val

    def getName(self):
        return self.switchName

    def buildONOSJson(self, whspForJsonIndention=""):
        """"device:leaf1": {
              "basic": {
                "managementAddress": "grpc://mininet:50001?device_id=1",
                "driver": "stratum-bmv2",
                "pipeconf": "org.onosproject.ngsdn-tutorial"
              },
              "fabricDeviceConfig": {
                "myStationMac": "00:aa:00:00:00:01",
                "isSpine": false
              }
            },"""
        buf = StringIO()
        buf.write( whspForJsonIndention+'   "device:%s": {' % (self.switchName) )
        buf.write( whspForJsonIndention+'      "basic": {')
        # ONOS expects device id is 1. So we are setting device id 1.
        buf.write (whspForJsonIndention+ '          "managementAddress": "grpc://127.0.0.1:%d?device_id=%d",' % (self.grpcPort, 1))
        buf.write ( whspForJsonIndention+ '          "driver": "%s",' % (str(self.driver)))
        buf.write ( whspForJsonIndention+ '          "pipeconf": "%s",' % (str(self.pipeconf)))
        buf.write (  whspForJsonIndention+ '          "thirftPort": "%s"' % ((self.thirftPort)))
        buf.write (  whspForJsonIndention+ '       },')
        buf.write (  whspForJsonIndention+ '       "fabricDeviceConfig": {')
        buf.write (  whspForJsonIndention+ '           "myStationMac": "%s",' % (self.myStationMac))
        buf.write (  whspForJsonIndention+ '           "switchType": "%s",' % (self.getSwitchTypeAsName()))
        buf.write (  whspForJsonIndention+ '           "switchHostSubnetPrefix": "%s:00%s"' % (self.subnetPrefix, self.prefixLength))
        buf.write (  whspForJsonIndention+ '          }')
        buf.write ( whspForJsonIndention+ '     }')
        return buf

    def addMyMininetInstance(self, myMininetInstance):
        self.myMininetInstance = myMininetInstance
        return self.myMininetInstance

    def getMyMininetInstance(self):
        return self.myMininetInstance



class Port:
    def __init__(self, portId, portName, parentSwitch):
        self.portName = portName
        self.portId = portId
        self.parentSwitch = parentSwitch
        self.connectedDeviceAtOtherEnd = None  # This can be of type switch or host. when you use that, you have to do type checking
        self.portNumInOtherEndDevice = None  # the port number on the other end's device
        return None
    def addPortRemoteEnd(self, connectedDeviceAtOtherEnd, portNumInOtherEndDevice):
        if(self.connectedDeviceAtOtherEnd != None):
            print(self.portName + " is already connected to "+self.connectedDeviceAtOtherEnd.getName())
            return False
        self.connectedDeviceAtOtherEnd = connectedDeviceAtOtherEnd
        self.portNumInOtherEndDevice = portNumInOtherEndDevice
        return True

    def getPortLocalID(self):
        return self.portId

    def getPortRemoteID(self):
        return self.portNumInOtherEndDevice

    def getRemoteEnd(self):
        if(self.connectedDeviceAtOtherEnd ==None):
            return None
        else:
            return self.connectedDeviceAtOtherEnd

    def __str__(self):
        val= ""
        val= val+"Port name is : "+ self.portName+"\n"
        if(self.connectedDeviceAtOtherEnd ==None):
            val = val+ " Port is not connected to any device"
        else:
            val= val+"Port :"+ str(self.portId) + " of Switch : "+ self.parentSwitch.switchName + "\n"
            val=val+ "connected to "+str(self.portNumInOtherEndDevice)+"'th port of "+ str(self.connectedDeviceAtOtherEnd.getName())
        return val

    def getName(self):
        return self.parentSwitch.getName()+-"port:"+self.portName
    def buildONOSJson(self, whspForJsonIndention=""):
        """"device:leaf1/3": {
        "interfaces": [
            {
                "name": "leaf1-3",
                "ips": ["2001:1:1::ff/64"]
            }
        ]
        }"""
        buf = StringIO()
        buf.write( whspForJsonIndention+'"device:%s/%d": {' % (self.parentSwitch.switchName, self.portId+1))
        buf.write(  whspForJsonIndention+ '  "interfaces":  [')
        buf.write(  whspForJsonIndention+ '    {')
        buf.write(  whspForJsonIndention+ '       "name": "%s-%d",' % (self.parentSwitch.switchName, self.portId+1))
        buf.write(  whspForJsonIndention+ '       "ips": ["%s%s"]' % (self.parentSwitch.swGateway, CC.FLAT_IPV6_PREFIX))
        buf.write(  whspForJsonIndention+ '    }')
        buf.write(  whspForJsonIndention+ '  ]')
        buf.write(  whspForJsonIndention+ '}')
        return buf

class MyHost:
    def __init__(self, hostID, hostName, hostMAC, hostIPv6, parentSwitch,parentSwitchPortIndex,ipv6_gw, neigh_lladdr):
        self.hostID = hostID
        self.name = hostName
        self.hostMAC = hostMAC
        self.hostIPv6 = hostIPv6
        self.parentSwitch = parentSwitch
        self.parentSwitchPortIndex = parentSwitchPortIndex
        self.port = Port(0,"eth0",parentSwitch)
        self.port.addPortRemoteEnd(parentSwitch,parentSwitchPortIndex)
        self.myMininetInstance = None # this is the object returned by mininet addSwitch method. We will keep track of this because it helps adding link
        self.ipv6_gw=ipv6_gw
        self.neigh_lladdr = neigh_lladdr
        return None

    def addMyMininetInstance(self,myMininetInstance):
        self.myMininetInstance = myMininetInstance
        return self.myMininetInstance

    def getMyMininetInstance(self):
        return self.myMininetInstance

    def __str__(self):
        val= ""
        val= val+"Host:-- name: "+ self.name
        val= val+", MAC:"+ self.hostMAC
        val= val+",IPv6: "+ self.hostIPv6
        val=val+ "connected to "+str(self.parentSwitch.getName())
        val= val+ ", local port: "+str(self.port.portId)
        val= val + ", Remote port: "+str(self.port.portNumInOtherEndDevice)
        val = val+ "Parent switch port index is :"+str(self.parentSwitchPortIndex)+"\n"
        return val
    def getName(self):
        return self.name
    def buildONOSJson(self, whspForJsonIndention=""):
        """"00:00:00:00:00:1A/None": {
            "basic": {
                "name": "h1a"
            }"ips": ["10.6.1.1"]
        },"""
        buf = StringIO()
        buf.write(whspForJsonIndention+ '"%s/None": {' % (self.hostMAC))
        buf.write(whspForJsonIndention+ '  "basic": {')
        buf.write(whspForJsonIndention+ '       "name": "%s",' % (self.name))
        buf.write(whspForJsonIndention+ '       "ips": ["%s"]' % (self.hostIPv6))
        buf.write(whspForJsonIndention+ '   },')
        buf.write(whspForJsonIndention+ '  "fabricHostConfig": {')
        buf.write(whspForJsonIndention+ '       "mac": "%s",' % (self.hostMAC))
        buf.write(whspForJsonIndention+ '       "location": "%s/%s"' % (self.parentSwitch.switchName, (self.port.getPortRemoteID()+1))) #We are adding one because the 0th port in mininet is
        #1 th port in stratum_bmv2 #TODO explore the reason and generalized work around later
        buf.write(whspForJsonIndention+ '   }')
        buf.write(whspForJsonIndention+ '}')
        return buf




def main():
    # net = Mininet(topo=TutorialTopo(), controller=None)
    # numberOfSpines,numberOfInterfacesPerSpine, numberOfLeaves, numberOfInterfacesPerLeaf, numberOfHostsPerLeaf, numberOfLinkesBetwenLeafAndSpine, *args, **kwargs
    # leafSpineDCN = LeafSpineDCN(1,1,1,4,2,1)
    # leafSpineDCN = LeafSpineDCN(8, 8, 8, 8, 4, 4)
    #leafSpineDCN = LeafSpineDCN(4, 4, 4, 4, 2, 2)
    dcn = ClosDCN()
    net = Mininet(topo=dcn, controller=None)

    print("Starting mininet")
    net.start()
    print("Started mininet")
    CLI(net)
    # print("Printing all link info")
    # alllinks = net.links(withKeys=True, withInfo=True)
    # for l in alllinks:
    #     print(l)

    net.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Mininet topology script for a pod based (clos topology) data center network')
    args = parser.parse_args()
    print (args)
    setLogLevel('info')
    main()











#
#
#
#
#
# def initiateMininetOvaiKhaliFail(self):
#     # This memthod will create the real mininet network
#     #This version tries to create link without port number
#     hostcounter = 0
#     for i in range(0, len(self.superSpineSwitches)):
#         superSpineSwitch = self.addSwitch(self.superSpineSwitches[i].switchName, cls=StratumBmv2Switch, pipeline_json =CC.STRATUM_SUPER_SPINE_PIPELINE,
#                                           cpuport=self.superSpineSwitches[i].cpuPort, grpcPort=self.superSpineSwitches[i].grpcPort, gateway = self.superSpineSwitches[i].swGateway)
#         self.mininetSuperSpineSwitches.append(superSpineSwitch)
#         self.superSpineSwitches[i].addMyMininetInstance(superSpineSwitch)
#     for i in range (0, len(self.pods)):
#         for j in range (0, len(self.pods[i].spineSwitches)):
#             spineSwitch = self.addSwitch(self.pods[i].spineSwitches[j].switchName, cls=StratumBmv2Switch, pipeline_json =CC.STRATUM_SPINE_PIPELINE,
#                                          cpuport=self.pods[i].spineSwitches[j].cpuPort, grpcPort=self.pods[i].spineSwitches[j].grpcPort,
#                                          gateway = self.pods[i].spineSwitches[j].swGateway)
#             self.pods[i].spineSwitches[j].addMyMininetInstance(spineSwitch)
#             self.pods[i].mininetSpineSwtiches.append(spineSwitch)
#
#     for i in range(0, len(self.superSpineSwitches)):
#         print("Adding link of superspine and spine switches:",str(self.superSpineSwitches[i]))
#
#         for j in range (0, len(self.superSpineSwitches[i].ports)):
#             if(self.superSpineSwitches[i].ports[j].getRemoteEnd() == None):
#                 print("This port is not connected. Port Details:", str(self.superSpineSwitches[i].ports[j]))
#             else:
#                 print("Port info: ", str(self.superSpineSwitches[i].ports[j]))
#                 x = self.superSpineSwitches[i].ports[j].connectedDeviceAtOtherEnd
#                 print("Printing remote end info:",str(x.getMyMininetInstance()))
#                 print("Port local id:",self.superSpineSwitches[i].ports[j].getPortLocalID())
#                 print("Port Remote  id:", self.superSpineSwitches[i].ports[j].getPortRemoteID())
#                 self.addLink(self.superSpineSwitches[i].getMyMininetInstance(), self.superSpineSwitches[i].ports[j].getRemoteEnd().getMyMininetInstance())
#
#     #For each pod
#     for i in range (0, len(self.pods)):
#         for j in range (0, len(self.pods[i].leafSwitches)):
#             leafSwitch = self.addSwitch(self.pods[i].leafSwitches[j].switchName, cls=StratumBmv2Switch, pipeline_json =CC.STRATUM_LEAF_PIPELINE,
#                                         cpuport=self.pods[i].leafSwitches[j].cpuPort, grpcPort=self.pods[i].leafSwitches[j].grpcPort,
#                                         gateway = self.pods[i].leafSwitches[j].swGateway)
#             self.pods[i].mininetLeafSwtiches.append(leafSwitch)
#             self.pods[i].leafSwitches[j].addMyMininetInstance(leafSwitch)
#         #leaf switch to spine switch connectivity
#         for i in range (0, len(self.pods)):
#             print("Adding leaf switch to spine switch link of pod:",self.pods[i].podName)
#             for j in range (0, (len(self.pods[i].spineSwitches))):
#                 for k in range (0, (len(self.pods[i].spineSwitches[j].ports)/2)-1):  #Because last of the ports are already connected to superspine
#                     if(self.pods[i].spineSwitches[j].ports[k].getRemoteEnd() == None):
#                         print("This port is not connected. Port Details:", str(self.superSpineSwitches[i].ports[j]))
#                     else:
#                         print("Port info:",str(self.pods[i].spineSwitches[j].ports[k]))
#                         self.addLink(self.pods[i].spineSwitches[j].getMyMininetInstance(), self.pods[i].spineSwitches[j].ports[k].getRemoteEnd().getMyMininetInstance())
#
#         print("Adding host link:",str(self.pods[i].leafSwitches[j].ports[k]))
#         for j in range (0, len(self.pods[i].leafSwitches)):
#             for k in range (0, len( self.pods[i].leafSwitches[j].hosts)):
#                 print("Adding following host: ", str(self.pods[i].leafSwitches[j].hosts[k]))
#                 print("It's mac is :|"+self.pods[i].leafSwitches[j].hosts[k].hostMAC+"|")
#                 h = self.addHost(self.pods[i].leafSwitches[j].hosts[k].name, cls=mystratum.NoOffloadHost,
#                                  mac=str(self.pods[i].leafSwitches[j].hosts[k].hostMAC), ipv6=str( self.pods[i].leafSwitches[j].hosts[k].hostIPv6) +
#                                                                                               CC.FLAT_IPV6_PREFIX,
#                                  ipv6_gw = str(self.pods[i].leafSwitches[j].swGateway +
#                                                CC.FLAT_IPV6_PREFIX))
#                 # hostcounter = hostcounter+1
#                 # h = self.addHost("h"+str(hostcounter), cls=IPv6Host)
#                 self.pods[i].leafSwitches[j].hosts[k].addMyMininetInstance(h)
#                 self.pods[i].leafSwitches[j].mininetHosts.append(h)
#
#         print("Adding host link:",str(self.pods[i].leafSwitches[j].ports[k]))
#         for j in range (0, ((len(self.pods[i].leafSwitches)))):  #Because last of the ports are already connected to spine
#             print("Leaf switch port arrrry length: ",(len(self.pods[i].leafSwitches[j].ports)))
#             for k in range (0, (len(self.pods[i].leafSwitches[j].ports)/2)-1):
#                 print("port k is ",str(self.pods[i].leafSwitches[j].ports[k]))
#                 if(self.pods[i].leafSwitches[j].ports[k].getRemoteEnd() == None):
#                     print("This port is not connected. Port Details:", str(self.superSpineSwitches[i].ports[j]))
#                 else:
#                     print("Node 1 = ",str(self.pods[i].leafSwitches[j].getMyMininetInstance()))
#                     print("Node 2 = ",str(self.pods[i].leafSwitches[j].ports[k].getRemoteEnd().getMyMininetInstance()))
#                     print("local port: " , self.pods[i].leafSwitches[j].ports[k].getPortLocalID())
#                     print("remote port: " , self.pods[i].leafSwitches[j].ports[k].getPortRemoteID())
#                     self.addLink(self.pods[i].leafSwitches[j].getMyMininetInstance(), self.pods[i].leafSwitches[j].ports[k].getRemoteEnd().getMyMininetInstance())
#
#
# def initiateMininetFailtothe powern(self):
#     # This memthod will create the real mininet network
#     hostcounter = 0
#     for i in range(0, len(self.superSpineSwitches)):
#         superSpineSwitch = self.addSwitch(self.superSpineSwitches[i].switchName, cls=StratumBmv2Switch, pipeline_json =CC.STRATUM_SUPER_SPINE_PIPELINE,
#                                           cpuport=self.superSpineSwitches[i].cpuPort, grpcPort=self.superSpineSwitches[i].grpcPort, gateway = self.superSpineSwitches[i].swGateway)
#         self.mininetSuperSpineSwitches.append(superSpineSwitch)
#         self.superSpineSwitches[i].addMyMininetInstance(superSpineSwitch)
#     for i in range (0, len(self.pods)):
#         for j in range (0, len(self.pods[i].spineSwitches)):
#             spineSwitch = self.addSwitch(self.pods[i].spineSwitches[j].switchName, cls=StratumBmv2Switch, pipeline_json =CC.STRATUM_SPINE_PIPELINE,
#                                          cpuport=self.pods[i].spineSwitches[j].cpuPort, grpcPort=self.pods[i].spineSwitches[j].grpcPort,
#                                          gateway = self.pods[i].spineSwitches[j].swGateway)
#             self.pods[i].spineSwitches[j].addMyMininetInstance(spineSwitch)
#             self.pods[i].mininetSpineSwtiches.append(spineSwitch)
#         for j in range (0, len(self.pods[i].leafSwitches)):
#             leafSwitch = self.addSwitch(self.pods[i].leafSwitches[j].switchName, cls=StratumBmv2Switch, pipeline_json =CC.STRATUM_LEAF_PIPELINE,
#                                         cpuport=self.pods[i].leafSwitches[j].cpuPort, grpcPort=self.pods[i].leafSwitches[j].grpcPort,
#                                         gateway = self.pods[i].leafSwitches[j].swGateway)
#             self.pods[i].mininetLeafSwtiches.append(leafSwitch)
#             self.pods[i].leafSwitches[j].addMyMininetInstance(leafSwitch)
#             for k in range (0, len( self.pods[i].leafSwitches[j].hosts)):
#                 print("Adding following host: ", str(self.pods[i].leafSwitches[j].hosts[k]))
#                 print("It's mac is :|"+self.pods[i].leafSwitches[j].hosts[k].hostMAC+"|")
#                 h = self.addHost(self.pods[i].leafSwitches[j].hosts[k].name, cls=Host,
#                                  mac=str(self.pods[i].leafSwitches[j].hosts[k].hostMAC), ipv6=str( self.pods[i].leafSwitches[j].hosts[k].hostIPv6) +
#                                                                                               CC.FLAT_IPV6_PREFIX,
#                                  ipv6_gw = str(self.pods[i].leafSwitches[j].swGateway +
#                                                CC.FLAT_IPV6_PREFIX))
#                 # hostcounter = hostcounter+1
#                 # h = self.addHost("h"+str(hostcounter), cls=IPv6Host)
#                 self.pods[i].leafSwitches[j].hosts[k].addMyMininetInstance(h)
#                 self.pods[i].leafSwitches[j].mininetHosts.append(h)
#
#
#     print("Adding link of superspine and pod:")
#     for i in range(0, len(self.superSpineSwitches)):
#         print("Adding link of superspine:",str(self.superSpineSwitches[i]))
#
#         for j in range (0, len(self.superSpineSwitches[i].ports)):
#             if(self.superSpineSwitches[i].ports[j].getRemoteEnd() == None):
#                 print("This port is not connected. Port Details:", str(self.superSpineSwitches[i].ports[j]))
#             else:
#                 print("Port info: ", str(self.superSpineSwitches[i].ports[j]))
#                 x = self.superSpineSwitches[i].ports[j].connectedDeviceAtOtherEnd
#                 print("Printing remote end info:",str(x.getMyMininetInstance()))
#                 print("Port local id:",self.superSpineSwitches[i].ports[j].getPortLocalID())
#                 print("Port Remote  id:", self.superSpineSwitches[i].ports[j].getPortRemoteID())
#                 self.addLink(self.superSpineSwitches[i].getMyMininetInstance(), self.superSpineSwitches[i].ports[j].getRemoteEnd().getMyMininetInstance(),
#                              self.superSpineSwitches[i].ports[j].getPortLocalID(), self.superSpineSwitches[i].ports[j].getPortRemoteID() )
#     for i in range (0, len(self.pods)):
#         print("Adding link of pod:",self.pods[i].podName)
#         for j in range (0, (len(self.pods[i].spineSwitches))):
#             for k in range (0, (len(self.pods[i].spineSwitches[j].ports)/2)-1):  #Because last of the ports are already connected to superspine
#                 if(self.pods[i].spineSwitches[j].ports[k].getRemoteEnd() == None):
#                     print("This port is not connected. Port Details:", str(self.superSpineSwitches[i].ports[j]))
#                 else:
#                     print("Port info:",str(self.pods[i].spineSwitches[j].ports[k]))
#                     self.addLink(self.pods[i].spineSwitches[j].getMyMininetInstance(), self.pods[i].spineSwitches[j].ports[k].getRemoteEnd().getMyMininetInstance(),
#                                  self.pods[i].spineSwitches[j].ports[k].getPortLocalID(), self.pods[i].spineSwitches[j].ports[k].getPortRemoteID() )
#     print("Adding host link:",str(self.pods[i].leafSwitches[j].ports[k]))
#     for j in range (0, ((len(self.pods[i].leafSwitches)))):  #Because last of the ports are already connected to spine
#         for k in range (0, (len(self.pods[i].leafSwitches[j].ports)/2)-1):
#             if(self.pods[i].leafSwitches[j].ports[k].getRemoteEnd() == None):
#                 print("This port is not connected. Port Details:", str(self.superSpineSwitches[i].ports[j]))
#             else:
#                 print("Node 1 = ",str(self.pods[i].leafSwitches[j].getMyMininetInstance()))
#                 print("Node 2 = ",str(self.pods[i].leafSwitches[j].ports[k].getRemoteEnd().getMyMininetInstance()))
#                 print("local port: " , self.pods[i].leafSwitches[j].ports[k].getPortLocalID())
#                 print("remote port: " , self.pods[i].leafSwitches[j].ports[k].getPortRemoteID())
#                 self.addLink(self.pods[i].leafSwitches[j].getMyMininetInstance(), self.pods[i].leafSwitches[j].ports[k].getRemoteEnd().getMyMininetInstance(),
#                              self.pods[i].leafSwitches[j].ports[k].getPortLocalID(), self.pods[i].leafSwitches[j].ports[k].getPortRemoteID() )


#
# def initiateMininetSuperFail(self):
#     # This memthod will create the real mininet network
#     hostcounter = 0
#     for i in range(0, len(self.superSpineSwitches)):
#         superSpineSwitch = self.addSwitch(self.superSpineSwitches[i].switchName, cls=StratumBmv2Switch, pipeline_json =CC.STRATUM_SUPER_SPINE_PIPELINE,
#                                           cpuport=self.superSpineSwitches[i].cpuPort, grpcPort=self.superSpineSwitches[i].grpcPort, gateway = self.superSpineSwitches[i].swGateway)
#         self.mininetSuperSpineSwitches.append(superSpineSwitch)
#         self.superSpineSwitches[i].addMyMininetInstance(superSpineSwitch)
#     for i in range (0, len(self.pods)):
#         for j in range (0, len(self.pods[i].spineSwitches)):
#             spineSwitch = self.addSwitch(self.pods[i].spineSwitches[j].switchName, cls=StratumBmv2Switch, pipeline_json =CC.STRATUM_SPINE_PIPELINE,
#                                          cpuport=self.pods[i].spineSwitches[j].cpuPort, grpcPort=self.pods[i].spineSwitches[j].grpcPort,
#                                          gateway = self.pods[i].spineSwitches[j].swGateway)
#             self.pods[i].spineSwitches[j].addMyMininetInstance(spineSwitch)
#             self.pods[i].mininetSpineSwtiches.append(spineSwitch)
#
#     for i in range(0, len(self.superSpineSwitches)):
#         print("Adding link of superspine and spine switches:",str(self.superSpineSwitches[i]))
#
#         for j in range (0, len(self.superSpineSwitches[i].ports)):
#             if(self.superSpineSwitches[i].ports[j].getRemoteEnd() == None):
#                 print("This port is not connected. Port Details:", str(self.superSpineSwitches[i].ports[j]))
#             else:
#                 print("Port info: ", str(self.superSpineSwitches[i].ports[j]))
#                 x = self.superSpineSwitches[i].ports[j].connectedDeviceAtOtherEnd
#                 print("Printing remote end info:",str(x.getMyMininetInstance()))
#                 print("Port local id:",self.superSpineSwitches[i].ports[j].getPortLocalID())
#                 print("Port Remote  id:", self.superSpineSwitches[i].ports[j].getPortRemoteID())
#                 self.addLink(self.superSpineSwitches[i].getMyMininetInstance(), self.superSpineSwitches[i].ports[j].getRemoteEnd().getMyMininetInstance(),
#                              self.superSpineSwitches[i].ports[j].getPortLocalID(), self.superSpineSwitches[i].ports[j].getPortRemoteID() )
#
#     #For each pod
#     for i in range (0, len(self.pods)):
#         for j in range (0, len(self.pods[i].leafSwitches)):
#             leafSwitch = self.addSwitch(self.pods[i].leafSwitches[j].switchName, cls=StratumBmv2Switch, pipeline_json =CC.STRATUM_LEAF_PIPELINE,
#                                         cpuport=self.pods[i].leafSwitches[j].cpuPort, grpcPort=self.pods[i].leafSwitches[j].grpcPort,
#                                         gateway = self.pods[i].leafSwitches[j].swGateway)
#             self.pods[i].mininetLeafSwtiches.append(leafSwitch)
#             self.pods[i].leafSwitches[j].addMyMininetInstance(leafSwitch)
#         #leaf switch to spine switch connectivity
#         for i in range (0, len(self.pods)):
#             print("Adding leaf switch to spine switch link of pod:",self.pods[i].podName)
#             for j in range (0, (len(self.pods[i].spineSwitches))):
#                 for k in range (0, (len(self.pods[i].spineSwitches[j].ports)/2)-1):  #Because last of the ports are already connected to superspine
#                     if(self.pods[i].spineSwitches[j].ports[k].getRemoteEnd() == None):
#                         print("This port is not connected. Port Details:", str(self.superSpineSwitches[i].ports[j]))
#                     else:
#                         print("Port info:",str(self.pods[i].spineSwitches[j].ports[k]))
#                         self.addLink(self.pods[i].spineSwitches[j].getMyMininetInstance(), self.pods[i].spineSwitches[j].ports[k].getRemoteEnd().getMyMininetInstance(),
#                                      self.pods[i].spineSwitches[j].ports[k].getPortLocalID(), self.pods[i].spineSwitches[j].ports[k].getPortRemoteID() )
#
#         print("Adding host link:",str(self.pods[i].leafSwitches[j].ports[k]))
#         for j in range (0, len(self.pods[i].leafSwitches)):
#             for k in range (0, len( self.pods[i].leafSwitches[j].hosts)):
#                 print("Adding following host: ", str(self.pods[i].leafSwitches[j].hosts[k]))
#                 print("It's mac is :|"+self.pods[i].leafSwitches[j].hosts[k].hostMAC+"|")
#                 # h = self.addHost(self.pods[i].leafSwitches[j].hosts[k].name, cls=mystratum.NoOffloadHost,
#                 #                  mac=str(self.pods[i].leafSwitches[j].hosts[k].hostMAC), ipv6=str( self.pods[i].leafSwitches[j].hosts[k].hostIPv6) +
#                 #                                                                               CC.FLAT_IPV6_PREFIX,
#                 #                  ipv6_gw = str(self.pods[i].leafSwitches[j].swGateway +
#                 #                                CC.FLAT_IPV6_PREFIX))
#                 # # hostcounter = hostcounter+1
#                 # # h = self.addHost("h"+str(hostcounter), cls=IPv6Host)
#                 # self.pods[i].leafSwitches[j].hosts[k].addMyMininetInstance(h)
#                 # self.pods[i].leafSwitches[j].mininetHosts.append(h)
#
#         print("Adding host link:",str(self.pods[i].leafSwitches[j].ports[k]))
#         for j in range (0, ((len(self.pods[i].leafSwitches)))):  #Because last of the ports are already connected to spine
#             print("Leaf switch port arrrry length: ",(len(self.pods[i].leafSwitches[j].ports)))
#             for k in range (0, (len(self.pods[i].leafSwitches[j].ports)/2)-1):
#                 print("port k is ",str(self.pods[i].leafSwitches[j].ports[k]))
#                 if(self.pods[i].leafSwitches[j].ports[k].getRemoteEnd() == None):
#                     print("This port is not connected. Port Details:", str(self.superSpineSwitches[i].ports[j]))
#                 else:
#                     print("Node 1 = ",str(self.pods[i].leafSwitches[j].getMyMininetInstance()))
#                     print("Node 2 = ",str(self.pods[i].leafSwitches[j].ports[k].getRemoteEnd().getMyMininetInstance()))
#                     print("local port: " , self.pods[i].leafSwitches[j].ports[k].getPortLocalID())
#                     print("remote port: " , self.pods[i].leafSwitches[j].ports[k].getPortRemoteID())
#                     self.addLink(self.pods[i].leafSwitches[j].getMyMininetInstance(), self.pods[i].leafSwitches[j].ports[k].getRemoteEnd().getMyMininetInstance(),
#                                  self.pods[i].leafSwitches[j].ports[k].getPortLocalID(), self.pods[i].leafSwitches[j].ports[k].getPortRemoteID() )



# def initiateMininetPod(self, topo):
#     for i in range (0, len(self.leafSwitches)):
#         leafSwitch = topo.addSwitch(self.leafSwitches[i].switchName, cls=ONOSBmv2Switch, pipeline_json =CC.STRATUM_LEAF_PIPELINE,
#                                     cpuport=self.leafSwitches[i].cpuPort, grpcport=self.leafSwitches[i].grpcPort,
#                                     gateway = self.leafSwitches[i].swGateway)
#         CC.GLOABAL_COMMAND_STRING= CC.GLOABAL_COMMAND_STRING + "topo.addSwitch("+self.leafSwitches[i].switchName+", cls=ONOSBmv2Switch, pipeline_json ="+CC.STRATUM_LEAF_PIPELINE+"," \
#                                    +"cpuport="+str(self.leafSwitches[i].cpuPort)+", grpcPort="+str(self.leafSwitches[i].grpcPort)+"," +"gateway = "+str(self.leafSwitches[i].swGateway)+")"+"\n"
#         self.mininetLeafSwtiches.append(leafSwitch)
#         self.leafSwitches[i].addMyMininetInstance(leafSwitch)
#         for j in range (0, len( self.leafSwitches[i].hosts)):
#             print("Adding following host: ", self.leafSwitches[i].hosts[j].name)
#             print("It's mac is :|"+self.leafSwitches[i].hosts[j].hostMAC+"|")
#             print("It's mac is :|"+self.leafSwitches[i].hosts[j].hostMAC+"|")
#             print("It's ip is :|"+str( self.leafSwitches[i].hosts[j].hostIPv6) +
#                   CC.FLAT_IPV6_PREFIX)
#             print("Its gateway is :"+str(self.leafSwitches[i].swGateway +
#                                          CC.FLAT_IPV6_PREFIX))
#             h = topo.addHost(self.leafSwitches[i].hosts[j].name, cls=IPv6Host,
#                              mac=str(self.leafSwitches[i].hosts[j].hostMAC), ipv6=str( self.leafSwitches[i].hosts[j].hostIPv6) +
#                                                                                   CC.FLAT_IPV6_PREFIX,
#                              ipv6_gw = str(self.leafSwitches[i].swGateway +
#                                            CC.FLAT_IPV6_PREFIX))
#             CC.GLOABAL_COMMAND_STRING= CC.GLOABAL_COMMAND_STRING + "topo.addHost("+self.leafSwitches[i].hosts[j].name+", cls=IPv6Host,mac="+ str(self.leafSwitches[i].hosts[j].hostMAC) +", ipv6="+str( self.leafSwitches[i].hosts[j].hostIPv6) +CC.FLAT_IPV6_PREFIX+",ipv6_gw = "+ str(self.leafSwitches[i].swGateway +CC.FLAT_IPV6_PREFIX)+")" +"\n"
#             #self.addLink(leafSwitch,h)
#             self.leafSwitches[i].hosts[j].addMyMininetInstance(h)
#             self.leafSwitches[i].mininetHosts.append(h)
#             print("adding host to switch link")
#             print("node 1 "+str(self.leafSwitches[i].ports[j].getRemoteEnd().getMyMininetInstance() ))
#             print("node 2 "+str(self.leafSwitches[i].getMyMininetInstance() ))
#             print("port1 "+str(self.leafSwitches[i].ports[j].getPortRemoteID() ))
#             print("port2 "+str(self.leafSwitches[i].ports[j].getPortLocalID()))
#
#             topo.addLink(self.leafSwitches[i].ports[j].getRemoteEnd().getMyMininetInstance(), self.leafSwitches[i].getMyMininetInstance(),self.leafSwitches[i].ports[j].getPortRemoteID(), self.leafSwitches[i].ports[j].getPortLocalID()+1)
#             CC.GLOABAL_COMMAND_STRING= CC.GLOABAL_COMMAND_STRING + "topo.addLink("+str(self.leafSwitches[i].ports[j].getRemoteEnd().getMyMininetInstance()) + ","+ str(self.leafSwitches[i].getMyMininetInstance())+","+str(self.leafSwitches[i].ports[j].getPortRemoteID())+","+ str(self.leafSwitches[i].ports[j].getPortLocalID()+1)+")\n"
#
#
#             #this loop is for adding link between spine and leaf switch inside a pod
#     for j in range (0, (len(self.spineSwitches))):
#         for k in range (0, (len(self.spineSwitches[j].ports)/2)):  #Because last of the ports are already connected to superspine
#             if(self.spineSwitches[j].ports[k].getRemoteEnd() == None):
#                 print("This port is not connected. Port Details:", str(self.superSpineSwitches[j].ports[k]))
#             else:
#                 print("Port info:",str(self.spineSwitches[j].ports[k]))
#                 print("src: ",self.spineSwitches[j].getMyMininetInstance())
#                 print("dest: ",self.spineSwitches[j].ports[k].getRemoteEnd().getMyMininetInstance())
#                 print("local port:",self.spineSwitches[j].ports[k].getPortLocalID())
#                 print("dest port:",self.spineSwitches[j].ports[k].getPortRemoteID() )
#                 k=topo.addLink(self.spineSwitches[j].getMyMininetInstance(), self.spineSwitches[j].ports[k].getRemoteEnd().getMyMininetInstance(),
#                                self.spineSwitches[j].ports[k].getPortLocalID(), self.spineSwitches[j].ports[k].getPortRemoteID())
#
#     pass
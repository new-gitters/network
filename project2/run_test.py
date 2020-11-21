#!/usr/bin/python
"""
Test TCP's efficiency and convergence to fairness within mininet.
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.cli import CLI

import sys
import subprocess

import time
from threading import Timer

from config import *
from outputconfig import *

tcp_probe_pid = 0
expt_start_time = 0

############################################################
## Methods to set up the topology, access hosts, switches, etc.

class SetupTopo(Topo):
    """ Simple topology to setup N sources, a bottleneck link, and N
    destinations. Here N is the config parameter `num_hostpairs`. 
    """

    def __init__(self, **opts):
        """ Construct topology with num_hostpairs host pairs sending
        traffic through a single bottleneck link. """
        Topo.__init__(self, **opts)
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        self.addLink(s1, s2) # bottleneck link
        # Bottleneck link bandwidth will be set up using `tc` later on.
        hosts_src = []
        hosts_dst = []
        for i in range(0, num_hostpairs):
            hosts_src.append(self.addHost('hsrc' + str(i),
                                          cpu=total_cpu_fraction/(2*num_hostpairs)))
            hosts_dst.append(self.addHost('hdst' + str(i),
                                          cpu=total_cpu_fraction/(2*num_hostpairs)))
            self.addLink(hosts_src[-1], s1)
            self.addLink(hosts_dst[-1], s2)

def getHosts(net):
    """ Get host Node objects corresponding to host names """
    hosts_src = []
    hosts_dst = []
    for i in range(0, num_hostpairs):
        hosts_src.append(net.getNodeByName('hsrc' + str(i)))
        hosts_dst.append(net.getNodeByName('hdst' + str(i)))
    return [hosts_src, hosts_dst]

def getSwitches(net):
    """ Get switch Node objects corresponding to switch names """
    s1 = net.getNodeByName('s1')
    s2 = net.getNodeByName('s2')
    return [s1, s2]

def pingFlowPairs(net, hosts_src, hosts_dst):
    """ Test connectivity between flow sources and destinations """
    assert len(hosts_src) == len(hosts_dst)
    print "Running pings between host pairs (outputs Yes if successful)"
    for i in range(0, len(hosts_src)):
        result = hosts_src[i].cmd('ping -c1 %s' % (hosts_dst[i].IP()))
        sent, received = net._parsePing(result)
        print 'src%d -> dst%d ' % (i, i) + 'Yes' if received else 'No '

############################################################
## Methods involving linux traffic control: set up limits,
## measurements, etc.

def getExptTime():
    """ Return time since the experiment started """
    return time.time() - expt_start_time

def sendCommandWithTime(host, cmd):
    """ Return results from sending a command to a host """
    # print "*** running command", cmd, "on host", host.name
    host.sendCmd(cmd)
    result = host.waitOutput()
    return str(getExptTime()) + " " + result.strip() + "\n"

def getTcStatCommand():
    """ Build a tc stat command to send to switch. 
    Mainly captures packet drops as of now.

    """
    cmd = "tc -s -d qdisc show dev s1-eth1 | grep dropped | head -1"
    return cmd

def getTcStats(net, switches_list):
    """ Collect tc stats for drops and overlimits """
    s1, s2 = switches_list
    tcp_stats = open(tmp_folder + tcp_stats_file, "w")

    end_time = time.time() + test_duration_sec
    while time.time() < end_time:
        # Record the tc stats line containing sent, drops and
        # overlimits
        cmd = getTcStatCommand()
        tcp_stats.write(sendCommandWithTime(s1, cmd))

        # Do the measurements periodically
        time.sleep(tc_drops_measurement_interval_sec)

    tcp_stats.close()

def setupTc(net, hosts_src, switches_list):
    """ Set up the bottleneck link rate for the network. """
    s1, s2 = switches_list
        
    # s1-s2 link capacity
    s1.cmd("ip link set s1-eth1 txqueuelen 2")
    s1.cmd("tc qdisc add dev s1-eth1 root handle 1: htb default 1")
    s1.cmd("tc class add dev s1-eth1 parent 1: classid 1:1 htb rate "
           + str(bottleneck_bandwidth_Mbps) + "Mbit")
    s1.cmd("tc qdisc add dev s1-eth1 parent 1:1 handle 10: netem "
           + "delay " + str(round_trip_delay_ms) + "ms "
           + "limit " + str(bottleneck_buffer_pkts))

############################################################
## Methods to run the workload, e.g., `iperf`

def startExpt():
    """ Record starting time of the experiment in the variable
    expt_start_time. To be used every time we want to know the time
    elapsed in the experiment. """
    global expt_start_time
    expt_start_time = time.time()
    f = open(tmp_folder + start_time_file, "w")
    f.write(str(expt_start_time))
    f.close()

def runIperfTest(net, hosts_src, hosts_dst, switches_list):
    """ Run iperf testing between hosts in the network and record
    throughput results. """
    global tcp_probe_pid
    s1, s2 = switches_list

    # open files to note experiment timestamps
    expt_start_files = []
    for i in range(0, num_hostpairs):
        expt_start_files.append(open(
            tmp_folder + "hsrc" + str(i) + expt_start_suffix,
            "w"))
    
    print "  Starting iperf servers on flow destination hosts"
    tcp_hosts_count = int(num_hostpairs)
    for h in hosts_dst[0:tcp_hosts_count]: # for each TCP host pair
        h.cmd("iperf -s -p 5003 -i 1 " +
              " > " + tmp_folder + h.name +
              tcp_server_throughput_suffix + " &")

    print "  Running tcp_probe for TCP parameter captures"
    subprocess.check_output("sudo modprobe tcp_probe", shell=True)
    tcp_probe_cmd = ("cat /proc/net/tcpprobe > " +
                     tmp_folder + tcp_probe_file + " & ")
    if debug_mode:
        print "TCP probe capture:"
        print tcp_probe_cmd
    tcp_probe_pid = subprocess.Popen(tcp_probe_cmd, shell=True)

    time.sleep(2) # this seems to be required to allow successful
                  # TCP connection establishment from clients

    print "  Starting iperf client transmission"
    startExpt()

    for i in range(0, num_hostpairs):
        hsrc = hosts_src[i]
        hdst = hosts_dst[i]
        cmd_str = ("iperf -t " + str(test_duration_sec) + " -c " +
                   hdst.IP() + " -p 5003 -i 1 -Z " + tcp_flavor +
                   " > " +
                   tmp_folder + hsrc.name +
                   tcp_server_throughput_suffix +" &")
        if debug_mode:
            print "Sending command", cmd_str, "to source", i
        hsrc.cmd(cmd_str)
        expt_start_files[i].write(str(getExptTime()))
        expt_start_files[i].close()

def finishTcpprobe(switches_list):
    """ Remove lingering tcp_probe process writing to output. """
    s1, s2 = switches_list
    tcp_probe_pid.kill()

############################################################
## The main methods.

def sharingTest():
    """ Main """
    topo = SetupTopo()
    # net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net = Mininet(topo=topo, host=CPULimitedHost)
    net.start()

    print "Dumping host links"
    dumpNodeConnections(net.hosts)

    [hosts_src, hosts_dst] = getHosts(net)
    switches_list = getSwitches(net)

    print "Testing network connectivity"
    pingFlowPairs(net, hosts_src, hosts_dst)

    print "Setting up the bottleneck link"
    setupTc(net, hosts_src, switches_list)

    print "Starting traffic workload (iperf)"
    runIperfTest(net, hosts_src, hosts_dst, switches_list)
    
    print "Collecting statistics... this will run for",
    print test_duration_sec, "seconds"
    getTcStats(net, switches_list)

    print "Run finished"

    finishTcpprobe(switches_list)
    net.stop()
    
if __name__ == '__main__':
    setLogLevel('info')
    sharingTest()

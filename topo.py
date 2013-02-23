#!/usr/bin/python

from mininet.cli import CLI
from mininet.net import Mininet
from mininet.topo import Topo

"""
from mininet.link import TCLink
from mininet.log import lg
from mininet.node import CPULimitedHost
from mininet.util import dumpNodeConnections

import subprocess
from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
import termcolor as T
from argparse import ArgumentParser

import sys
import os
from util.monitor import monitor_qlen
from util.helper import stdev
"""

class TestTopo(Topo):
  def __init__(self):
    Topo.__init__(self)
    sw = self.addSwitch("s1", ip="10.0.0.1", mac="00:00:00:00:00:01", dpid="000001")
    self.addHost("h1", ip="10.0.0.2", mac="00:00:00:00:00:02", dpid="000002")
    self.addHost("h2", ip="10.0.0.3", mac="00:00:00:00:00:03", dpid="000003")
    self.addLink("s1", "h1")
    self.addLink("s1", "h2")

SWITCH, HOST_SW, HOST_CPU = range(1, 4)

# TODO: IP addresses can only support DCell1. Do we care?
class DCellTopo(Topo):
  def __init__(self, level=1, n=4):
    Topo.__init__(self)

    if level > 1:
      print "DCell levels above 1 don't work yet..."
      sys.exit(1)

    create_dcell([], level, n + level)

  def make_ids(list, type):
    """ Make name, IP, MAC, and DPID from list of indices. """
    if type == SWITCH: type_str = "sw"
    elif type == HOST_SW: type_str = "host"
    elif type == HOST_CPU: type_str = "cpu"
    else: type_str = "invalid"

    name = ".".join(["%d" % x for x in list] + [type_str])
    ids = {}
    ids["dpid"] = sum([x << (8 * i) for (i, x) in enumerate(list)])

    for i in range(2 - len(list): list.insert(0, 0)
    ids["ip"] = ".".join(["10"] + ["%d" % x for x in list + [type]])

    for i in range(5 - len(list)): list.insert(0, 0)
    ids["mac"] = ":".join(["%02x" % x for x in list + [type]])

    return

  def create_dcell(self, prefix, level, n):
    if level == 0:
      sw = self.addSwitch("s%s" % prefix)
      for i in range(n):
        name = "%s%d" % (prefix, i)
        host = self.addSwitch("h%s" % name)
        cpu  = self.addNode("c%s" % name)
        self.addLink(host, cpu)
        self.addLink(sw, host)
      return

    for i in range(1, n + 1):
      create_dcell(prefix + [i], level - 1, n - 1)

if __name__ == "__main__":
  net = Mininet(topo = TestTopo())
  net.start()
  CLI(net)
  net.stop()


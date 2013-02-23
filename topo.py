#!/usr/bin/python

from mininet.cli import CLI
from mininet.net import Mininet
from mininet.topo import Topo

from util import *

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


class DCellTopo(Topo):
  def __init__(self, level=1, n=4):
    Topo.__init__(self)

    if level > 1:
      print "DCell levels above 1 don't work yet..."
      sys.exit(1)

    create_dcell([], level, n + level)

  def add_host(list):
    name, ids = make_ids(list, HOST_CPU)
    return self.addHost(name, **ids)

  def add_switch(list, type):
    (name, ids) = make_ids(list, type):
    return self.addSwitch(name, **ids)

  def create_dcell(self, prefix, level, n):
    if level == 0:
      sw = self.add_switch(prefix + [0], SWITCH)
      for i in range(1, n + 1):
        list = prefix + [i]
        host = self.add_switch(list, HOST_SW)
        cpu  = self.add_host(list)
        self.addLink(host, cpu)
        self.addLink(sw, host)
      return

    for i in range(1, n + 1):
      create_dcell(prefix + [i], level - 1, n - 1)
      # TODO: Add inter-DCell0 links...

if __name__ == "__main__":
  topo = DCellTopo(level=0)
  net = Mininet(topo = topo)
  net.start()
  CLI(net)
  net.stop()


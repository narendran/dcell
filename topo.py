#!/usr/bin/python

from mininet.cli import CLI
from mininet.node import RemoteController
from mininet.net import Mininet
from mininet.topo import Topo

import sys
from failure import sim_failures
from nodeid import DCellNodeID

class DCellTopo(Topo):
  def __init__(self, level=1, n=4):
    Topo.__init__(self)

    if level > 1:
      print "DCell levels above 1 don't work yet..."
      sys.exit(1)

    self.level = level
    self.sws = {}
    self._create_dcell([], level, n)

    self.failed = []

  def id_gen(self, *args, **kwargs):
    return DCellNodeID(self.level, *args, **kwargs)

  def link_down(self, *n):
    self.failed.append(n)
  def is_link_down(self, *n):
    return n in self.failed

  def _add_node(self, prefix, type):
    id = self.id_gen(prefix, type)
    args = {'dpid': "%016x" % id.dpid, 'ip': id.ip_str(), 'mac': id.mac_str()}
    if type == DCellNodeID.HOST_CPU: return self.addHost(str(id), **args)
    sw = self.addSwitch(str(id), **args)
    if type == DCellNodeID.HOST_SW: self.sws[str(id)] = (id, sw)
    return sw

  def _create_dcell(self, prefix, level, n):
    if level == 0:
      sw = self._add_node(prefix + [0], DCellNodeID.SWITCH)
      for i in range(1, n + 1):
        l = prefix + [i]
        print ".",
        sys.stdout.flush()
        host = self._add_node(l, DCellNodeID.HOST_SW)
        cpu  = self._add_node(l, DCellNodeID.HOST_CPU)
        self.addLink(host, cpu)
        self.addLink(sw, host)
      return

    # TODO: Generalize to DCell_k, k > 1
    for i in range(1, n + 2):
      self._create_dcell(prefix + [i], level - 1, n)
    for i in range(1, n + 1):
      for j in range(i + 1, n + 2):
        id1 = self.id_gen(prefix + [i, j - 1], DCellNodeID.HOST_SW)
        id2 = self.id_gen(prefix + [j, i], DCellNodeID.HOST_SW)
        n1 = self.sws[str(id1)][1]
        n2 = self.sws[str(id2)][1]
        self.addLink(n1, n2)

  # Used by riplpox
  LAYER_EDGE = DCellNodeID.HOST_SW
  def layer_nodes(self, layer):
    return [x[0].name_str() for x in self.sws.values() if x[0].type == layer]

  def down_nodes(self, node):
    assert "host" in node
    return [node.replace("host", "cpu")]

if __name__ == "__main__":
  topo = DCellTopo()
  net = Mininet(topo = topo, controller = RemoteController, autoSetMacs = True)
  net.start()
  sim_failures(topo, net)
  CLI(net)
  net.stop()


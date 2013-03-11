from nodeid import DCellNodeID
import os, sys
from time import sleep

def fail_link(topo, net, n1, n2, node = False):
  if node: print "Failing node %s" % n1
  else: print "Failing link %s <-> %s" % (n1, n2)
  if net: net.configLinkStatus(n1, n2, "down")
  if node:
    sleep(5)
    print "Link state timeout"
  topo.link_down(n1, n2)

def reset_link(topo, net, n1, n2):
  print "Restoring link %s <-> %s" % (n1, n2)
  if net: net.configLinkStatus(n1, n2, "up")
  topo.link_up(n1, n2)

def sim_failures(topo, net = None):
  n1, n2 = ("14h", "51h")
  while not os.access("start.txt", os.R_OK): sleep(0.1)
  print "Starting experiment..."
  sleep(34)
  fail_link(topo, net, n1, n2)
  sleep(8)
  reset_link(topo, net, n1, n2)
  sleep(62)
  fail_link(topo, net, n1, n2, True)

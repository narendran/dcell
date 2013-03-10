from nodeid import DCellNodeID
from time import sleep

def sim_failures(topo, net = None):
  print "Started thread"
  sleep(5)
  print "Failing link"
  n = ("1_1_host", "2_1_host")
  topo.link_down(*n)
  if net:
    print "Net"
    net.configLinkStatus(n[0], n[1], "down")

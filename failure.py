from nodeid import DCellNodeID
import os, sys
from time import sleep

def sim_failures(topo, net = None):
  print "Started thread"
  while not os.access("linkfail.txt", os.R_OK):
    sleep(1)
  print "Failing link"
  n = ("1_1_host", "2_1_host")
  topo.link_down(*n)
  if net:
    print "Net"
    net.configLinkStatus(n[0], n[1], "down")

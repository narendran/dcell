import os, sys
from multiprocessing import Process
from nodeid import DCellNodeID
from subprocess import Popen
from time import sleep

OUTPUT_DIR = "out"

def fail_link(topo, net, n1, n2, node = False):
  if net:
    if node: print "Failing node %s" % n1
    else: print "Failing link %s <-> %s" % (n1, n2)
    net.configLinkStatus(n1, n2, "down")
  if node:
    sleep(5)
    if net: print "Link state timeout"
  # We pause for a second to allow all existing flows in the network to clear out before clearing flow tables
  else: sleep(1)
  topo.link_down(n1, n2)

def reset_link(topo, net, n1, n2):
  if net:
    print "Restoring link %s <-> %s" % (n1, n2)
    net.configLinkStatus(n1, n2, "up")
  topo.link_up(n1, n2)

# Taken from PA 2 starter code
def monitor_devs_ng(fname="%s/txrate.txt" % OUTPUT_DIR, interval_sec=1):
  """Uses bwm-ng tool to collect iface tx rate stats.  Very reliable."""
  cmd = ("sleep 1; bwm-ng -t %s -o csv "
         "-u bits -T rate -C ',' > %s" %
         (interval_sec * 1000, fname))
  Popen(cmd, shell=True).wait()

def start_monitor():
  p = Process(target=monitor_devs_ng, args=())
  p.start()
  return p

def start_iperf(net, src, dst):
  server = net.getNodeByName(dst)
  server.popen("iperf -s -p 5001 >%s/server.txt" % OUTPUT_DIR, shell=True)

  client = net.getNodeByName(src)
  client.popen("iperf -c %s -p 5001 -i 1 -t 3600 -Z bic >%s/client.txt" % (server.IP(), OUTPUT_DIR), shell=True)

def my_sleep(t, net):
  for i in range(t):
    sleep(1)
    if net: print "%d" % (t - i - 1),
    sys.stdout.flush()

def run_experiment(topo, net = None):
  fname = "start.txt"
  if net:
    start_iperf(net, "11c", "54c")
    sleep(3)
    monitor = start_monitor()
    with open(fname, "w") as f: f.write("go")
    print "Starting 1"
  else:
    while not os.access(fname, os.R_OK): sleep(0.1)
    print "Starting 2"

  n1, n2 = ("14h", "51h")
  my_sleep(34, net)
  fail_link(topo, net, n1, n2)
  my_sleep(8, net)
  reset_link(topo, net, n1, n2)
  my_sleep(62, net)
  fail_link(topo, net, n1, n2, True)
  my_sleep(30, net)

  if net:
    monitor.terminate()
    Popen("killall -9 iperf bwm-ng", shell=True).wait()
    os.remove(fname)
    print "Done with experiment. Please type quit()."

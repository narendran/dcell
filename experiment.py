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
    my_sleep(5)
    if net: print "Link state timeout"
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

def my_sleep(t):
  for i in range(t):
    sleep(1)
    print "%d" % (t - i - 1),
    sys.stdout.flush()

def run_experiment(topo, net = None):
  fname = "start.txt"
  if net:
    with open(fname, "w") as f: f.write("go")
    start_iperf(net, "11c", "54c")
    monitor = start_monitor()
  else:
    while not os.access("start.txt", os.R_OK): sleep(0.1)
    print "Starting experiment..."

  n1, n2 = ("14h", "51h")
  my_sleep(5)
  #my_sleep(34)
  fail_link(topo, net, n1, n2)
  my_sleep(5)
  #my_sleep(8)
  reset_link(topo, net, n1, n2)
  my_sleep(5)
  #my_sleep(62)
  fail_link(topo, net, n1, n2, True)
  my_sleep(10)

  if net:
    monitor.terminate()
    Popen("killall -9 iperf bwm-ng", shell=True).wait()
    os.remove(fname)
  else: print "Done"

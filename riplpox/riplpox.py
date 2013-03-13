"""
RipL+POX.  As simple a data center controller as possible.
"""

import logging
from struct import pack
from zlib import crc32

from pox.core import core
from pox.lib.util import dpidToStr
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import EventMixin
from pox.lib.addresses import EthAddr
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.udp import udp
from pox.lib.packet.tcp import tcp

from ripl.mn import topos

import sys
from time import sleep
from util import buildTopo, getRouting

oflog = logging.getLogger("openflow.of_01")
oflog.setLevel(logging.WARNING)

log = core.getLogger()
log.setLevel(logging.WARNING)

# Number of bytes to send for packet_ins
MISS_SEND_LEN = 2000

MODES = ['reactive', 'proactive']
DEF_MODE = MODES[0]


# Borrowed from pox/forwarding/l2_multi
class Switch (EventMixin):
  def __init__ (self):
    self.connection = None
    self.ports = None
    self.dpid = None
    self._listeners = None

  def __repr__ (self):
    return dpidToStr(self.dpid)

  def disconnect (self):
    if self.connection is not None:
      log.debug("Disconnect %s" % (self.connection,))
      self.connection.removeListeners(self._listeners)
      self.connection = None
      self._listeners = None

  def connect (self, connection):
    if self.dpid is None:
      self.dpid = connection.dpid
    assert self.dpid == connection.dpid
    if self.ports is None:
      self.ports = connection.features.ports
    self.disconnect()
    log.debug("Connect %s" % (connection,))
    self.connection = connection
    self._listeners = self.listenTo(connection)

  def send_packet_data(self, outport, data = None):
    msg = of.ofp_packet_out(in_port=of.OFPP_NONE, data = data)
    msg.actions.append(of.ofp_action_output(port = outport))
    self.connection.send(msg)

  def send_packet_bufid(self, outport, buffer_id = -1):
    msg = of.ofp_packet_out(in_port=of.OFPP_NONE)
    msg.actions.append(of.ofp_action_output(port = outport))
    msg.buffer_id = buffer_id
    self.connection.send(msg)

  def install(self, port, match, buf = -1, idle_timeout = 0, hard_timeout = 0):
    msg = of.ofp_flow_mod()
    msg.match = match
    msg.idle_timeout = idle_timeout
    msg.hard_timeout = hard_timeout
    msg.actions.append(of.ofp_action_output(port = port))
    msg.buffer_id = buf
    self.connection.send(msg)

  def _handle_ConnectionDown (self, event):
    self.disconnect()
    pass


class RipLController(EventMixin):

  def __init__ (self, t, r, mode):
    self.switches = {}  # Switches seen: [dpid] -> Switch
    self.t = t  # Master Topo object, passed in and never modified.
    self.r = r  # Master Routing object, passed in and reused.
    self.mode = mode # One in MODES.
    self.macTable = {}  # [mac] -> (dpid, port)

    # TODO: generalize all_switches_up to a more general state machine.
    self.all_switches_up = False  # Sequences event handling.
    self.listenTo(core.openflow, priority=0)
    self.t.controller = self
    self.failed = 0
    self.flows = []

  def _handle_PortStatus(self, event):
    if event.ofp.desc.state == 1:
      self.failed += 1
      #if self.failed == 2: 
      #  sleep(1)
      #  self.clearFlowTables()
    elif event.ofp.desc.state == 0:
      self.failed -= 1
      #if self.failed == 0:
      #  print "Full clear"
      #  self.clearFlowTables()

  #    self.clearFlowTables()
  #  # We only fail port 3
  #  print "!!! %d %d" % (event.port, event.ofp.desc.state)
  #  if event.port != 3: return

  #  oldfail = self.fail
  #  if event.ofp.desc.state == 1: # Down
  #    if not self.fail: sleep(1) # Pause to avoid race conditions and nasty things
  #    self.fail = True
  #  elif event.ofp.desc.state == 0: # Up
  #    if self.fail: sleep(1)
  #    self.fail = False

  #  if self.fail == oldfail: return
  def clearFlowTables(self):
    # Taken from pox/forwarding/l2_multi.py
    clear = of.ofp_flow_mod(match=of.ofp_match(),command=of.OFPFC_DELETE)
    for sw in self.switches.itervalues():
      sw.connection.send(clear)

    # Reset all the previously seen flows (otherwise disaster strikes)
    for x in self.flows:
      route = self.r.get_route(x[0], x[1], None)
      #print "! %s" % route
      for i, node in enumerate(route):
        node_dpid = self.t.id_gen(name = node).dpid
        if i < len(route) - 1:
          next_node = route[i + 1]
          out_port, next_in_port = self.t.port(node, next_node)
        else:
          out_port = x[2]
        self.switches[node_dpid].install(out_port, x[3], idle_timeout = 10)

  def _raw_dpids(self, arr):
    "Convert a list of name strings (from Topo object) to numbers."
    return [self.t.id_gen(name = a).dpid for a in arr]

  def _ecmp_hash(self, packet):
    "Return an ECMP-style 5-tuple hash for TCP/IP packets, otherwise 0."
    hash_input = [0] * 5
    if isinstance(packet.next, ipv4):
      ip = packet.next
      hash_input[0] = ip.srcip.toUnsigned()
      hash_input[1] = ip.dstip.toUnsigned()
      hash_input[2] = ip.protocol
      if isinstance(ip.next, tcp) or isinstance(ip.next, udp):
        l4 = ip.next
        hash_input[3] = l4.srcport
        hash_input[4] = l4.dstport
        return crc32(pack('LLHHH', *hash_input))
    return 0

  def _install_reactive_path(self, event, out_dpid, final_out_port, packet):
    "Install entries on route between two switches."
    in_name = self.t.id_gen(dpid = event.dpid).name_str()
    out_name = self.t.id_gen(dpid = out_dpid).name_str()
    hash_ = self._ecmp_hash(packet)
    route = self.r.get_route(in_name, out_name, hash_)
    # XXX
    log.info("route from %s to %s: %s" % (in_name, out_name, route))
    match = of.ofp_match.from_packet(packet)
    if (in_name == "11h" and out_name == "54h") or (in_name == "54h" and out_name == "11h"):
      self.flows.append((in_name, out_name, final_out_port, match))
      #print "!!! %s -> %s: %s" % (in_name, out_name, route)
    for i, node in enumerate(route):
      node_dpid = self.t.id_gen(name = node).dpid
      if i < len(route) - 1:
        next_node = route[i + 1]
        out_port, next_in_port = self.t.port(node, next_node)
      else:
        out_port = final_out_port
      self.switches[node_dpid].install(out_port, match, idle_timeout = 10)

  def _src_dst_hash(self, src_dpid, dst_dpid):
    "Return a hash based on src and dst dpids."
    return crc32(pack('QQ', src_dpid, dst_dpid))

  def _install_proactive_path(self, src, dst):
    """Install entries on route between two hosts based on MAC addrs.
    
    src and dst are unsigned ints.
    """
    src_sw = self.t.up_nodes(self.t.id_gen(dpid = src).name_str())
    assert len(src_sw) == 1
    src_sw_name = src_sw[0]
    dst_sw = self.t.up_nodes(self.t.id_gen(dpid = dst).name_str())
    assert len(dst_sw) == 1
    dst_sw_name = dst_sw[0]
    hash_ = self._src_dst_hash(src, dst)
    route = self.r.get_route(src_sw_name, dst_sw_name, hash_)
    log.info("route: %s" % route)

    # Form OF match
    match = of.ofp_match()
    match.dl_src = EthAddr(src).toRaw()
    match.dl_dst = EthAddr(dst).toRaw()

    dst_host_name = self.t.id_gen(dpid = dst).name_str()
    final_out_port, ignore = self.t.port(route[-1], dst_host_name)
    for i, node in enumerate(route):
      node_dpid = self.t.id_gen(name = node).dpid
      if i < len(route) - 1:
        next_node = route[i + 1]
        out_port, next_in_port = self.t.port(node, next_node)
      else:
        out_port = final_out_port
      self.switches[node_dpid].install(out_port, match)

  def _flood(self, event):
    packet = event.parsed
    dpid = event.dpid
    #log.info("PacketIn: %s" % packet)
    in_port = event.port
    t = self.t

    # Broadcast to every output port except the input on the input switch.
    # Hub behavior, baby!
    for sw in self._raw_dpids(t.layer_nodes(t.LAYER_EDGE)):
      #log.info("considering sw %s" % sw)
      ports = []
      sw_name = t.id_gen(dpid = sw).name_str()
      for host in t.down_nodes(sw_name):
        sw_port, host_port = t.port(sw_name, host)
        if sw != dpid or (sw == dpid and in_port != sw_port):
          ports.append(sw_port)
      # Send packet out each non-input host port
      # TODO: send one packet only.
      for port in ports:
        #log.info("sending to port %s on switch %s" % (port, sw))
        #buffer_id = event.ofp.buffer_id
        #if sw == dpid:
        #  self.switches[sw].send_packet_bufid(port, event.ofp.buffer_id)
        #else:
        self.switches[sw].send_packet_data(port, event.data)
        #  buffer_id = -1

  def _handle_packet_reactive(self, event):
    packet = event.parsed
    dpid = event.dpid
    #log.info("PacketIn: %s" % packet)
    in_port = event.port
    t = self.t

    # Learn MAC address of the sender on every packet-in.
    self.macTable[packet.src] = (dpid, in_port)

    #log.info("mactable: %s" % self.macTable)

    # Insert flow, deliver packet directly to destination.
    if packet.dst in self.macTable:
      out_dpid, out_port = self.macTable[packet.dst]
      self._install_reactive_path(event, out_dpid, out_port, packet)

      #log.info("sending to entry in mactable: %s %s" % (out_dpid, out_port))
      self.switches[out_dpid].send_packet_data(out_port, event.data)

    else:
      self._flood(event)

  def _handle_packet_proactive(self, event):
    packet = event.parse()

    if packet.dst.isMulticast():
      self._flood(event)
    else:
      hosts = self._raw_dpids(self.t.layer_nodes(self.t.LAYER_HOST))
      if packet.src.toInt() not in hosts:
        raise Exception("unrecognized src: %s" % packet.src)
      if packet.dst.toInt() not in hosts:
        raise Exception("unrecognized dst: %s" % packet.dst)
      raise Exception("known host MACs but entries weren't pushed down?!?")

  def _handle_PacketIn(self, event):
    #log.info("Parsing PacketIn.")
    if not self.all_switches_up:
      log.info("Saw PacketIn before all switches were up - ignoring.")
      return
    else:
      if self.mode == 'reactive':
        self._handle_packet_reactive(event)
      elif self.mode == 'proactive':
        self._handle_packet_proactive(event)

  def _install_proactive_flows(self):
    t = self.t
    # Install L2 src/dst flow for every possible pair of hosts.
    for src in sorted(self._raw_dpids(t.layer_nodes(t.LAYER_HOST))):
      for dst in sorted(self._raw_dpids(t.layer_nodes(t.LAYER_HOST))):
        self._install_proactive_path(src, dst)


  def _handle_ConnectionUp (self, event):
    sw = self.switches.get(event.dpid)
    sw_str = dpidToStr(event.dpid)
    log.info("Saw switch come up: %s", sw_str)
    name_str = self.t.id_gen(dpid = event.dpid).name_str()

    print name_str,
    sys.stdout.flush()

    if name_str not in self.t.switches():
      log.warn("Ignoring unknown switch %s" % sw_str)
      return
    if sw is None:
      log.info("Added fresh switch %s" % sw_str)
      sw = Switch()
      self.switches[event.dpid] = sw
      sw.connect(event.connection)
    else:
      log.info("Odd - already saw switch %s come up" % sw_str)
      sw.connect(event.connection)
    sw.connection.send(of.ofp_set_config(miss_send_len=MISS_SEND_LEN))

    if len(self.switches) == len(self.t.switches()):
      log.info("Woo!  All switches up")
      self.all_switches_up = True
      if self.mode == 'proactive':
        self._install_proactive_flows()

  #def _handle_PortStatus(self, event):
  #  # If not eth3, not a link event we care about
  #  if (event.port != 3: return
  #  sw = self.t.id_gen(dpid = event.dpid).name_str()
  #  print "!! %s: %d" % (sw, event.ofp.desc.state)

def launch(topo = None, routing = None, mode = None):
  """
  Args in format toponame,arg1,arg2,...
  """
  if not mode:
    mode = DEF_MODE
  # Instantiate a topo object from the passed-in file.
  if not topo:
    raise Exception("please specify topo and args on cmd line")
  else:
    t = buildTopo(topo, topos)
    r = getRouting(routing, t)

  core.registerNew(RipLController, t, r, mode)

  log.info("RipL-POX running with topo=%s." % topo)

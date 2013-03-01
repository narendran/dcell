from nodeid import DCellNodeID
from ripl.routing import Routing

class DCellRouting(Routing):
  def __init__(self, topo):
    Routing.__init__(self, topo)
    print "Started routing"

  def get_route(self, src, dst, pkt):
    print "Route from %s to %s" % (src, dst)
    if src == dst: return [src]
    src_id = self.topo.id_gen(name = src)
    dst_id = self.topo.id_gen(name = dst)
    if src_id.prefix[:-1] == dst_id.prefix[:-1]:
      prefix = src_id.prefix[:-1] + [0]
      sw = self.topo.id_gen(prefix, DCellNodeID.SWITCH)
      print "Local switch: %s" % sw
      return [src, sw.name_str(), dst]
    return None

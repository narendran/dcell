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
      sw = self.topo.id_gen(src_id.prefix[:-1] + [0], DCellNodeID.SWITCH)
      return [src, sw.name_str(), dst]

    # TODO: DCell1 only
    s = src_id.prefix[0]
    d = dst_id.prefix[0]
    assert s != d
    if s < d: min = s; max = d
    else: min = d; max = s

    n1 = self.topo.id_gen([min, max - 1], DCellNodeID.HOST_SW).name_str()
    n2 = self.topo.id_gen([max, min], DCellNodeID.HOST_SW).name_str()
    if min == s:
      r1 = self.get_route(src, n1, pkt)
      r2 = self.get_route(n2, dst, pkt)
    else:
      r1 = self.get_route(src, n2, pkt)
      r2 = self.get_route(n1, dst, pkt)
    return r1 + r2

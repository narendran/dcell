from failure import sim_failures
from nodeid import DCellNodeID
from threading import Thread
from ripl.routing import Routing

class DCellRouting(Routing):
  def __init__(self, topo):
    Routing.__init__(self, topo)
    t = Thread(target = sim_failures, args = (topo,))
    t.start()

  def get_route(self, src, dst, pkt):
    print "Route from %s to %s" % (src, dst)
    if src == dst: return [src]

    src_id = self.topo.id_gen(name = src)
    dst_id = self.topo.id_gen(name = dst)

    if src_id.prefix[:-1] == dst_id.prefix[:-1]:
      sw = self.topo.id_gen(src_id.prefix[:-1] + [0], DCellNodeID.SWITCH)
      return [src, sw.name_str(), dst]

    if src_id.prefix > dst_id.prefix:
      rev = True
      temp = src; src = dst; dst = temp
      temp = src_id; src_id = dst_id; dst_id = temp
    else: rev = False

    s = src_id.prefix[0]
    d = dst_id.prefix[0]
    assert s < d

    n1 = self.topo.id_gen([s, d - 1], DCellNodeID.HOST_SW).name_str()
    n2 = self.topo.id_gen([d, s], DCellNodeID.HOST_SW).name_str()

    if self.topo.is_link_down(n1, n2):
        n1r = ''
        n2r = ''
        for i in range(0, self.topo.n):
            n1r = self.topo.id_gen([s, i+1], DCellNodeID.HOST_SW).name_str()
            n2r = self.topo.id_gen([i+2, s], DCellNodeID.HOST_SW).name_str()
            if n1 != n1r:
                if not self.topo.is_link_down(n1, n1r):
                    break

        r1 = self.get_route(src, n1, pkt)
        rr1 = self.get_route(n1, n1r, pkt)
        rr2 = self.get_route(n2r, dst, pkt)

        newroute = r1[:-1] + rr1 + rr2
        if rev: newroute.reverse()
        return newroute
    else:
        r1 = self.get_route(src, n1, pkt)
        r2 = self.get_route(n2, dst, pkt)

        route = r1 + r2
        if rev: route.reverse()
        return route


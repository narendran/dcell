from experiment import *
from nodeid import DCellNodeID
from threading import Thread
from ripl.routing import Routing

class DCellRouting(Routing):
  def __init__(self, topo):
    Routing.__init__(self, topo)
    t = Thread(target = run_experiment, args = (topo,))
    t.start()

  def get_route(self, src, dst, pkt):
    if src == dst: return [src]

    src_id = self.topo.id_gen(name = src)
    dst_id = self.topo.id_gen(name = dst)

    if src_id.prefix[:-1] == dst_id.prefix[:-1]:
      sw = self.topo.id_gen(src_id.prefix[:-1] + [0], DCellNodeID.SWITCH).name_str()
      # Handles cases where a packet gets stuck in teh middle of the network while we reset flow tables
      if src == sw or dst == sw: return [src, dst]
      return [src, sw, dst]

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
        for i in range(self.topo.n + 1):
            n1r = self.topo.id_gen([s, i+1], DCellNodeID.HOST_SW).name_str()
            n2r = self.topo.id_gen([i+2, s], DCellNodeID.HOST_SW).name_str()
            if n1 != n1r and not self.topo.is_link_down(n1r, n2r):
                    break

        r1 = self.get_route(src, n1, pkt)
        rr1 = self.get_route(n1, n1r, pkt)
        rr2 = self.get_route(n2r, dst, pkt)

        route = r1[:-1] + rr1 + rr2
    else:
        r1 = self.get_route(src, n1, pkt)
        r2 = self.get_route(n2, dst, pkt)
        route = r1 + r2

    if rev: route.reverse()
    return route


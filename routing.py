from ripl.routing import Routing

class DCellRouting(Routing):
  def __init__(self, topo):
    Routing.__init__(self, topo)
    print "Started routing"

  def get_route(self, src, dst, pkt):
    print "Route from %s to %s" % (src, dst)
    return [src, dst]

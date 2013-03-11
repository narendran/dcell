from ripl.dctopo import NodeID

class DCellNodeID(NodeID):
  SWITCH, HOST_SW, HOST_CPU = range(1, 4)
  TYPES = ["s", "h", "c"]
  TYPE_MAP = {"s": SWITCH, "h": HOST_SW, "c": HOST_CPU}

  # Level is only needed for DPID
  def __init__(self, level, prefix = None, type = 0, dpid = None, name = None):
    if dpid: self.from_dpid(dpid, level)
    elif name: self.from_name(name)
    else:
      self.prefix = prefix
      self.type = type

    if not name: self.type_str = self.TYPES[self.type - 1]
    if not dpid: self.dpid = sum([x << (8 * i) for x, i in zip(self.prefix + [self.type], range(len(self.prefix), -1, -1))])

  def from_dpid(self, dpid, level):
    self.dpid = dpid
    self.prefix = [(dpid >> (8 * i)) & 0xff for i in range(level + 1, 0, -1)]
    self.type = dpid & 0xff

  def from_name(self, name):
    l = list(name)
    self.prefix = [int(x) for x in l[:-1]]
    self.type_str = l[-1]
    self.type = self.TYPE_MAP[self.type_str]

  def __str__(self):
    return self.name_str()

  def name_str(self):
    return "".join(["%d" % x for x in self.prefix] + [self.type_str])

  # TODO: Can't go past DCell 1
  def ip_str(self):
    iplist = list(self.prefix)
    for i in range(2 - len(iplist)): iplist.insert(0, 0)
    iplist.insert(0, 10)
    iplist.append(self.type)
    return ".".join(["%d" % x for x in iplist])

  def mac_str(self):
    maclist = list(self.prefix)
    for i in range(5 - len(maclist)): maclist.insert(0, 0)
    maclist.append(self.type)
    return ":".join(["%02x" % x for x in maclist])


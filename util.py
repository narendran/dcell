
SWITCH, HOST_SW, HOST_CPU = range(1, 4)

#TODO: Can't handle levels > 1
def make_ids(l, type):
  """ Make name, IP, MAC, and DPID from list of indices. """
  if type == SWITCH: type_str = "sw"
  elif type == HOST_SW: type_str = "host"
  elif type == HOST_CPU: type_str = "cpu"
  else: type_str = "invalid"

  name = ".".join(["%d" % x for x in l] + [type_str])
  ids = {}
  ids["dpid"] = "%016x" % sum([x << (8 * i) for (i, x) in enumerate(l)])

  l2 = list(l)
  for i in range(2 - len(l2)): l2.insert(0, 0)
  ids["ip"] = ".".join(["10"] + ["%d" % x for x in l2 + [type]])

  for i in range(5 - len(l2)): l2.insert(0, 0)
  ids["mac"] = ":".join(["%02x" % x for x in l2 + [type]])

  return (name, ids)


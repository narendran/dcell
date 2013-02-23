
def make_ids(list, type):
  """ Make name, IP, MAC, and DPID from list of indices. """
  if type == SWITCH: type_str = "sw"
  elif type == HOST_SW: type_str = "host"
  elif type == HOST_CPU: type_str = "cpu"
  else: type_str = "invalid"
  name = ".".join(["%d" % x for x in list] + [type_str])
  ids = {}
  ids["dpid"] = sum([x << (8 * i) for (i, x) in enumerate(list)])
  for i in range(2 - len(list)): list.insert(0, 0)
  ids["ip"] = ".".join(["10"] + ["%d" % x for x in list + [type]])
  for i in range(5 - len(list)): list.insert(0, 0)
  ids["mac"] = ":".join(["%02x" % x for x in list + [type]])
  return (name, ids)



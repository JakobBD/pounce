from machine import Machine

@Machine.RegisterSubclass('cray')
class CrayCluster(Machine):
   pass


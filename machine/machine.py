from baseclass import BaseClass

class Machine(BaseClass): 
   pass

@Machine.RegisterSubclass('local')
class LocalSystem(Machine):
   pass

@Machine.RegisterSubclass('cray')
class CrayCluster(Machine):
   pass


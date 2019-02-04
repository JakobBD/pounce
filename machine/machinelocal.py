from .machine import Machine

@Machine.RegisterSubclass('local')
class LocalSystem(Machine):
   pass

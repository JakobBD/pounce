from uqmethod import UqMethod

@UqMethod.RegisterSubclass('sc')
class Sc(UqMethod):
   def RunSimulation(self,machine,solver):
      pass

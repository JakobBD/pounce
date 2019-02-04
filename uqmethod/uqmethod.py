from baseclass import BaseClass

class UqMethod(BaseClass): 
   pass

@UqMethod.RegisterSubclass('sc')
class Sc(UqMethod):
   def RunSimulation(self,machine,solver):
      pass

@UqMethod.RegisterSubclass('mlmc')
class Mlmc(UqMethod):
   def RunSimulation(self,machine,solver):
      print("Run Simulation")



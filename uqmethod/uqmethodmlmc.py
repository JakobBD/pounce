from uqmethod import UqMethod

@UqMethod.RegisterSubclass('mlmc')
class Mlmc(UqMethod):

   def RunSimulation(self,machine,solver):
      pass



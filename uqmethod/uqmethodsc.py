from .uqmethod import UqMethod

@UqMethod.RegisterSubclass('sc')
class Sc(UqMethod):

   def InitLoc(self): 
      self.nMaxIter=1

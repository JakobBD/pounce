from .uqmethod import UqMethod

@UqMethod.RegisterSubclass('sc')
class Sc(UqMethod):
   stochVarDefaults={
      'PolyDeg': 'NODEFAULT'
      }

   def InitLoc(self): 
      self.nMaxIter=1

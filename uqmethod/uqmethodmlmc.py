from .uqmethod import UqMethod

@UqMethod.RegisterSubclass('mlmc')
class Mlmc(UqMethod):
   subclassDefaults={
         "nLevels" : "NODEFAULT",
         "nMaxIter" : "NODEFAULT"
         }



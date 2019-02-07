from helpers.baseclass import BaseClass

class Level(BaseClass):
   subclasses = {}
   classDefaults={
      'nCoresPerSample' : 'NODEFAULT'
      }

   def __init__(self,classDict,*args):
      for arg in args:
         self.classDefaults.update(arg)
      self.ReadPrms(classDict)
      self.InitLoc()


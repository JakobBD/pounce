from helpers.baseclass import BaseClass

class Level(BaseClass):
   subclasses = {}
   classDefaults={
      'nCoresPerSample' : 'NODEFAULT'
      }

   def __init__(self,inputPrmDict,*args):
      for arg in args:
         self.classDefaults.update(arg)
      super().__init__(inputPrmDict)


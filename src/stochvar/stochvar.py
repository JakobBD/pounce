from helpers.baseclass import BaseClass

class StochVar(BaseClass):
   subclasses = {}
   classDefaults={
      'name' : 'NODEFAULT'
      }

   def __init__(self,inputPrmDict,*args):
      for arg in args:
         self.classDefaults.update(arg)
      super().__init__(inputPrmDict)

from . import *

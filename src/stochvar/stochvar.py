from helpers.baseclass import BaseClass

class StochVar(BaseClass): 
   subclasses = {}
   classDefaults={
      'name' : 'NODEFAULT'
      }
   def __init__(self,classDict,*args):
      for arg in args:
         self.classDefaults.update(arg)
      self.ReadPrms(classDict)
      self.InitLoc()

from . import *

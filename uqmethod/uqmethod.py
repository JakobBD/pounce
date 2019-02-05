from helpers.baseclass import BaseClass

class UqMethod(BaseClass): 
   # dictionary of default input values; 
   # serves as check of correct input format and for default prm file printing
   classDefaults = {}
   subclasses = {}

   def RunSimulation(self,machine,solver):
      pass

from . import *

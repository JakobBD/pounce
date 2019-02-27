from helpers.baseclass import BaseClass


class UqMethod(BaseClass):

   subclasses={}
   stochVarDefaults={}
   levelDefaults={}


   def SetupBatches(self):
      pass




# import subclasses
from . import *

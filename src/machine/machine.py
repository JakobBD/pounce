from helpers.baseclass import BaseClass

class Machine(BaseClass):

   subclasses = {}
   stochVarDefaults={}
   levelDefaults={}

   def AllocateResourcesPostproc(self,batches):
      pass

from . import *

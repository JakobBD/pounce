from helpers.baseclass import BaseClass

class Machine(BaseClass):

   subclasses = {}
   stochVarDefaults={}
   levelDefaults={}

   def AllocateResourcesPostproc(self,batches):
      pass

   def AllocateResourcesSimuPostproc(self,batch):
      pass

from . import *

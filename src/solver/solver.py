import sys,os

from helpers.baseclass import BaseClass
from helpers.printtools import *

class Solver(BaseClass):
   subclasses = {}
   classDefaults = {
      "projectName":"NODEFAULT",
      "exePaths": {"mainSolver": "","iterationPostproc": "", "simulationPostproc": ""}
      }

   def CheckAllFinished(self,batches):
      finished = [self.CheckFinished(batch) for batch in batches]
      if all(finished): 
            Print("All jobs finished.")
      else:
         tmp=[batch.name for batch,isFinished in zip(batches,finished) if not isFinished]
         raise Exception("not all jobs finished. Problems with batch(es) "+", ".join(tmp)+".")

from . import *


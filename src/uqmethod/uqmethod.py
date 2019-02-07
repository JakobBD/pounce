from helpers.baseclass import BaseClass

class UqMethod(BaseClass):

   subclasses={}
   stochVarDefaults={}
   levelDefaults={}

   def SetupLevels(self):
      pass

   def RunSimulation(self):
      """Main Loop for UQMethod.
           General procedure:
           1. Let machine decide how many samples to compute.
           2. Generate samples and weights.
           3. Compute samples on system

      """
      iteration=0
      # main loop
      while True:
         # self.machine.allocateRessources(self.levels,self.solver.dofsPerCore)
         self.GetNodesAndWeights()
         self.PrepareSimulation()
         # self.machine.runBatch(self.solver)
         # self.machine.runBatch(postprocSolver)
         iteration+=1
         if(iteration==self.nMaxIter):
            break


# import subclasses
from . import *



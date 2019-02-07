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
         iteration+=1
         print("-"*132+"\nStart iteration %d\n"%(iteration)+"-"*132)
         # self.machine.allocateRessources(self.levels,self.solver.dofsPerCore)
         self.GetNodesAndWeights()
         self.PrepareAllSimulations()
         self.RunAllBatches()
         if(iteration==self.nMaxIter):
            # self.machine.runBatch(postprocSolver)
            break
         self.getNewSamples()

# import subclasses
from . import *

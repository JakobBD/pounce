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
         print("="*132+"\nStart iteration %d\n"%(iteration)+"="*132)
         # self.machine.allocateRessources(self.levels,self.solver.dofsPerCore)
         print("-"*132+"\nGet sample nodes and weights")
         self.GetNodesAndWeights()
         print("-"*132+"\nPrepare simulations")
         self.PrepareAllSimulations()
         print("-"*132+"\nRun simulations")
         self.RunAllBatches()
         if(iteration==self.nMaxIter):
            break
         print("-"*132+"\nGet number of samples for next iteration")
         self.getNewNSamples()
      print("="*132+"\nLast iteration finished. Exit loop.%d\n"%(iteration)+"="*132)
      # self.machine.runBatch(postprocSolver)

# import subclasses
from . import *

from helpers.baseclass import BaseClass
from helpers.printtools import *

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
         PrintMajorSection("Start iteration %d"%(iteration))
         # self.machine.allocateRessources(self.levels,self.solver.dofsPerCore)
         PrintMinorSection("Get samples:")
         self.GetNodesAndWeights()
         Print("Number of current samples for this iteration:")
         IndentIn()
         [Print("Level %2d: %6d samples"%(level.ind,level.nCurrentSamples)) for level in self.levels]
         IndentOut()
         PrintMinorSection("Prepare simulations:")
         self.PrepareAllSimulations()
         PrintMinorSection("Run simulations:")
         self.RunAllBatches()
         PrintMinorSection("Prepare postprocessing:")
         self.PrepareAllPostprocessing()
         PrintMinorSection("Run postprocessing:")
         self.RunAllBatchesPostprocessing()
         if(iteration==self.nMaxIter):
            break
         PrintMinorSection("Get number of samples for next iteration:")
         self.GetNewNCurrentSamples()
      PrintMajorSection("Last iteration finished. Exit loop.")
      # self.machine.runBatch(postprocSolver)

# import subclasses
from . import *

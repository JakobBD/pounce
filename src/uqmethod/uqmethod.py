import pickle

from helpers.baseclass import BaseClass
from helpers.printtools import *

class UqMethod(BaseClass):

   subclasses={}
   stochVarDefaults={}
   levelDefaults={}


   def __init__(self,inputPrmDict):
      super().__init__(inputPrmDict)
      self.iterations=[Iteration()]
      self.filename = "pickle"
      self.doContinue = True

   def SetupLevels(self):
      pass

   def RunSimulation(self):
      """Main Loop for UQMethod.
      """
      # main loop
      while self.doContinue:
         self.RunIteration()

      PrintMajorSection("Last iteration finished. Exit loop.")
      # self.machine.runBatch(postprocSolver)


   def RunIteration(self):
      """General procedure:
      
      1. Let machine decide how many samples to compute.
      2. Generate samples and weights.
      3. Compute samples on system
      """

      PrintMajorSection("Start iteration %d"%(len(self.iterations)))
      if self.iterations[-1].finishedSteps:
         Print(green("Skipping finished steps of iteration:"))
         [Print("  "+i) for i in self.iterations[-1].finishedSteps]

      # self.RunStep(self.machine.allocateRessources,"Allocate resources")

      self.RunStep(self.GetNodesAndWeights,"Get samples")

      self.RunStep(self.PrepareAllSimulations,"Prepare simulations")

      self.RunStep(self.RunAllBatches,"Run simulations")

      self.RunStep(self.PrepareAllPostprocessing,"Prepare postprocessing")

      self.RunStep(self.RunAllBatchesPostprocessing,"Run postprocessing")

      if len(self.iterations) == self.nMaxIter:
         self.doContinue=False
         return

      self.RunStep(self.GetNewNCurrentSamples,"Get number of samples for next iteration")

      if self.doContinue:
         self.iterations.append(Iteration())

      return


   def RunStep(self,func,description):
      if description not in self.iterations[-1].finishedSteps:
         PrintStep(description+":")
         func()
         self.iterations[-1].UpdateStep(self,description)



class Iteration():
   
   def __init__(self):
      self.finishedSteps=[]

   def UpdateStep(self,instance,string):
      self.finishedSteps.append(string)

      f = open(instance.filename, 'wb')
      pickle.dump(instance, f, 2)
      f.close()



# import subclasses
from . import *

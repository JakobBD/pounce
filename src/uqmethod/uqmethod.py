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

   def SetupBatches(self):
      pass

   def RunSimulation(self):
      """Main Loop for UQMethod.
      """
      # main loop
      while self.doContinue:
         self.RunIteration(self.iterations[-1])

      PrintMajorSection("Last iteration finished. Exit loop.")
      # self.machine.runBatch(postprocSolver)


   def RunIteration(self,iteration):
      """General procedure:
      
      1. Let machine decide how many samples to compute.
      2. Generate samples and weights.
      3. Compute samples on system
      """

      PrintMajorSection("Start iteration %d"%(len(self.iterations)))
      if iteration.finishedSteps:
         Print(green("Skipping finished steps of iteration:"))
         [Print("  "+i) for i in iteration.finishedSteps]

      iteration.RunStep(self,self.machine.AllocateResources,"Allocate resources",self.solverBatches)

      iteration.RunStep(self,self.GetNodesAndWeights,"Get samples")

      iteration.RunStep(self,self.solver.PrepareSimulations,"Prepare simulations",self.solverBatches,self.stochVars)

      iteration.RunStep(self,self.machine.RunBatches,"Run simulations",self.solverBatches,self.solver)

      iteration.RunStep(self,self.machine.PreparePostProc,"Prepare postprocessing",self.postprocBatches,self.solver)

      iteration.RunStep(self,self.machine.RunBatches,"Run postprocessing",self.postprocBatches,self.solver,postProc=True)

      if len(self.iterations) == self.nMaxIter:
         self.doContinue=False
         return

      iteration.RunStep(self,self.GetNewNCurrentSamples,"Get number of samples for next iteration")

      if self.doContinue:
         self.iterations.append(Iteration())

      return





class Iteration():
   
   def __init__(self):
      self.finishedSteps=[]

   def UpdateStep(self,uqMethod,string):
      self.finishedSteps.append(string)

      with open(uqMethod.filename, 'wb') as f:
         pickle.dump(uqMethod, f, 2)

   def RunStep(self,uqMethod,func,description,*args,**kwargs):
      if description not in self.finishedSteps:
         PrintStep(description+":")
         func(*args,**kwargs)
         self.UpdateStep(uqMethod,description)



# import subclasses
from . import *

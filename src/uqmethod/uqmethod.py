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

      PrintMajorSection("Last iteration finished. Exit loop. Start Post-Processing")
      # self.machine.runBatch(postprocSolver)
      PrintMajorSection("POUNCE Finished")


   def RunIteration(self,iteration):
      """General procedure:
      
      1. Let machine decide how many samples to compute.
      2. Generate samples and weights.
      3. Compute samples on system
      """

      # Prepare next iteration

      PrintMajorSection("Start iteration %d"%(len(self.iterations)))
      if iteration.finishedSteps:
         Print(green("Skipping finished steps of iteration:"))
         [Print("  "+i) for i in iteration.finishedSteps]

      iteration.RunStep("Get samples",
                        self.GetNodesAndWeights,
                        self)

      # Simulations 

      iteration.RunStep("Allocate resources",
                        self.machine.AllocateResources,
                        self,
                        self.solverBatches)

      iteration.RunStep("Prepare simulations",
                        self.solver.PrepareSimulations,
                        self,
                        self.solverBatches,self.stochVars)

      iteration.RunStep("Run simulations",
                        self.machine.RunBatches,
                        self,
                        self.solverBatches,self.solver)

      # Post-Processing

      iteration.RunStep("Allocate resources Postproc",
                        self.machine.AllocateResourcesPostproc,
                        self,
                        self.postprocBatches)

      iteration.RunStep("Prepare postprocessing",
                        self.solver.PreparePostprocessing,
                        self,
                        self.postprocBatches)

      iteration.RunStep("Run postprocessing",
                        self.machine.RunBatches,
                        self,
                        self.postprocBatches,self.solver,postProc=True)

      # Prepare next iteration

      if len(self.iterations) == self.nMaxIter:
         self.doContinue=False
         return

      iteration.RunStep("Get number of samples for next iteration",
                        self.GetNewNCurrentSamples,
                        self)

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

   def RunStep(self,description,func,uqMethod,*args,**kwargs):
      if description not in self.finishedSteps:
         PrintStep(description+":")
         func(*args,**kwargs)
         self.UpdateStep(uqMethod,description)



# import subclasses
from . import *

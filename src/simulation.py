import pickle

from helpers.printtools import *

class Simulation():

   def __init__(self):
      self.iterations=[Iteration()]
      self.filename = "pickle"
      self.doContinue = True

   def Run(self):
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
                        self.uqMethod.GetNodesAndWeights,
                        self)

      # Simulations 

      iteration.RunStep("Allocate resources",
                        self.machine.AllocateResources,
                        self,
                        self.uqMethod.solverBatches)

      iteration.RunStep("Prepare simulations",
                        self.solver.PrepareSimulations,
                        self,
                        self.uqMethod.solverBatches,self.uqMethod.stochVars)

      iteration.RunStep("Run simulations",
                        self.machine.RunBatches,
                        self,
                        self.uqMethod.solverBatches,self.solver)

      # Post-Processing

      iteration.RunStep("Allocate resources Postproc",
                        self.machine.AllocateResourcesPostproc,
                        self,
                        self.uqMethod.postprocBatches)

      iteration.RunStep("Prepare postprocessing",
                        self.solver.PreparePostprocessing,
                        self,
                        self.uqMethod.postprocBatches)

      iteration.RunStep("Run postprocessing",
                        self.machine.RunBatches,
                        self,
                        self.uqMethod.postprocBatches,self.solver,postProc=True)

      # Prepare next iteration

      if len(self.iterations) == self.uqMethod.nMaxIter:
         self.doContinue=False
         return

      iteration.RunStep("Get number of samples for next iteration",
                        self.uqMethod.GetNewNCurrentSamples,
                        self,
                        self.solver)

      if self.doContinue:
         self.iterations.append(Iteration())

      return



class Iteration():
   
   def __init__(self):
      self.finishedSteps=[]

   def UpdateStep(self,simulation,string):
      self.finishedSteps.append(string)
      with open(simulation.filename, 'wb') as f:
         pickle.dump(simulation, f, 2)

   def RunStep(self,description,func,simulation,*args,**kwargs):
      if description not in self.finishedSteps:
         PrintStep(description+":")
         func(*args,**kwargs)
         self.UpdateStep(simulation,description)

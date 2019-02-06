from helpers.baseclass import BaseClass

class UqMethod(BaseClass):

  def RunSimulation(self,machine,solver):
     """Main Loop for UQMethod.
          General procedure:
          1. Let machine decide how many samples to compute.
          2. Generate samples and weights.
          3. Compute samples on system

      Args:
          machine: class of machine, i.e. local, or computing cluster.
          solver: class of solver, i.e. flexi, or python solver.

     """
     iteration=0
     # main loop
     while True:
        # nSamples=machine.allocateRessources(solver.dofsPerCore)
        nSamples= [20,4]
        samples, weights=self.GetNodesAndWeights(nSamples)
        self.PrepareSimulation(samples,weights,solver)
        # machine.runBatch(solver)
        # machine.runBatch(postprocSolver)
        iteration+=1
        if(iteration==self.nMaxIter):
           break



from . import *

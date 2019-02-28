from .solver import Solver
import h5py
import numpy as np
from helpers.printtools import *

@Solver.RegisterSubclass('internal')
class SolverInternal(Solver):
   subclassDefaults={
      }

   def PrepareSimulations(self,batches,stochVars):
      """ Prepares the simulation by generating the runCommand 
      and writing the HDF5 file containing all samples of the current iteration
      and the current level.
      """
      for batch in batches:
         Print("Write HDF5 parameter file for simulation "+batch.name)
         batch.projectName = self.projectName+'_'+batch.name
         batch.h5PrmFileName = 'input_'+batch.projectName+'.h5'
         self.WriteHdf5(batch,stochVars)
         batch.runCommand='python3 '+self.exePaths["mainSolver"] + ' '+batch.h5PrmFileName

   def WriteHdf5(self,batch,stochVars):
      """ Writes the HDF5 file containing all necessary data for the internal 
      to run.
      """
      h5f = h5py.File(batch.h5PrmFileName, 'w')
      h5f.create_dataset('Samples', data=batch.samples.nodes)
      h5f.create_dataset('Weights', data=batch.samples.weights)
      h5f.attrs["nPrevious"] = batch.samples.nPrevious
      h5f.attrs["ProjectName"] = batch.projectName
      for key, value in batch.solverPrms.items():
         h5f.attrs[key] = value
      h5f.close()

   def PreparePostproc(self,postprocBatches):
      """ Prepares the postprocessing by generating the runPostprocCommand.
      """
      for postproc in postprocBatches: 
         names=[p.name for p in postproc.participants]
         Print("Generate Post-proc command for simulation(s) "+", ".join(names))
         postproc.runCommand = "python3 "+self.exePaths["iterationPostproc"]
         # this is a rather ugly current implementation
         postproc.projectName = postproc.participants[0].projectName
         for p in postproc.participants:
            postproc.runCommand=postproc.runCommand+' '+p.projectName+"_State.h5"

   def GetWorkMean(self,postproc):
      return self.GetPostprocQuantityFromFile(postproc,"WorkMean")

   def GetPostprocQuantityFromFile(self,postproc,quantityName):
      """ Readin sigmaSq for MLMC.
      """
      h5FileName = 'sums_'+postproc.participants[0].projectName+'.h5'
      h5f = h5py.File(h5FileName, 'r')
      quantity = h5f.attrs[quantityName]
      h5f.close()
      return quantity

   def CheckFinished(self,postproc):
      return True

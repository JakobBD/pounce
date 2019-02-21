from .solver import Solver
import h5py
import numpy as np
from helpers.printtools import *

@Solver.RegisterSubclass('internal')
class SolverInternal(Solver):
   subclassDefaults={
      "exeSimulationPath" : "NODEFAULT",
      "exePostprocessingPath" : "NODEFAULT",
      "projectName" : "NODEFAULT"
      }

   def PrepareSimulations(self,batches,stochVars):
      """ Prepares the simulation by generating the runCommand 
      and writing the HDF5 file containing all samples of the current iteration
      and the current level.
      """
      for batch in batches:
         Print("Write HDF5 parameter file for simulation "+batch.name)
         h5FileName = self.projectName+'_'+batch.name+'_StochInput.h5'
         self.WriteHdf5(batch,stochVars)
         batch.runCommand='python '+self.exeSimulationPath+ ' -f '+h5FileName

   def WriteHdf5(self,batch,stochVars):
      """ Writes the HDF5 file containing all necessary data for the internal 
      to run.
      """
      h5f = h5py.File(self.projectName+'_'+batch.name+'_StochInput.h5', 'w')
      h5f.create_dataset('Samples', data=batch.samples.nodes)
      h5f.create_dataset('Weights', data=batch.sampes.weights)
      h5f.attrs.create('StochVarNames', [var.name for var in stochVars], (len(stochVars),) )
      h5f.attrs["Projectname"] = self.projectName
      for key, value in batch.solverPrms.items():
         h5f.attrs[key] = value
      h5f.close()

   def PreparePostprocessing(self,fileNameSubStr):
      """ Prepares the postprocessing by generating the runPostprocCommand.
      """
      Print("Generate Post-proc command for simulation(s) "+", ".join(fileNameSubStr))
      runPostprocCommand=self.GeneratePostprocessingCommand(fileNameSubStr)
      return runPostprocCommand

   def GeneratePostprocessingCommand(self,fileNameSubStr):
      """ Generates the postprocessing command which is executed by the machine.
      """
      runPostprocCommand='python '+self.exePostprocessingPath+ ' -f '
      for subStrs in fileNameSubStr:
         runPostprocCommand=runPostprocCommand+self.projectName+'_'+subStrs+'_State.h5 '
      return runPostprocCommand

   def GetPostProcQuantityFromFile(self,fileNameSubStr,quantityName):
      """ Readin sigmaSq for MLMC.
      """
      h5FileName = self.projectName+'_'+fileNameSubStr+'_Postproc.h5'
      h5f = h5py.File(h5FileName, 'r')
      quantity = np.array(h5f[quantityName])
      h5f.close()
      return quantity

   def CheckFinished(self,batch):
      return True

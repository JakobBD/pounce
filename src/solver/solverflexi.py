from .solver import Solver
import h5py
from helpers.printtools import *

@Solver.RegisterSubclass('flexi')
class SolverFlexi(Solver):
   subclassDefaults={
      "exeSimulationPath" : "NODEFAULT",
      "exePostprocessingPath" : "NODEFAULT",
      "generalFilename" : "NODEFAULT",
      "prmfile": "NODEFAULT"
      }

   def PrepareSimulation(self,level,stochVars,fileNameSubStr,furtherAttrs):
      """ Prepares the simulation by generating the runCommand
      and writing the HDF5 file containing all samples of the current iteration
      and the current level.
      """
      Print("Write HDF5 parameter file for simulation "+fileNameSubStr)
      h5FileName = self.generalFilename+'_'+fileNameSubStr+'.h5'
      self.WriteHdf5(level,stochVars,fileNameSubStr,furtherAttrs)
      runCommand=self.GenerateRunCommand(h5FileName)
      return runCommand

   def GenerateRunCommand(self,h5FileName):
      """ Generates the run command which is executed by the machine.
      """
      runCommand = self.exeSimulationPath + ' ' + self.prmfile + ' ' + h5FileName \
                 + self.machine.nSequentialRuns + self.machine.nParallelRuns 
      return runCommand

   def WriteHdf5(self,level,stochVars,fileNameSubStr,furtherAttrs):
      """ Writes the HDF5 file containing all necessary data for flexi run
      to run.
      """
      h5f = h5py.File(self.generalFilename+'_'+fileNameSubStr+'_StochInput.h5', 'w')
      h5f.create_dataset('Samples', data=level.samples)
      h5f.create_dataset('Weights', data=level.weights)
      h5f.attrs.create('StochVars', [var.name for var in stochVars], (len(stochVars),) )
      h5f.attrs.create('iOccurrence', [var.GetiOccurrence() for var in stochVars], (len(stochVars),) )
      h5f.attrs.create('iPos', [var.GetiPos() for var in stochVars], (len(stochVars),) )
      h5f.attrs["Projectname"] = self.projectName
      for key, value in furtherAttrs.items():
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

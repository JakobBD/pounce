import h5py
import numpy as np
from .solver import Solver
from helpers.printtools import *

@Solver.RegisterSubclass('flexi')
class SolverFlexi(Solver):
   subclassDefaults={
      "exeSimulationPath" : "NODEFAULT",
      "exePostprocessingPath" : "NODEFAULT",
      "projectName" : "NODEFAULT",
      "generalFilename" : "NODEFAULT",
      "prmfile" : "NODEFAULT"
      }

   def PrepareSimulation(self,level,stochVars,fileNameSubStr,furtherAttrs):
      """ Prepares the simulation by generating the runCommand
      and writing the HDF5 file containing all samples of the current iteration
      and the current level.
      """
      Print("Write HDF5 parameter file for simulation "+fileNameSubStr)
      h5FileName = self.projectName+'_'+fileNameSubStr+'.h5'
      self.WriteHdf5(level,stochVars,fileNameSubStr,furtherAttrs)
      runCommand=self.GenerateRunCommand(h5FileName)
      return runCommand

   def GenerateRunCommand(self,h5FileName):
      """ Generates the run command which is executed by the machine.
      """
      runCommand = self.exeSimulationPath + ' ' + h5FileName + ' ' + self.prmfile

      return runCommand

   def WriteHdf5(self,level,stochVars,fileNameSubStr,furtherAttrs):
      """ Writes the HDF5 file containing all necessary data for flexi run
      to run.
      """
      h5f = h5py.File(self.projectName+'_'+fileNameSubStr+'.h5', 'w')
      h5f.create_dataset('Samples', data=level.samples)
      h5f.create_dataset('Weights', data=level.weights)
      h5f.attrs.create('StochVarNames', [var.name.ljust(255) for var in stochVars], (len(stochVars),), dtype='S255' )
      h5f.attrs.create('iOccurrence', [var.GetiOccurrence() for var in stochVars], (len(stochVars),) )
      h5f.attrs.create('iArray', [var.GetiPos() for var in stochVars], (len(stochVars),) )
      h5f.attrs["Projectname"] = self.projectName
      h5f.attrs["nStochVars"] = len(stochVars)
      h5f.attrs["nGlobalRuns"] = len(level.samples)
      # h5f.attrs["nParallelRuns"] = self.nParallelRuns
      h5f.attrs["nParallelRuns"] = 2
      levelVarsInt={}
      levelVarsString={}
      levelVarsReal={}
      for key, value in furtherAttrs.items():
         print(key,value)
         if(type(value)) is int and (key != 'Level'): levelVarsInt.update({key:value})
         if(type(value)) is str and (key != 'Sublevel'): levelVarsString.update({key:value})
         if(type(value)) is float: levelVarsReal.update({key:value})
      h5f.attrs["nLevelVarsInt"] = len(levelVarsInt)
      h5f.attrs["LevelVarsNamesInt"] = np.array([key for key in levelVarsInt], dtype='S')
      h5f.attrs["LevelVarsInt"] = [levelVarsInt.get(key) for key in levelVarsInt]
      h5f.attrs["nLevelVarsStr"] = len(levelVarsString)
      h5f.attrs["LevelVarsNamesStr"] = np.array([key for key in levelVarsString], dtype='S')
      h5f.attrs["LevelVarsStr"] = [levelVarsString.get(key) for key in levelVarsString]
      h5f.attrs["nLevelVarsReal"] = len(levelVarsReal)
      h5f.attrs["LevelVarsNamesReal"] = np.array([key for key in levelVarsReal], dtype='S')
      h5f.attrs["LevelVarsReal"] = [levelVarsReal.get(key) for key in levelVarsReal]

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
      """ Readin sigmaSq or avgWalltime for MLMC.
      """
      h5FileName = self.projectName+'_'+fileNameSubStr+'_Postproc.h5'
      h5f = h5py.File(h5FileName, 'r')
      quantity = np.array(h5f[quantityName])
      h5f.close()
      return quantity

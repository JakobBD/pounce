from .solver import Solver
import h5py
import numpy as np

@Solver.RegisterSubclass('internal')
class SolverInternal(Solver):
   subclassDefaults={
      "exeSimulationPath" : "NODEFAULT",
      "exePostprocessingPath" : "NODEFAULT"
      }

   def PrepareSimulation(self,level,stochVars,fileNameSubStr,furtherAttrs):
      h5FileName = self.projectName+'_'+fileNameSubStr+'_StochInput.h5'
      self.WriteHdf5(level,stochVars,fileNameSubStr,furtherAttrs)
      runCommand=self.GenerateRunCommand(h5FileName)
      return runCommand

   def GenerateRunCommand(self,h5FileName):
      runCommand='python '+self.exeSimulationPath+ ' -f '+h5FileName
      return runCommand

   def WriteHdf5(self,level,stochVars,fileNameSubStr,furtherAttrs):
      h5f = h5py.File(self.projectName+'_'+fileNameSubStr+'_StochInput.h5', 'w')
      h5f.create_dataset('Samples', data=level.samples)
      h5f.attrs.create('StochVars', [var.name for var in stochVars], (len(stochVars),) )
      h5f.attrs["Projectname"] = self.projectName
      for key, value in furtherAttrs.items():
         h5f.attrs[key] = value
      h5f.close()

   def PreparePostprocessing(self,fileNameSubStr):
      runPostprocCommand=self.GeneratePostprocessingCommand(fileNameSubStr)
      return runPostprocCommand

   def GeneratePostprocessingCommand(self,fileNameSubStr):
      runPostprocCommand='python '+self.exePostprocessingPath+ ' -f '
      for subStrs in fileNameSubStr:
         runPostprocCommand=runPostprocCommand+self.projectName+'_'+subStrs+'_State.h5 '
      return runPostprocCommand

   def GetSigmaSq(self,fileNameSubStr):
      h5FileName = self.projectName+'_'+fileNameSubStr+'_Postproc.h5'
      h5f = h5py.File(h5FileName, 'r')
      sigmaSq = np.array(h5f['sigmaSq'])
      h5f.close()
      return sigmaSq

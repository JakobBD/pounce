from .solver import Solver
import h5py
import numpy as np

@Solver.RegisterSubclass('internal')
class SolverInternal(Solver):
   subclassDefaults={
      "exePath" : "NODEFAULT"
      }

   def PrepareSimulation(self,level,sublevel,stochVars,fileNameSubStr,furtherAttrs):
      h5FileName = self.projectName+'_'+fileNameSubStr+'_StochInput.h5'
      self.WriteHdf5(level,stochVars,fileNameSubStr,furtherAttrs)
      self.GenerateRunCommand(sublevel,h5FileName)

   def GenerateRunCommand(self,sublevel,h5FileName):
      sublevel.runCommand='python '+self.exePath+ ' -f '+h5FileName

   def WriteHdf5(self,level,stochVars,fileNameSubStr,furtherAttrs):
      h5f = h5py.File(self.projectName+'_'+fileNameSubStr+'_StochInput.h5', 'w')
      h5f.create_dataset('Samples', data=level.samples)
      h5f.create_dataset('Weights', data=level.weights)
      h5f.attrs.create('StochVars', [var.name for var in stochVars], (len(stochVars),) )
      h5f.attrs["Projectname"] = self.projectName
      for key, value in furtherAttrs.items():
         h5f.attrs[key] = value
      h5f.close()

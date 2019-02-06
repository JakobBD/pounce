from .solver import Solver
import h5py
import numpy as np

@Solver.RegisterSubclass('internal')
class SolverInternal(Solver):

   def PrepareSimulation(self,level,stochVars,fileNameSubStr,furtherAttrs):
      self.WriteHdf5(level,stochVars,fileNameSubStr,furtherAttrs)
      # generateRunCommand(self)

   # def GenerateRunCommand(self):
      # self.runCommand='python '+self.exePath

   def WriteHdf5(self,level,stochVars,fileNameSubStr,furtherAttrs):
      h5f = h5py.File(self.projectName+'_'+fileNameSubStr+'_StochInput.h5', 'w')
      h5f.create_dataset('Samples', data=level.samples)
      h5f.create_dataset('Weights', data=level.weights)
      h5f.attrs.create('StochVars', [var.name for var in stochVars], (len(stochVars),) )
      for key, value in furtherAttrs.items(): 
         h5f.attrs[key] = value
      h5f.close()

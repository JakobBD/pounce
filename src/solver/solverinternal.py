from .solver import Solver
import h5py
import numpy as np

@Solver.RegisterSubclass('internal')
class SolverInternal(Solver):

   def Report(self):
      print("I am Internal")


   def PrepareSimulation(self,prepSimuDict):
      print prepSimuDict
      self.WriteHdf5(prepSimuDict)
      # generateRunCommand(self)

   # def GenerateRunCommand(self):
      # self.runCommand='python '+self.exePath

   def WriteHdf5(self,prepSimuDict):
      h5f = h5py.File(self.projectname+'_'+str(prepSimuDict["level"])+prepSimuDict["sublevel"]+'_StochInput.h5', 'w')
      h5f.create_dataset('Samples', data=np.transpose(prepSimuDict["samples"][:]))
      h5f.create_dataset('Weights', data=prepSimuDict["weights"])
      h5f.attrs.create('StochVars', prepSimuDict["varnames"], (len(prepSimuDict["varnames"]),))
      h5f.attrs['Level']    = prepSimuDict["level"]
      h5f.attrs['SubLevel'] = prepSimuDict["sublevel"]
      h5f.close()

import numpy as np

from .stochvar import StochVar

@StochVar.RegisterSubclass('uniform')
class StochVarUniform(StochVar):
   subclassDefaults={
      'bounds' : 'NODEFAULT'
      }

   def DrawSamples(self,nSamples):
      return np.random.uniform(self.bounds[0],self.bounds[1],nSamples)

   def GetDistribution(self,nSamples):
      return cp.Uniform(self.bounds[0],self.bounds[1])

import numpy as np
import chaospy as cp
from .stochvar import StochVar

@StochVar.RegisterSubclass('uniform')
class StochVarUniform(StochVar):
   subclassDefaults={
      'bounds' : 'NODEFAULT'
      }

   def DrawSamples(self,nSamples):
      return np.random.uniform(self.bounds[0],self.bounds[1],nSamples) if nSamples >0 else []

   def GetDistribution(self):
      return cp.Uniform(self.bounds[0],self.bounds[1])

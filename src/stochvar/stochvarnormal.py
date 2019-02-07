import numpy as np
import chaospy as cp
from .stochvar import StochVar

@StochVar.RegisterSubclass('normal')
class StochVarNormal(StochVar):
   subclassDefaults={
      'mean' : 'NODEFAULT',
      'standardDeviation' : 'NODEFAULT'
      }

   def DrawSamples(self,nSamples):
      return np.random.normal(self.mean,self.standardDeviation,nSamples)

   def GetDistribution(self,nSamples):
      return cp.Normal(self.mean,self.standardDeviation)

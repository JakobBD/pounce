import numpy as np
import chaospy as cp
from .stochvar import StochVar

@StochVar.RegisterSubclass('normal')
class StochVarNormal(StochVar):
   subclassDefaults={
      'mean' : 'NODEFAULT',
      'standardDeviation' : 'NODEFAULT',
      'iOccurrence': {},
      'iPos': {}
      }

   def DrawSamples(self,nSamples):
      return np.random.normal(self.mean,self.standardDeviation,nSamples) if nSamples >0 else []

   def GetDistribution(self):
      return cp.Normal(self.mean,self.standardDeviation)

   def GetiOccurrence(self):
      return self.iOccurrence

   def GetiPos(self):
      return self.iPos

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

   @property
   def distribution(self):
      return cp.Normal(self.mean,self.standardDeviation)

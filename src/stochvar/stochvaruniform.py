import numpy as np
import chaospy as cp
from .stochvar import StochVar

@StochVar.RegisterSubclass('uniform')
class StochVarUniform(StochVar):
   subclassDefaults={
      'bounds' : 'NODEFAULT',
      'iOccurrence': {},
      'iPos': {}
      }

   def DrawSamples(self,nSamples):
      return np.random.uniform(self.bounds[0],self.bounds[1],nSamples) if nSamples >0 else []

   @property
   def distribution(self):
      return cp.Uniform(self.bounds[0],self.bounds[1])

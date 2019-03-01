import numpy as np
import chaospy as cp
from .stochvar import StochVar

@StochVar.register_subclass('uniform')
class StochVarUniform(StochVar):
   subclass_defaults={
      'bounds' : 'NODEFAULT',
      'i_occurrence': {},
      'i_pos': {}
      }

   def draw_samples(self,n_samples):
      return np.random.uniform(self.bounds[0],self.bounds[1],n_samples) if n_samples >0 else []

   @property
   def distribution(self):
      return cp.Uniform(self.bounds[0],self.bounds[1])

import numpy as np
import chaospy as cp
from .stochvar import StochVar

@StochVar.register_subclass('normal')
class StochVarNormal(StochVar):
    subclass_defaults={
        'mean' : 'NODEFAULT',
        'standard_deviation' : 'NODEFAULT',
        'i_occurrence': {},
        'i_pos': {}
        }

    def draw_samples(self,n_samples):
        return np.random.normal(self.mean,self.standard_deviation,n_samples) if n_samples >0 else []

    @property
    def distribution(self):
        return cp.Normal(self.mean,self.standard_deviation)

    @property
    def parameters(self):
        return [self.mean, self.standard_deviation]

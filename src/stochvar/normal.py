import numpy as np
import chaospy as cp
from .stochvar import StochVar

@StochVar.register_subclass('normal')
class Normal(StochVar):
    subclass_defaults={
        'mean' : 'NODEFAULT',
        'standard_deviation' : 'NODEFAULT',
        'i_occurrence': {},
        'i_pos': {}
        }

    def __init__(self,input_prm_dict,*args):
        super().__init__(input_prm_dict,*args)
        self.distribution=cp.Normal(self.mean,self.standard_deviation)
        self.parameters = [self.mean, self.standard_deviation]

    def draw_samples(self,n_samples):
        return np.random.normal(self.mean,self.standard_deviation,n_samples) if n_samples >0 else []

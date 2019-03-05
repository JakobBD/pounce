import numpy as np
import chaospy as cp
from .stochvar import StochVar

@StochVar.register_subclass('uniform')
class Uniform(StochVar):
    subclass_defaults={
        'bounds' : 'NODEFAULT',
        'i_occurrence': {},
        'i_pos': {}
        }

    def __init__(self,input_prm_dict,*args):
        super().__init__(input_prm_dict,*args)
        self.distribution= cp.Uniform(self.bounds[0],self.bounds[1])
        self.parameters = self.bounds

    def draw_samples(self,n_samples):
        return np.random.uniform(self.bounds[0],self.bounds[1],n_samples) if n_samples >0 else []

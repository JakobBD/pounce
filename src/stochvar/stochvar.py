import numpy as np
import chaospy as cp
from helpers.baseclass import BaseClass

class StochVar(BaseClass):
    """
    parent class for stochastic variables
    """
    pass

class Normal(StochVar):
    """
    normal distribution
    uses numpy and chaospy routines
    """

    defaults_ = {
        'mean' : 'NODEFAULT',
        'standard_deviation' : 'NODEFAULT',
        }

    def __init__(self,input_prm_dict,*args):
        super().__init__(input_prm_dict,*args)
        self.distribution=cp.Normal(self.mean,self.standard_deviation)
        self.parameters = [self.mean, self.standard_deviation]

    def draw_samples(self,n_samples):
        return np.random.normal(self.mean,self.standard_deviation,n_samples) \
               if n_samples >0 else []


class Uniform(StochVar):
    """
    uniform distribution
    uses numpy and chaospy routines
    """

    defaults_ = {
        'bounds' : 'NODEFAULT'
        }

    def __init__(self,input_prm_dict,*args):
        super().__init__(input_prm_dict,*args)
        self.distribution= cp.Uniform(self.bounds[0],self.bounds[1])
        self.parameters = self.bounds

    def draw_samples(self,n_samples):
        return np.random.uniform(self.bounds[0],self.bounds[1],n_samples) \
               if n_samples >0 else []

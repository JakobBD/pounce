import chaospy as cp
import numpy as np

from helpers.baseclass import BaseClass
from helpers.printtools import *


class Sampling(BaseClass):
    """
    parent class with placeholders for the sampling strategies
    """

    def get(self):
        """
        get samples
        """
        pass

    def sampling_prms(self):
        """
        parameters specific to the sampling strategy which are
        needed by the solver or by the post-processing routines
        """
        return {}

    @property
    def n_total_current(self): 
        return self.n_previous + self.n


class MonteCarlo(Sampling):
    """
    Vanilla Monte Carlo sampling
    """
    defaults_={
        "fixed_seed": False,
        "seed_offset": 0
        }

    def get(self):
        if self.fixed_seed: 
            self.nodes=np.empty((self.n,len(self.stoch_vars)))
            for i_var, var in enumerate(self.stoch_vars):
                for i_sample in range(self.n):
                    # max random seed is about 4e9 
                    # gives unique seed for up to 1e6 samples, 100 stoch vars and 40 batches.
                    seed = int(1e8)*self.seed_id + int(1e2)*(i_sample+self.n_previous) + i_var + self.seed_offset
                    np.random.seed(seed)
                    self.nodes[i_sample,i_var] = var.draw_samples(1)
        else: 
            self.nodes=[]
            for var in self.stoch_vars:
                self.nodes.append(var.draw_samples(self.n))
            self.nodes=np.transpose(self.nodes)

    # to be precise, one could add a class 
    # IterativeMonteCarlo(MonteCarlo) here
    def sampling_prms(self):
        return {"nPreviousRuns":self.n_previous}


class GaussianQuadrature(Sampling):
    """
    Sampling at Gaussian collocation nodes based on ChaosPy routines
    Smolyak sparse grid is possible
    """
         
    defaults_={
        "poly_deg": "NODEFAULT",
        "sparse_grid" : "NODEFAULT"
        }

    def get(self):
        distributions=[var.distribution for var in self.stoch_vars]
        nodes,self.weights = \
            cp.generate_quadrature(self.poly_deg,
                                   cp.J(*distributions),
                                   rule='G',
                                   sparse=self.sparse_grid)
        self.nodes=np.transpose(nodes)
        self.n = len(self.nodes)

    def sampling_prms(self):
        """
        For mean and variance, only weights would be used. 
        The rest is for response surface creation.
        """
        return({
            'Weights'          : self.weights,
            'Distributions'    : [i._type        for i in self.stoch_vars],
            'DistributionProps': [i.parameters   for i in self.stoch_vars],
            "polyDeg"          : self.poly_deg
            })


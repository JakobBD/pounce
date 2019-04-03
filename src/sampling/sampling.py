import chaospy as cp
import numpy as np

from helpers.baseclass import BaseClass
from helpers.printtools import *


class Sampling(BaseClass):

    def get_samples(self,levels):
        pass


class MonteCarlo(Sampling):

    defaults_={
        "reset_seed" : False
        }

    def get_samples(self,levels):
        for level in levels:
            level.samples.nodes=[]
            for var in self.stoch_vars:
                level.samples.nodes.append(var.draw_samples(level.samples.n))
            level.samples.nodes=np.transpose(level.samples.nodes)
        p_print("Number of current samples for this iteration:")
        for level in levels:
            p_print("  Level %2s: %6d samples"%(level.name,level.samples.n))


class Collocation(Sampling):
         
    defaults_={
        "sparse_grid" : "NODEFAULT"
        }

    def get_samples(self,levels):
        distributions=[var.distribution for var in self.stoch_vars]
        for level in levels:
            nodes,level.samples.weights = \
                cp.generate_quadrature(level.poly_deg,
                                       cp.J(*distributions),
                                       rule='G',
                                       sparse=self.sparse_grid)
            level.samples.nodes=np.transpose(nodes)
            level.samples.n = len(level.samples.nodes)
        p_print("Number of current samples for this iteration:")
        for level in levels:
            p_print("  Level %2s: %6d samples"%(level.name,level.samples.n))

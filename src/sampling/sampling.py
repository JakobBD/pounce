import chaospy as cp
import numpy as np

from helpers.baseclass import BaseClass
from helpers.printtools import *


class Sampling(BaseClass):

    def get_samples(self,batches):
        pass


class MonteCarlo(Sampling):

    defaults_={
        "reset_seed" : False
        }

    def get_samples(self,batches):
        for batch in batches:
            batch.samples.nodes=[]
            for var in self.stoch_vars:
                batch.samples.nodes.append(var.draw_samples(batch.samples.n))
            batch.samples.nodes=np.transpose(batch.samples.nodes)
        p_print("Number of current samples for this iteration:")
        for batch in batches:
            p_print("  Level %2s: %6d samples"%(batch.name,batch.samples.n))


class Collocation(Sampling):
         
    defaults_={
        "sparse_grid" : "NODEFAULT"
        }

    def get_samples(self,batches):
        distributions=[var.distribution for var in self.stoch_vars]
        for batch in batches:
            nodes,batch.samples.weights = \
                cp.generate_quadrature(batch.poly_deg,
                                       cp.J(*distributions),
                                       rule='G',
                                       sparse=self.sparse_grid)
            batch.samples.nodes=np.transpose(nodes)
            batch.samples.n = len(batch.samples.nodes)
        p_print("Number of current samples for this iteration:")
        for batch in batches:
            p_print("  Level %2s: %6d samples"%(batch.name,batch.samples.n))

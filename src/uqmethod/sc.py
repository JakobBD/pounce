import chaospy as cp
import numpy as np

from .uqmethod import UqMethod
from helpers.printtools import *
from helpers.tools import *

class Sc(UqMethod):

    defaults_ = {
        "sparse_grid" : "NODEFAULT"
        }

    defaults_add = { 
        "Level": {
            "poly_deg": "NODEFAULT",
            'solver_prms' : {}
            }
        }

    def __init__(self,input_prm_dict):
        super().__init__(input_prm_dict)
        self.has_simulation_postproc=False
        self.n_max_iter=1

    def setup_batches(self,qois):
        for i_level,level in enumerate(self.levels):
            level.name=str(i_level+1)
            level.samples=Empty()
            level.samples.n_previous = 0
            level.qois=[copy.deepcopy(qoi) for qoi in qois]
            for qoi in level.qois:
                qoi.participants=[level]
                qoi.name="postproc_"+level.name
                qoi.avg_walltime=level.avg_walltime_postproc
                qoi.prepare=qoi.prepare_iter_postproc
        self.solver_batches=self.levels
        self.postproc_batches = \
            [qoi for level in self.levels for qoi in level.qois]

    def get_nodes_and_weights(self):
        distributions=[var.distribution for var in self.stoch_vars]
        for level in self.levels:
            nodes,level.samples.weights = \
                cp.generate_quadrature(level.poly_deg,
                                       cp.J(*distributions),
                                       rule='G',
                                       sparse=self.sparse_grid)
            level.samples.nodes=np.transpose(nodes)
            level.samples.n = len(level.samples.nodes)
        p_print("Number of current samples for this iteration:")
        for level in self.levels:
            p_print("  Level %2s: %6d samples"%(level.name,level.samples.n))


    def prm_dict_add(self,level):
        return({
            'Weights'          : level.samples.weights,
            'Distributions'    : [i._type        for i in self.stoch_vars],
            'DistributionProps': [i.parameters   for i in self.stoch_vars],
            "polyDeg"          : level.poly_deg
            })

    def get_new_n_samples(self,solver):
        raise Exception("the GetNewNSamples routine should not be called for"
                        " stochastic collocation")


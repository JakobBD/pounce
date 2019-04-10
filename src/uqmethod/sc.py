from .uqmethod import UqMethod
from helpers.printtools import *
from helpers.tools import *
from sampling.sampling import Collocation

class Sc(UqMethod, Collocation):

    defaults_add = { 
        "Level": {
            "poly_deg": "NODEFAULT",
            'solver_prms': {}
            }
        }

    def __init__(self, input_prm_dict):
        super().__init__(input_prm_dict)
        self.has_simulation_postproc = False
        self.n_max_iter = 1

    def setup(self, qois):
        for i_level,level in enumerate(self.levels):
            level.name = str(i_level+1)
            level.samples = Empty()
            level.samples.n_previous = 0
            level.qois = [copy.deepcopy(qoi) for qoi in qois]
            for qoi in level.qois:
                qoi.participants = [level]
                qoi.name = "postproc_"+level.name
                qoi.avg_walltime = level.avg_walltime_postproc
                qoi.prepare = qoi.prepare_iter_postproc
        self.solver_batches = self.levels
        self.postproc_batches = \
            [qoi for level in self.levels for qoi in level.qois]

    def prm_dict_add(self, level):
        return({
            'Weights'          : level.samples.weights,
            'Distributions'    : [i._type        for i in self.stoch_vars],
            'DistributionProps': [i.parameters   for i in self.stoch_vars],
            "polyDeg"          : level.poly_deg
            })

    def get_new_n_samples(self, solver):
        raise Exception("the GetNewNSamples routine should not be called for"
                        " stochastic collocation")


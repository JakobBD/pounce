from .uqmethod import UqMethod
from helpers.printtools import *
from helpers.tools import *
from sampling.sampling import Collocation
from solver.solver import Solver
from machine.machine import Machine
from stochvar.stochvar import StochVar
from helpers import config
from helpers import globels

class Sc(UqMethod, Collocation):

    defaults_add = { 
        "Solver": {
            "poly_deg": "NODEFAULT",
            'solver_prms': {}
            }
        }

    def __init__(self, input_prm_dict):
        super().__init__(input_prm_dict)
        self.has_simulation_postproc = False
        self.n_max_iter = 1

    def setup(self, prms):

        SolverLoc = Solver.subclass(prms["solver"]["_type"])
        MachineLoc = Machine.subclass(prms["machine"]["_type"])

        # initialize StochVars
        self.stoch_vars = config.config_list("stoch_vars", prms, StochVar.create,
                                             SolverLoc)

        # initialize lists of classes for all levels, stoch_vars and qois
        self.solver = Solver.create(prms["solver"], self, MachineLoc)

        self.stages = [Machine.create(prms["machine"])]
        self.stages[0].fill("simulation", True)
        self.stages[0].batches = [self.solver]
        if "machine_postproc" in prms: 
            MachineLoc = Machine.subclass("local")
            sub_dict = prms["machine_postproc"]
        else: 
            sub_dict = prms["machine"]

        self.postproc = MachineLoc(sub_dict)
        self.postproc.fill("postproc", False)

        self.solver.name = ""
        self.solver.samples = Empty()
        for sub_dict in prms["qois"]: 
            qoi = SolverLoc.QoI.create_by_stage("iteration_postproc",sub_dict, self)
            qoi.participants = [self.solver]
            qoi.name = "postproc"
            self.postproc.batches.append(qoi)

    @staticmethod
    def default_yml(d):
        d.get_machine()
        solver = d.process_subclass(Solver)
        d.all_defaults["qois"] = d.get_list_defaults(solver.QoI)

    def prm_dict_add(self, solver):
        return({
            'Weights'          : solver.samples.weights,
            'Distributions'    : [i._type        for i in self.stoch_vars],
            'DistributionProps': [i.parameters   for i in self.stoch_vars],
            "polyDeg"          : solver.poly_deg
            })

    def get_new_n_current_samples(self, solver):
        pass
        # raise Exception("the GetNewNSamples routine should not be called for"
                        # " stochastic collocation")


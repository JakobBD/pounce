from .uqmethod import UqMethod
from helpers.printtools import *
from helpers.tools import *
from sampling.sampling import Collocation
from solver.solver import Solver
from machine.machine import Machine
from stochvar.stochvar import StochVar
from helpers import config
from helpers import globels

class Sc(UqMethod):
    """
    Stochastic Collocation (non-adaptive)
    """

    SamplingMethod = Collocation

    def __init__(self, input_prm_dict):
        super().__init__(input_prm_dict)
        self.has_simulation_postproc = False
        self.n_max_iter = 1

    def setup(self, prms):
        """
        Only one batch is needed (called solver)
        """

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

        self.stages.append(MachineLoc(sub_dict))
        self.stages[1].fill("postproc", False)

        self.solver.name = ""
        self.solver.samples = Collocation(prms["sampling"])
        self.solver.samples.stoch_vars = self.stoch_vars
        for sub_dict in prms["qois"]: 
            qoi = SolverLoc.QoI.create_by_stage("iteration_postproc",sub_dict, self)
            qoi.participants = [self.solver]
            qoi.name = "postproc"
            self.stages[1].batches.append(qoi)

    def prepare_next_iteration(self):
        """
        There is only one "iteration", so no next 
        one needs to be prepared.
        """
        pass

    @classmethod
    def default_yml(cls,d):
        super().default_yml(d)
        d.all_defaults["sampling"] = cls.SamplingMethod.defaults(with_type=False)

from prettytable import PrettyTable
import numpy as np

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

    cname = "sc"

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

        # initialize StochVars
        self.stoch_vars = config.config_list("stoch_vars", prms, StochVar.create,
                                             SolverLoc)
        
        self.samples = Collocation(prms["sampling"])
        self.samples.stoch_vars = self.stoch_vars

        for i_stage, stage in enumerate(self.stages): 
            solver = Solver.create_by_stage_from_list(prms["solver"],i_stage,
                                                         stage.name,self,stage.__class__)
            solver.name = "sc"
            solver.samples = self.samples
            stage.batches = [solver]

        postproc = config.config_pp_mach(prms,self,"postproc")
        self.stages.append(postproc)


        self.internal_qois = []
        for sub_dict in prms["qois"]: 
            qoi = SolverLoc.QoI.create_by_stage(sub_dict,"iteration_postproc",self)
            qoi.participants = self.stages[-2].batches
            if qoi.internal: 
                self.internal_qois.append(qoi)
            else: 
                self.stages[-1].batches.append(qoi)

    def prepare_next_iteration(self):
        """
        There is only one "iteration", so no next 
        one needs to be prepared.
        """
        self.internal_iteration_postproc()

    def internal_iteration_postproc(self): 
        table = PrettyTable()
        table.field_names = ["QoI","Mean","Standard Deviation"]
        for qoi in self.internal_qois: 
            u_out = qoi.get_response()[0]
            n = self.samples.n
            qoi.mean = np.dot(np.transpose(u_out),self.samples.weights)
            qoi.stddev = np.sqrt(np.dot(np.transpose(u_out**2),self.samples.weights) - qoi.mean**2.)
            if isinstance(qoi.mean,(float,np.float)):
                table.add_row([qoi.cname,qoi.mean,qoi.stddev])
            else:
                table.add_row([qoi.cname + " (Int.)",
                               qoi.integrate(qoi.mean),
                               np.sqrt(qoi.integrate(qoi.stddev**2))])
            qoi.write_to_file()
        self.mean = self.internal_qois[0].mean
        self.stddev = self.internal_qois[0].stddev
        print_table(table)


    @classmethod
    def default_yml(cls,d):
        super().default_yml(d)
        d.all_defaults["sampling"] = cls.SamplingMethod.defaults(with_type=False)

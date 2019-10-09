import numpy as np
import os
import copy

from .uqmethod import UqMethod
from helpers.printtools import *
from helpers.tools import *
from sampling.sampling import MonteCarlo
from solver.solver import Solver
from machine.machine import Machine
from stochvar.stochvar import StochVar
from helpers import config


class Mlmc(UqMethod):

    defaults_ = {
        "n_max_iter" : "NODEFAULT",
        "tolerance" : None,
        "total_work" : None,
        "reset_seed" : False
        }

    defaults_add = { 
        "Solver": { 
            "n_warmup_samples": "NODEFAULT"
            },
        "QoI": {
            "optimize": False,
            }
        }

    SamplingMethod = MonteCarlo

    def __init__(self, input_prm_dict):
        super().__init__(input_prm_dict)
        if bool(self.tolerance) == bool(self.total_work): 
            raise Exception("MLMC: Prescribe either tolerance or total_work")
        self.has_simulation_postproc = True
        if self.reset_seed:
            p_print("Reset RNG seed to 0")
            np.random.seed(0)

    def setup(self, prms):

        SolverLoc = Solver.subclass(prms["solver"]["_type"])
        MachineLoc = Machine.subclass(prms["machine"]["_type"])

        # initialize StochVars
        self.stoch_vars = config.config_list("stoch_vars", prms, StochVar.create,
                                             SolverLoc)

        # initialize sublevels
        subs_fine = config.config_list("solver", prms, Solver.create, 
                                       self, MachineLoc, sub_list_name="levels")
        subs_coarse=[Empty()]
        subs_coarse.extend(copy.deepcopy(subs_fine[:-1]))
        # initialize levels and connect to sublevels
        iterator=zip(range(1,len(subs_fine)+1),subs_fine,subs_coarse)
        self.levels = [self.setup_level(*args) for args in iterator]

        #setup stages 
        main_simu = MachineLoc(prms["machine"])
        main_simu.fill("simulation", True)
        main_simu.batches = []
        for level in self.levels:
            main_simu.batches.extend(level.sublevels)
        if "machine_postproc" in prms: 
            MachineLoc = Machine.subclass("local")
            sub_dict = prms["machine_postproc"]
        else: 
            sub_dict = prms["machine"]
        iter_postproc = MachineLoc(sub_dict)
        iter_postproc.fill("iteration_postproc", False)
        self.stages = [main_simu, iter_postproc]
        self.simulation_postproc = MachineLoc(sub_dict)
        self.simulation_postproc.fill("simulation_postproc", False)

        self.qois_optimize = []
        for level in self.levels:
            level.n_optimize = 0
            level.qois = []
            for sub_dict in prms["qois"]: 
                self.setup_qoi(sub_dict,level)
            if level.n_optimize != 1: 
                raise Exception("Please specify exactly "
                                "one QoI to optimize")

        for i,sub_dict in enumerate(prms["qois"]): 
            QoILoc = Solver.subclass(prms["solver"]["_type"]).QoI
            qoi = QoILoc.create_by_stage("simulation_postproc",sub_dict,self)
            qoi.name = "combinelevels"
            qoi.participants = [l.qois[i] for l in self.levels]
            self.simulation_postproc.batches.append(qoi)

    def setup_level(self, i, sub_fine, sub_coarse):
        level=Empty()
        level.name = str(i)
        level.samples = MonteCarlo({})
        level.samples.stoch_vars = self.stoch_vars
        level.samples.n = sub_fine.n_warmup_samples
        level.samples.n_previous = 0
        sublevels = [sub_fine, sub_coarse]
        for sub, sub_name in zip(sublevels,['f', 'c']):
            sub.samples = level.samples
            sub.name = level.name+sub_name
        if i == 1:
            sublevels = [sub_fine]
        level.sublevels = sublevels
        return level

    def setup_qoi(self, subdict, level):
        QoILoc = level.sublevels[0].__class__.QoI
        qoi = QoILoc.create_by_stage("iteration_postproc",subdict, self)
        qoi.participants = level.sublevels
        qoi.name = "postproc_"+level.name

        qoi.samples = level.samples
        if qoi.optimize: 
            level.n_optimize += 1
            self.qois_optimize.append(qoi)
        level.qois.append(qoi)
        self.stages[1].batches.append(qoi)


    @classmethod
    def default_yml(cls,d):
        super().default_yml(d)
        d.all_defaults["solver"] = d.expand_to_several(
            sub = d.all_defaults["solver"], 
            list_name = "levels", 
            exclude = ["_type","exe_path"])
        for i,sub in enumerate(d.all_defaults["qois"]):
            d.all_defaults["qois"][i] = d.expand_to_several(
                sub = sub, 
                list_name = "stages", 
                keys = ["iteration_postproc","simulation_postproc"], 
                exclude = ["_type","optimize"])

    def get_new_n_current_samples(self):

        stdout_table = StdOutTable("sigma_sq","work_mean","mlopt_rounded",
                                   "samples__n_previous","samples__n")
        stdout_table.set_descriptions("SigmaSq","mean work","ML_opt",
                                      "finished Samples","new Samples")

        # build sum over levels of sqrt(sigma^2/w)
        sum_sigma_w = 0.
        for qoi in self.qois_optimize:
            if qoi.samples.n > 0:
                qoi.sigma_sq = float(qoi.get_derived_quantity("SigmaSq"))
                work_mean = qoi.get_work_mean()
                if qoi.samples.n_previous > 0:
                    qoi.work_mean = ((qoi.samples.n_previous*qoi.work_mean
                                      + qoi.samples.n*work_mean)
                                     / (qoi.samples.n+qoi.samples.n_previous))
                else:
                    qoi.work_mean = work_mean
            if qoi.samples.n_previous+qoi.samples.n > 0:
                sum_sigma_w += safe_sqrt(qoi.sigma_sq*qoi.work_mean)

        for qoi in self.qois_optimize:
            if self.tolerance: 
                qoi.mlopt = (sum_sigma_w
                             * safe_sqrt(qoi.sigma_sq/qoi.work_mean)
                             / (self.tolerance*self.tolerance/4.))
            elif self.total_work: 
                qoi.mlopt = (self.total_work
                             * safe_sqrt(qoi.sigma_sq/qoi.work_mean)
                             / sum_sigma_w)
            qoi.mlopt_rounded = int(round(qoi.mlopt)) if qoi.mlopt > 1 \
                else qoi.mlopt
            qoi.samples.n_previous += qoi.samples.n

            # slowly approach mlopt... heuristic solution
            n_iter_remain = self.n_max_iter-self.current_iter.n
            if n_iter_remain > 0: 
                expo = 1./sum(0.15**i for i in range(n_iter_remain))
                n_total_new = qoi.mlopt**expo * qoi.samples.n**(1-expo)
                qoi.samples.n = \
                    max(int(np.ceil(n_total_new))-qoi.samples.n_previous , 0)
            else: 
                qoi.samples.n = 0

            stdout_table.update(qoi)

        stdout_table.p_print()

        print()
        if self.tolerance: 
            self.est_total_work = sum(
                [q.work_mean*max(q.mlopt, q.samples.n_previous) \
                    for q in self.qois_optimize])
            p_print("Estimated required total work to achieve prescribed "
                    "tolerance: %d core-seconds"%(int(self.est_total_work)))
        elif self.total_work: 
            self.est_tolerance = sum(
                [q.sigma_sq/max(q.mlopt, q.samples.n_previous) \
                    for q in self.qois_optimize])
            p_print("Estimated achieved tolerance for given total work: %e" \
                    %(2.*np.sqrt(self.est_tolerance)))

        self.iter_loop_finished = len(self.stages[0].active_batches) == 0




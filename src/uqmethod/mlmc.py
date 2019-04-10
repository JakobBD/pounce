import numpy as np
import os
import copy

from .uqmethod import UqMethod
from helpers.printtools import *
from helpers.tools import *
from sampling.sampling import MonteCarlo
from solver.solver import Solver
from machine.machine import Machine
from level.level import Level
from helpers import config


class Mlmc(UqMethod,MonteCarlo):

    defaults_ = {
        "n_max_iter" : "NODEFAULT",
        "tolerance" : None,
        "total_work" : None
        }

    defaults_add = { 
        "Level": {
            "n_warmup_samples": "NODEFAULT",
            "solver_prms" : {},
            },
        "QoI": {
            "exe_paths": {
                "iteration_postproc": "",
                "simulation_postproc": ""
                },
            "optimize": False,
            "avg_walltime_combinelevels": 300.
            }
        }

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
        LocMachine = Machine.subclass(prms["machine"]["_type"])

        # initialize lists of classes for all levels, stoch_vars and qois
        self.levels = config.config_list("levels", prms, Level, 
                                         self, LocMachine)

        self.main_simulation = LocMachine(prms["machine"])
        self.main_simulation.fill("simulation", True)
        if "machine_postproc" in prms: 
            LocMachine = Machine.subclass("local")
            sub_dict = prms["machine_postproc"]
        else: 
            sub_dict = prms["machine"]

        self.iteration_postproc = LocMachine(sub_dict)
        self.iteration_postproc.fill("iteration_postproc", False)
        self.simulation_postproc = LocMachine(sub_dict)
        self.simulation_postproc.fill("simulation_postproc", False)

        self.qois_optimize = []
        for i_level,level in enumerate(self.levels):
            level.name = str(i_level+1)
            level.samples = Empty()
            level.samples.n = level.n_warmup_samples
            level.samples.n_previous = 0
            level.sublevels = []
            self.setup_sublevel(prms, level, level,'f')
            if i_level > 0:
                self.setup_sublevel(prms, level, self.levels[i_level-1], 'c')
            level.n_optimize = 0
            level.qois = []
            for sub_dict in prms["qois"]: 
                self.setup_qoi(sub_dict,SolverLoc,level)
            if level.n_optimize != 1: 
                raise Exception("Please specify exactly "
                                "one QoI to optimize")

        for i,sub_dict in enumerate(prms["qois"]): 
            qoi = SolverLoc.QoI.create(sub_dict,self)
            qoi.name = "combinelevels"
            qoi.avg_walltime = qoi.avg_walltime_combinelevels
            qoi.participants = [l.qois[i] for l in self.levels]
            qoi.prepare = qoi.prepare_simu_postproc
            self.simulation_postproc.batches.append(qoi)



    def setup_sublevel(self, prms, diff_level, resolution_level, name):
        sub = Solver.create(prms["solver"])

        sub.solver_prms = resolution_level.solver_prms
        sub.cores_per_sample = resolution_level.cores_per_sample
        sub.avg_walltime = resolution_level.avg_walltime

        sub.samples = diff_level.samples
        sub.name = diff_level.name+name

        sub.prepare = sub.prepare_simulations

        diff_level.sublevels.append(sub)
        self.main_simulation.batches.append(sub)

    def setup_qoi(self, subdict, SolverLoc, level):
        qoi = SolverLoc.QoI.create(subdict, self)
        qoi.participants = level.sublevels
        qoi.name = "postproc_"+level.name
        qoi.avg_walltime = level.avg_walltime_postproc

        qoi.prepare = qoi.prepare_iter_postproc
        qoi.samples = level.samples
        if qoi.optimize: 
            level.n_optimize += 1
            self.qois_optimize.append(qoi)
        level.qois.append(qoi)
        self.iteration_postproc.batches.append(qoi)


    @staticmethod
    def default_yml(d):
        d.get_machine()
        solver = d.process_subclass(Solver)
        d.all_defaults["levels"] = [Level.defaults(*d.subclasses)]
        d.all_defaults["qois"] = d.get_list_defaults(solver.QoI)


    def prm_dict_add(self, sublevel):
        return {"nPreviousRuns":sublevel.samples.n_previous}


    def get_new_n_current_samples(self, n_iter):

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
            n_iter_remain = self.n_max_iter-n_iter
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

        self.do_continue = len(self.main_simulation.active()) > 0




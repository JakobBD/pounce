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


# TODO: 
# - get work for model, not for qoi 
# - fix qoi_optimize vs. all qois 
# - slightly nicer stdout 
# - rename check_all_finished
# - default yml
# - update estimates for rho, alpha and estimated MSE



class Mfmc(UqMethod):
    """
    Multilevel Monte Carlo
    The number of levels is prescribed, the number of samples is 
    adapted iteratively in a prescribed number of iterations
    (convergence rate and work per sample are obtained empirically).
    """

    defaults_ = {
        # "tolerance" : None,
        "total_work" : "NODEFAULT",
        "n_warmup_samples": "NODEFAULT",
        "reset_seed" : False
        }

    defaults_add = { 
        "Solver": { 
            "name": "NODEFAULT"
            },
        "QoI": {
            "optimize": False,
            }
        }

    SamplingMethod = MonteCarlo

    def __init__(self, input_prm_dict):
        super().__init__(input_prm_dict)
        self.has_simulation_postproc = True
        if self.reset_seed:
            p_print("Reset RNG seed to 0")
            np.random.seed(0)
        self.n_max_iter = 2
        self.has_simulation_postproc = False

    def setup(self, prms):
        """
        Set up data structure for an MLMC simulation
        Includes levels and sublevels, quantities of interest, 
        each initiallized according to chosen solver, 
        and stages (main simulation and post proc) according to
        chosen machine.
        """

        # TODO!!!!!!!!!!
        SolverLoc = Solver.subclass(prms["models"]["_type"])
        MachineLoc = Machine.subclass(prms["machine"]["_type"])

        # initialize StochVars
        self.stoch_vars = config.config_list("stoch_vars", prms, StochVar.create,
                                             SolverLoc)

        # initialize sublevels
        self.models = config.config_list("models", prms, Solver.create, 
                                    self, MachineLoc, sub_list_name="fidelities")
        for model in self.models: 
            model.samples = Empty()
            model.samples.n = self.n_warmup_samples
            model.samples.n_previous = 0
            model.samples.stoch_vars = self.stoch_vars
            model.internal_qois = []
        self.hfm = self.models[0]
        self.sampling = MonteCarlo({})
        self.sampling.nodes_all = np.empty((0,len(self.stoch_vars)))
        self.sampling.stoch_vars = self.stoch_vars

        #setup stages 
        main_simu = MachineLoc(prms["machine"])
        main_simu.fill("simulation", True)
        main_simu.batches = self.models
        self.stages = [main_simu]

        self.qois_optimize = []
        for model in self.models:
            model.n_optimize = 0
            model.qois = []
            for sub_dict in prms["qois"]: 
                self.setup_qoi(sub_dict,model)
            if model.n_optimize != 1: 
                raise Exception("Please specify exactly "
                                "one QoI to optimize")

                self.internal_qois = [] #TODO: needed?


    def setup_qoi(self, subdict, model):
        """ 
        set up quantity of interest for a model and make the 
        sublevels its participants
        """
        QoILoc = model.__class__.QoI
        qoi = QoILoc.create_by_stage("iteration_postproc",subdict, self)
        qoi.participants = [model]
        qoi.name = qoi.__class__.name()+"_"+model.name
        qoi.samples = model.samples
        if qoi.optimize: 
            model.n_optimize += 1
            self.qois_optimize.append(qoi)
            model.qoi_opt = qoi
        model.qois.append(qoi)
        model.internal_qois.append(qoi)
        qoi.u_sum      = 0.
        qoi.u_sq_sum   = 0.
        qoi.u_uhfm_sum = 0.


    def get_samples(self,dummy):
        """
        Overwritten. 
        samples are only drawn once, and then distributed to the models.
        """
        self.sampling.n = np.max([m.samples.n for m in self.models])
        if self.sampling.n > 0: 
            self.sampling.get()
        self.sampling.nodes_all = np.concatenate((self.sampling.nodes_all, self.sampling.nodes))
        for m in self.models: 
            limit_l = m.samples.n_previous
            limit_u = m.samples.n_previous + m.samples.n + 1
            m.samples.nodes = self.sampling.nodes_all[limit_l:limit_u]


    @staticmethod
    def get_rho(n,qoi,qoi_hfm):
        qoi.u_sum      = np.sum(qoi.u)
        qoi.u_sq_sum   = np.sum(qoi.u**2)
        qoi.u_uhfm_sum = np.sum(qoi.u*qoi_hfm.u)

        qoi.sigma_sq = (qoi.u_sq_sum - (qoi.u_sum**2 / n)) / (n-1)
        tmp = qoi.u_uhfm_sum - qoi.u_sum*qoi_hfm.u_sum/n
        qoi.rho_sq = tmp**2 / (qoi.sigma_sq * qoi_hfm.sigma_sq * (n-1)**2)



    # @classmethod
    # def default_yml(cls,d):
        # """
        # MLMC specific layout of the default yml file.
        # """
        # super().default_yml(d)
        # d.all_defaults["solver"] = d.expand_to_several(
            # sub = d.all_defaults["solver"], 
            # list_name = "levels", 
            # exclude = ["_type","exe_path"])
        # for i,sub in enumerate(d.all_defaults["qois"]):
            # d.all_defaults["qois"][i] = d.expand_to_several(
                # sub = sub, 
                # list_name = "stages", 
                # keys = ["iteration_postproc","simulation_postproc"], 
                # exclude = ["_type","optimize"])




    def prepare_next_iteration(self):
        if len(self.iterations) == 1: 
            for i, qoi in enumerate(self.hfm.internal_qois): 
                p_print("Evaluate QoI " + qoi.name)
                stdout_table = StdOutTable("om_rho_sq","work_mean")
                stdout_table.set_descriptions("1-Rho^2","mean work")
                for model in self.models: 
                    qoi = model.internal_qois[i]
                    qoi.u = qoi.get_response()[0]
                    qoi.get_work_mean()
                    self.get_rho(self.sampling.n,qoi,self.hfm.qois[i])
                    qoi.om_rho_sq = 1. - qoi.rho_sq
                    stdout_table.update(qoi)
                stdout_table.p_print()

            self.select_models()
            self.qois_optimize = [m.qoi_opt for m in self.models_opt]
            m1, m2 = self.qois_optimize[0:2]
            for m, mn in zip( self.qois_optimize[:-1], self.qois_optimize[1:] ):
                m.r = np.sqrt(m1.work_mean * (m.rho_sq - mn.rho_sq)/(m.work_mean * (1. - m2.rho_sq)))
            # remove dummy at the end
            self.models_opt.pop(-1) 
            self.qois_optimize.pop(-1) 

            # update n samples
            for m in self.models: 
                m.samples.n_previous = m.samples.n
                m.samples.n = 0
            self.sampling.n_previous = self.sampling.n
            
            # get mlopt and alpha
            rv = [m.r         for m in self.qois_optimize]
            wv = [m.work_mean for m in self.qois_optimize]
            mlopt1 = self.total_work/np.dot(rv, wv)
            p_print("Selected Models and optimal number of samples:")
            stdout_table = StdOutTable("mlopt","alpha")
            stdout_table.set_descriptions("M_opt","alpha")
            for m in self.qois_optimize:
                m.mlopt = int(np.floor(mlopt1*m.r))
                m.samples.n = max(m.mlopt - m.samples.n_previous, 0)
                m.alpha = np.sqrt(m.rho_sq * self.hfm.qoi_opt.sigma_sq / m.sigma_sq)
                stdout_table.update(m)
            stdout_table.p_print()
            self.total_cost = np.dot(wv, [m.mlopt for m in self.qois_optimize])
            p_print("Estimated actual required total work: {}".format(self.total_cost))
            p_print("Estimated achieved MSE: {}".format(np.sqrt(self.v_opt))) #TODO
        else: 
            for model in self.models_opt: 
                if model.samples.n == 0: 
                    continue
                for qoi in model.internal_qois: 
                    qoi.u = np.concatenate((qoi.u,qoi.get_response()[0]))
            n = self.hfm.samples.n + self.hfm.samples.n_previous
            u = self.hfm.qoi_opt.u[:n+1]#.astype(np.float64)
            self.mean = np.mean(u)
            self.var = np.var(u,ddof=1)
            for mp, m in zip(self.models_opt[:-1], self.models_opt[1:]):
                n   =  m.samples.n +  m.samples.n_previous
                u   = m.qoi_opt.u[:n+1]#.astype(np.float64)
                np_ = mp.samples.n + mp.samples.n_previous
                up  = m.qoi_opt.u[:np_+1]#.astype(np.float64)
                self.mean += m.qoi_opt.alpha * (np.mean(u) - np.mean(up))
                self.var  += m.qoi_opt.alpha * (np.var(u,ddof=1) - np.var(up,ddof=1))
            self.std = np.sqrt(self.var)
            print()
            p_print("MEAN: {}".format(self.mean))
            p_print("STD:  {}".format(self.std))
            print()
           


    def select_models(self): 
        models = sorted(self.models, key=lambda m: m.qoi_opt.rho_sq, reverse=True)
        sets = []
        self.all_subsets(sets,[models[0]],models[1:])
        dummy = Empty()
        dummy.qoi_opt = Empty()
        dummy.qoi_opt.rho_sq = 0.
        for s in sets:
            s.append(dummy)
        s = sets.pop(0)
        v = self.get_v(s)
        for s_loc in sets: 
            v_loc = self.get_v(s_loc)
            if v_loc: 
                v = min(v, v_loc)
                s = s_loc
        self.models_opt = s
        self.v_opt = v

    def all_subsets(self,all_lists, prev_list, fut_list):
        if fut_list: 
            self.all_subsets(all_lists, prev_list, fut_list[1:])
            self.all_subsets(all_lists, prev_list + [fut_list[0]], fut_list[1:])
        else: 
            all_lists.append(prev_list)


    def get_v(self,set_): 
        for mp, m, mn in zip(set_[:-2], set_[1:-1], set_[2:]):
            qp, q, qn = mp.qoi_opt, m.qoi_opt, mn.qoi_opt
            if (qp.work_mean / q.work_mean) <= (qp.rho_sq - q.rho_sq) / (q.rho_sq - qn.rho_sq):
                return None
        v = 0.
        for m, mn in zip(set_[:-1], set_[1:]):
            q, qn = m.qoi_opt, mn.qoi_opt
            v += np.sqrt(q.work_mean * (q.rho_sq - qn.rho_sq))
        return v**2 * set_[0].qoi_opt.sigma_sq / self.total_work





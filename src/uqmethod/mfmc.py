import numpy as np
import os
import copy
from prettytable import PrettyTable

from .uqmethod import UqMethod
from helpers.printtools import *
from helpers.tools import *
from sampling.sampling import MonteCarlo
from solver.solver import Solver
from machine.machine import Machine
from stochvar.stochvar import StochVar
from helpers import config


# TODO: 
# - do not re-use pilot models in second iteration
# - get work for model, not for qoi 
# - fix qoi_optimize vs. all qois 
# - slightly nicer stdout 
# - rename check_all_finished
# - default yml
# - update estimates for rho, alpha and estimated MSE
# - get surrogate rho_sq estimate from subsets of hfm



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
        "reuse_warmup_samples": False,
        "reset_seed" : False
        }

    defaults_add = { 
        "Solver": { 
            "name": "NODEFAULT",
            "is_surrogate": False,
            "is_auxiliary": False # sample independently & exclude from postproc
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

        main_simu = Machine.create(prms["machine"])

        # initialize models
        all_models = config.config_list("models", prms, Solver.create, 
                                    self, main_simu, sub_list_name="fidelities")

        # initialize StochVars
        self.stoch_vars = config.config_list("stoch_vars", prms, StochVar.create,
                                             *all_models)

        for model in all_models: 
            if model.is_auxiliary: 
                # TODO: allow different kinds of sampling
                model.samples = MonteCarlo({})
            else: 
                model.samples = Empty()
                model.samples.n = self.n_warmup_samples
            model.samples.n_previous = 0
            model.samples.stoch_vars = self.stoch_vars
            model.internal_qois = []
        self.hfm = all_models[0]
        self.sampling = MonteCarlo({})
        self.sampling.nodes_all = np.empty((0,len(self.stoch_vars)))
        self.sampling.stoch_vars = self.stoch_vars

        #setup stages 
        main_simu.fill("simulation", True)
        main_simu.batches = [b for b in all_models if not b.is_surrogate]
        self.auxiliaries = [b for b in all_models if b.is_auxiliary]
        self.surrogates = [b for b in all_models if b.is_surrogate]
        self.models = [b for b in all_models if not b.is_auxiliary]
        temp = [b for b in self.models if not b.is_surrogate]
        # sorting: auxiliaries, then normal models, then surrogates
        self.all_models = self.auxiliaries + temp + self.surrogates
        self.stages = [main_simu]
       
        self.qois_optimize = []
        for model in self.all_models:
            # if model.is_surrogate: 
                # continue
            model.n_optimize = 0
            model.qois = []
            for sub_dict in prms["qois"]: 
                self.setup_qoi(sub_dict,model)
            if model.n_optimize != 1: 
                raise Exception("Please specify exactly "
                                "one QoI to optimize")
        for sm in self.surrogates:
            im = all_models[sm.i_model_input]
            im.samples.n = model.n_samples_input
            for i_qoi, qoi in enumerate(sm.qois): 
                qoi.participants = [sm, im, im.qois[i_qoi]]


    def setup_qoi(self, subdict, model):
        """ 
        set up quantity of interest for a model and make the 
        sublevels its participants
        """
        SolCls = model.__class__
        QoILoc = SolCls.QoI
        qoi = QoILoc.create_by_stage("iteration_postproc",subdict, SolCls, self)
        qoi.participants = [model]
        qoi.name = model.name + " " + qoi.__class__.name().replace(model.__class__.name()+"_", "")
        qoi.samples = model.samples
        if qoi.optimize: 
            model.n_optimize += 1
            model.qoi_opt = qoi
            if not model.is_auxiliary: 
                self.qois_optimize.append(qoi)
        model.qois.append(qoi)
        model.internal_qois.append(qoi)
        qoi.u_sum      = 0.
        qoi.u_sq_sum   = 0.
        qoi.u_uhfm_sum = 0.
        qoi.is_surrogate = model.is_surrogate


    def get_samples(self,dummy):
        """
        Overwritten. 
        samples are only drawn once, and then distributed to the models.
        """
        self.sampling.n = np.max([m.samples.n for m in self.models])
        if self.sampling.n > 0: 
            self.sampling.get()
        self.sampling.nodes_all = np.concatenate((self.sampling.nodes_all, self.sampling.nodes))
        for m in self.all_models:
            if m.is_auxiliary: 
                m.samples.get()
            else: 
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
            for i, qoi_hfm in enumerate(self.hfm.internal_qois): 
                p_print("Evaluate QoI " + qoi_hfm.name.replace(self.hfm.name+" ",""))
                table = PrettyTable()
                table.field_names = ["QoI","1-Rho^2","mean work"]
                for model in self.all_models: 
                    qoi = model.internal_qois[i]
                    qoi.u = qoi.get_response()[0]
                    qoi.get_work_mean()
                    if model.is_auxiliary: 
                        continue
                    self.get_rho(self.sampling.n,qoi,qoi_hfm)
                    qoi.om_rho_sq = 1. - qoi.rho_sq
                    table.add_row([qoi.name,qoi.om_rho_sq,qoi.work_mean])
                print_table(table)

            self.select_models()
            self.qois_optimize = [m.qoi_opt for m in self.models_opt]
            m1, m2 = self.qois_optimize[0:2]
            for m, mn in zip( self.qois_optimize[:-1], self.qois_optimize[1:] ):
                m.r = np.sqrt(m1.work_mean * (m.rho_sq - mn.rho_sq)/(m.work_mean * (1. - m2.rho_sq)))
            # remove dummy at the end
            self.models_opt.pop(-1) 
            self.qois_optimize.pop(-1) 

            # update n samples
            if self.reuse_warmup_samples: 
                for m in self.all_models: 
                    m.samples.n_previous = m.samples.n
                    # m.samples.n = 0
                self.sampling.n_previous = self.sampling.n
            
            # get mlopt and alpha
            rv = [m.r         for m in self.qois_optimize]
            wv = [m.work_mean for m in self.qois_optimize]
            mlopt1 = self.total_work/np.dot(rv, wv)
            p_print("\nSelected Models and optimal number of samples:")
            table = PrettyTable()
            table.field_names = ["QoI","M_opt","alpha"]
            for m in self.qois_optimize:
                m.mlopt = int(np.floor(mlopt1*m.r))
                m.samples.n = max(m.mlopt - m.samples.n_previous, 0)
                m.alpha = np.sqrt(m.rho_sq * self.hfm.qoi_opt.sigma_sq / m.sigma_sq)
                table.add_row([m.name,m.mlopt,m.alpha])
            print_table(table)
            self.total_cost = np.dot(wv, [m.mlopt for m in self.qois_optimize])
            p_print("\nEstimated actual required total work: {}".format(self.total_cost))
            p_print("Estimated achieved RMSE: {}".format(np.sqrt(self.v_opt))) #TODO
            # with open("results.dat","a") as f: 
                # f.write(str(self.total_cost)+", "+str(np.sqrt(self.v_opt))+", ")
        else: 
            for model in self.models_opt: 
                if model.samples.n == 0: 
                    continue
                for qoi in model.internal_qois: 
                    if self.reuse_warmup_samples: 
                        qoi.u = np.concatenate((qoi.u,qoi.get_response()[0]))
                    else: 
                        qoi.u = qoi.get_response()[0]
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
            # with open("results.dat","a") as f: 
                # f.write(str(self.mean)+", "+str(self.std)+"\n")
           

    def select_models(self): 
        models = sorted(self.models, key=lambda m: m.qoi_opt.rho_sq, reverse=True)
        sets = []
        self.all_subsets(sets,[models[0]],models[1:])
        dummy = Empty()
        dummy.qoi_opt = Empty()
        dummy.qoi_opt.rho_sq = 0.
        for s in sets:
            s.append(dummy)
        self.models_opt = min(sets, key=self.get_v)
        self.v_opt = self.get_v(self.models_opt)


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
                return 1.E100
        v = 0.
        for m, mn in zip(set_[:-1], set_[1:]):
            q, qn = m.qoi_opt, mn.qoi_opt
            v += np.sqrt(q.work_mean * (q.rho_sq - qn.rho_sq))
        return v**2 * set_[0].qoi_opt.sigma_sq / self.total_work





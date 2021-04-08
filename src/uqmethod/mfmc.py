import numpy as np
import os
import copy
from prettytable import PrettyTable
import collections

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

    cname = "mfmc"

    defaults_ = {
        # "tolerance" : None,
        "total_work" : "NODEFAULT",
        "n_warmup_samples": "NODEFAULT",
        "reuse_warmup_samples": False,
        "update_alpha": False,
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
        if self.update_alpha and not self.reuse_warmup_samples: 
            raise Exception("update alpha only possible if warmup samples are resued!")

    def setup(self, prms):
        """
        Set up data structure for an MLMC simulation
        Includes levels and sublevels, quantities of interest, 
        each initiallized according to chosen solver, 
        and stages (main simulation and post proc) according to
        chosen machine.
        """


        prms_models = config.expand_prms_by_sublist(prms["models"],"fidelities")
        model_classes = [Solver.subclass(sd["_type"]) for sd in prms_models]

        # initialize StochVars
        self.stoch_vars = config.config_list("stoch_vars", prms, StochVar.create,
                                             *model_classes)

        # samplers 
        self.samplers = []
        for subdict in prms_models: 
            if subdict.get("is_auxiliary"):
                # TODO: allow different kinds of sampling
                sampler = MonteCarlo({})
            else: 
                sampler = Empty()
                sampler.n = self.n_warmup_samples
            sampler.n_previous = 0
            sampler.stoch_vars = self.stoch_vars
            self.samplers.append(sampler)

        #stages 
        for i_stage, stage in enumerate(self.stages): 
            stage.all_models = config.config_list("models", prms, Solver.create_by_stage_from_list, i_stage, 
                                             stage.name, self, stage.__class__, sub_list_name="fidelities")
            stage.batches = [b for b in stage.all_models if not b.is_surrogate]
            for sampler, model in zip(self.samplers,stage.all_models): 
                model.samples = sampler 
                model.internal_qois = []


        all_models = self.stages[-1].all_models # last stage is input to QoI

        self.hfm = all_models[0]
        self.sampling = MonteCarlo({})
        self.sampling.nodes_all = np.empty((0,len(self.stoch_vars)))
        self.sampling.stoch_vars = self.stoch_vars

        #setup stages 
        self.auxiliaries = [b for b in all_models if b.is_auxiliary]
        self.surrogates = [b for b in all_models if b.is_surrogate]
        self.models = [b for b in all_models if not b.is_auxiliary]
        temp = [b for b in self.models if not b.is_surrogate]
        # sorting: auxiliaries, then normal models, then surrogates
        self.all_models = self.auxiliaries + temp + self.surrogates
       
        self.qois_optimize = []
        for model, ModelClass in zip(all_models,model_classes):
            # if model.is_surrogate: 
                # continue
            model.n_optimize = 0
            model.qois = []
            for sub_dict in prms["qois"]: 
                # model class is required since model itself can be a stage subclass and QoIs
                # are no subclasses of StageSub.QoI
                self.setup_qoi(sub_dict,model,ModelClass.QoI)
            if model.n_optimize != 1: 
                raise Exception("Please specify exactly "
                                "one QoI to optimize")
        for sm in self.surrogates:
            im = all_models[sm.i_model_input]
            im.samples.n = model.n_samples_input
            for i_qoi, qoi in enumerate(sm.qois): 
                qoi.participants = [sm, im, im.qois[i_qoi]]


    def setup_qoi(self, subdict, model, QoILoc):
        """ 
        set up quantity of interest for a model and make the 
        sublevels its participants
        """
        qoi = QoILoc.create_by_stage(subdict,"iteration_postproc",self)
        qoi.participants = [model]
        qoi.name = model.name + " " + qoi.cname
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
        qoi.u_sum      = np.sum(qoi.u[:n],axis=0)
        qoi.u_sq_sum   = np.sum(qoi.u[:n]**2,axis=0)
        qoi.u_uhfm_sum = np.sum(qoi.u[:n]*qoi_hfm.u[:n],axis=0)

        qoi.sigma_sq = (qoi.u_sq_sum - (qoi.u_sum**2 / n)) / (n-1)
        tmp = qoi.u_uhfm_sum - qoi.u_sum*qoi_hfm.u_sum/n
        qoi.rho_sq = tmp**2 / (qoi.sigma_sq * qoi_hfm.sigma_sq * (n-1)**2)

        qoi.sigma_sq = qoi.integrate(qoi.sigma_sq)
        qoi.rho_sq   = qoi.integrate(qoi.rho_sq)



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
                for model in self.all_models: 
                    qoi = model.internal_qois[i]
                    qoi.u = qoi.get_response()[0]
                    qoi.get_work_mean()
                    if model.is_auxiliary: 
                        continue
                    self.get_rho(self.sampling.n,qoi,qoi_hfm)
                    qoi.om_rho_sq = 1. - qoi.rho_sq
                add_str = " (Optimized)" if qoi_hfm is self.hfm.qoi_opt else ""
                p_print("Evaluate QoI " + qoi_hfm.cname + add_str)
                table = PrettyTable()
                for model in self.all_models: 
                    qoi = model.internal_qois[i]
                    table.add_row([model.name,qoi.om_rho_sq,qoi.work_mean])
                table.field_names = ["Model","1-Rho^2","mean work"]
                print_table(table)

            self.select_models()
            self.qois_optimize = [m.qoi_opt for m in self.models_opt]
            q1, q2 = self.qois_optimize[0:2]
            for q, qn in zip( self.qois_optimize[:-1], self.qois_optimize[1:] ):
                q.r = np.sqrt(q1.work_mean * (q.rho_sq - qn.rho_sq)/(q.work_mean * (1. - q2.rho_sq)))
            # remove dummy at the end
            self.models_opt.pop(-1) 
            self.qois_optimize.pop(-1) 

            # update n samples
            if self.reuse_warmup_samples: 
                for m in self.all_models: 
                    m.samples.n_previous = m.samples.n
                self.sampling.n_previous = self.sampling.n
            for m in self.all_models: 
                m.samples.n = 0
            
            # get mlopt and alpha
            rv = [q.r         for q in self.qois_optimize]
            wv = [q.work_mean for q in self.qois_optimize]
            mlopt1 = self.total_work/np.dot(rv, wv)
            if self.reuse_warmup_samples: 
                self.work_warmup = 0.
            else: 
                self.work_warmup = np.sum(wv)*self.n_warmup_samples

            for i, qoi_hfm in enumerate(self.hfm.internal_qois): 
                for model in self.models_opt: 
                    qoi = model.internal_qois[i]
                    qoi.alpha = np.sqrt(qoi.rho_sq * qoi_hfm.sigma_sq / qoi.sigma_sq)

            p_print("\nSelected Models and optimal number of samples:")
            table = PrettyTable()
            table.field_names = ["Model","M_opt","alpha"]
            for m in self.models_opt: 
                q = m.qoi_opt
                mlopt = mlopt1*q.r
                q.mlopt = int(round(mlopt))
                q.samples.n = max(q.mlopt - q.samples.n_previous, 0)
                mlopt_print = q.mlopt if q.mlopt > 1 else mlopt
                table.add_row([m.name,mlopt_print,q.alpha])
            print_table(table)
            self.total_cost = np.dot(wv, [q.mlopt for q in self.qois_optimize])
            print()
            p_print("Estimated actual required total work: {}".format(self.total_cost))
            p_print("Estimated achieved RMSE: {}".format(np.sqrt(self.v_opt))) #TODO
        else: 
            for model in self.models_opt: 
                if model.samples.n == 0: 
                    continue
                for qoi in model.internal_qois: 
                    if self.reuse_warmup_samples: 
                        qoi.u = np.concatenate((qoi.u,qoi.get_response()[0]))
                    else: 
                        qoi.u = qoi.get_response()[0]
            n_hfm = self.hfm.samples.n + self.hfm.samples.n_previous

            table = PrettyTable()
            table.field_names = ["QoI","Mean","Standard Deviation"]
            for i, qoi_hfm in enumerate(self.hfm.internal_qois): 
                if self.update_alpha: 
                    for m in self.models_opt:
                        if model.is_auxiliary: 
                            continue
                        q = m.internal_qois[i]
                        self.get_rho(n_hfm,q,qoi_hfm)
                        q.alpha = np.sqrt(q.rho_sq * qoi_hfm.sigma_sq / q.sigma_sq)
                u = qoi_hfm.u[:n_hfm+1]#.astype(np.float64)
                qoi_hfm.mean = np.mean(u,axis = 0)
                qoi_hfm.var = np.var(u,axis=0,ddof=1)
                for mp, m in zip(self.models_opt[:-1], self.models_opt[1:]):
                    q = m.internal_qois[i]
                    n   =  m.samples.n +  m.samples.n_previous
                    u   = q.u[:n+1]#.astype(np.float64)
                    np_ = mp.samples.n + mp.samples.n_previous
                    up  = q.u[:np_+1]#.astype(np.float64)
                    qoi_hfm.mean += q.alpha * (np.mean(u,axis = 0) - np.mean(up,axis=0))
                    qoi_hfm.var  += q.alpha * (np.var(u,axis=0,ddof=1) - np.var(up,axis=0,ddof=1))
                qoi_hfm.stddev = np.sqrt(qoi_hfm.var)
                qoi_hfm.write_to_file()
                if isinstance(qoi_hfm.mean,(float,np.float)):
                    table.add_row([qoi_hfm.cname,qoi_hfm.mean,qoi_hfm.stddev])
                else:
                    table.add_row([qoi_hfm.cname + " (Int.)",
                                   qoi_hfm.integrate(qoi_hfm.mean),
                                   np.sqrt(qoi_hfm.integrate(qoi_hfm.var))])
            self.mean   = self.hfm.qoi_opt.mean
            self.stddev = self.hfm.qoi_opt.stddev
            print_table(table)
           

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





import numpy as np
import os
import copy
from prettytable import PrettyTable
import collections
import warnings
import sys

from .uqmethod import UqMethod
from helpers.printtools import *
from helpers.tools import *
from sampling.sampling import MonteCarlo
from solver.solver import Solver,register_batch_series
from machine.machine import Machine
from stochvar.stochvar import StochVar
from helpers import config


# TODO: 
# - get work for model, not for qoi 
# - fix qoi_optimize vs. all qois 
# - rename check_all_finished
# - default yml



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
        "update_alpha": False
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

    def __init__(self, input_prm_dict):
        super().__init__(input_prm_dict)
        self.has_simulation_postproc = True
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
        sampling_prms = prms["sampling"] if "sampling" in prms else {}
        for subdict in prms_models: 
            if subdict.get("is_auxiliary"):
                # TODO: allow different kinds of sampling
                sampler = MonteCarlo(sampling_prms)
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

        register_batch_series(self.stages) 

        all_models = self.stages[-1].all_models # last stage is input to QoI

        self.hfm = all_models[0]
        self.sampling = MonteCarlo(sampling_prms)
        self.sampling.seed_id = 0
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
            self.sampling.n_previous = self.sampling.nodes_all.shape[0]
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
        # print(qoi.u[:n]) #TODO DEBUG
        qoi.u_sum      = np.sum(qoi.u[:n],axis=0)
        qoi.u_sq_sum   = np.sum(qoi.u[:n]**2,axis=0)
        qoi.u_uhfm_sum = np.sum(qoi.u[:n]*qoi_hfm.u[:n],axis=0)

        qoi.sigma_sq_field = (qoi.u_sq_sum - (qoi.u_sum**2 / n)) / (n-1)
        enum  = ((qoi.u_uhfm_sum - qoi.u_sum*qoi_hfm.u_sum/n) / (n-1.))**2
        denom = qoi.sigma_sq_field * qoi_hfm.sigma_sq_field
        # this is a fallbck for sigma = 0 or very small
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        qoi.rho_sq_field = np.where(denom > enum,enum/denom,1.)
        warnings.filterwarnings("default", category=RuntimeWarning)

        qoi.sigma_sq = qoi.integrate(qoi.sigma_sq_field)
        # TODO: Decide
        # V1 
        # qoi.rho_sq   = qoi.integrate(qoi.rho_sq_field)
        # V2
        # qoi.rho_sq   = qoi.integrate(enum)/qoi.integrate(denom)
        # V3
        sqrtdenom = safe_sqrt(denom)
        qoi.rho_sq   = qoi.integrate(qoi.rho_sq_field*sqrtdenom)/qoi.integrate(sqrtdenom)



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

            # create dummy model
            self.dummy_model = Empty()
            self.dummy_model.internal_qois = [Empty() for q in self.hfm.internal_qois]
            for q in self.dummy_model.internal_qois: 
                q.rho_sq = 0.

            for i, qoi_hfm in enumerate(self.hfm.internal_qois): 
                for model in self.all_models: 
                    qoi = model.internal_qois[i]
                    qoi.u = qoi.get_response()[0]
                    qoi.work_mean_static = qoi.work_mean

                    # TODO: DEBUG 
                    # if i==2: 
                       # np.savetxt("csv/"+model.name+".csv",qoi.u)

                    if model.is_auxiliary: 
                        continue
                    self.get_rho(self.sampling.n,qoi,qoi_hfm)
                    qoi.om_rho_sq = 1. - qoi.rho_sq
                add_str = " (OPTIMIZED!)" if qoi_hfm is self.hfm.qoi_opt else ""
                p_print("Evaluate QoI " + qoi_hfm.cname + add_str)
                table = PrettyTable()
                for model in self.all_models: 
                    qoi = model.internal_qois[i]
                    table.add_row([model.name,qoi.om_rho_sq,qoi.work_mean_static])
                table.field_names = ["Model","1-Rho^2","mean work"]
                print_table(table)

                models_opt, v_opt = self.select_models(i)
                qois_opt = [m.internal_qois[i] for m in models_opt]
                q1, q2 = qois_opt[0:2]
                for q, qn in zip( qois_opt[:-1], qois_opt[1:] ):
                    q.r = safe_sqrt(q1.work_mean_static * (q.rho_sq - qn.rho_sq)/(q.work_mean_static * (1. - q2.rho_sq)))
                # remove dummy at the end
                models_opt.pop(-1) 
                qois_opt.pop(-1) 

            
                # get mlopt and alpha
                rv = [q.r         for q in qois_opt]
                wv = [q.work_mean_static for q in qois_opt]
                mlopt1 = self.total_work/np.dot(rv, wv)
                if self.reuse_warmup_samples: 
                    work_warmup = 0.
                else: 
                    work_warmup = np.sum(wv)*self.n_warmup_samples

                for qoi in qois_opt: 
                    qoi.alpha = safe_sqrt(qoi.rho_sq * qoi_hfm.sigma_sq / qoi.sigma_sq)

                p_print("\nSelected Models and optimal number of samples:")
                table = PrettyTable()
                table.field_names = ["Model","M_opt","alpha"]
                for m, q in zip(models_opt,qois_opt): 
                    mlopt = mlopt1*q.r
                    q.mlopt = int(round(mlopt))
                    mlopt_print = q.mlopt if q.mlopt > 1 else mlopt
                    table.add_row([m.name,mlopt_print,q.alpha])
                print_table(table)
                total_cost = np.dot(wv, [q.mlopt for q in qois_opt])
                print()
                p_print("Estimated actual required total work: {}".format(total_cost))
                p_print("Estimated achieved RMSE: {}".format(safe_sqrt(v_opt)))
                
                # make valid for simulation
                if qoi_hfm.optimize: 
                    self.models_opt = models_opt
                    self.qois_optimize = qois_opt
                    self.work_warmup = work_warmup
                    self.total_cost = total_cost
                    self.v_opt = v_opt

            # update n samples
            if self.reuse_warmup_samples: 
                for m in self.all_models: 
                    m.samples.n_previous = m.samples.n
                self.sampling.n_previous = self.sampling.n
            for m in self.all_models: 
                m.samples.n = 0
            for m in self.models_opt: 
                m.samples.n = max(m.qoi_opt.mlopt - m.samples.n_previous, 0)
        else: 
            for model in self.models_opt: 
                if model.samples.n == 0: 
                    continue
                for qoi in model.internal_qois: 
                    if self.reuse_warmup_samples: 
                        qoi.u = np.concatenate((qoi.u,qoi.get_response()[0]))
                    else: 
                        qoi.u = qoi.get_response()[0]
                    qoi.work_mean_static = qoi.work_mean
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
                        q.alpha = safe_sqrt(q.rho_sq * qoi_hfm.sigma_sq / q.sigma_sq)
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
                qoi_hfm.stddev = safe_sqrt(qoi_hfm.var)
                qoi_hfm.write_to_file()
                if isinstance(qoi_hfm.mean,(float,np.float)):
                    table.add_row([qoi_hfm.cname,qoi_hfm.mean,qoi_hfm.stddev])
                else:
                    table.add_row([qoi_hfm.cname + " (Int.)",
                                   qoi_hfm.integrate(qoi_hfm.mean),
                                   safe_sqrt(qoi_hfm.integrate(qoi_hfm.var))])
            self.mean   = self.hfm.qoi_opt.mean
            self.stddev = self.hfm.qoi_opt.stddev
            print_table(table)
           

    def select_models(self,i_qoi): 
        models = sorted(self.models, key=lambda m: m.internal_qois[i_qoi].rho_sq, reverse=True)
        sets = []
        self.all_subsets(sets,[models[0]],models[1:])
        for s in sets:
            s.append(self.dummy_model)
        models_opt = min(sets, key=lambda s: self.get_v(s,i_qoi))
        v_opt = self.get_v(models_opt,i_qoi)
        return models_opt,v_opt


    def all_subsets(self,all_lists, prev_list, fut_list):
        if fut_list: 
            self.all_subsets(all_lists, prev_list, fut_list[1:])
            self.all_subsets(all_lists, prev_list + [fut_list[0]], fut_list[1:])
        else: 
            all_lists.append(prev_list)


    def get_v(self,set_,i_qoi): 
        for mp, m, mn in zip(set_[:-2], set_[1:-1], set_[2:]):
            qp, q, qn = mp.internal_qois[i_qoi], m.internal_qois[i_qoi], mn.internal_qois[i_qoi]
            if (qp.work_mean_static / q.work_mean_static) <= (qp.rho_sq - q.rho_sq) / (q.rho_sq - qn.rho_sq):
                return 1.E100
        v = 0.
        for m, mn in zip(set_[:-1], set_[1:]):
            q, qn = m.internal_qois[i_qoi], mn.internal_qois[i_qoi]
            v += safe_sqrt(q.work_mean_static * (q.rho_sq - qn.rho_sq))
        return v**2 * set_[0].internal_qois[i_qoi].sigma_sq / self.total_work





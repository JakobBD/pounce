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



class Mfmc(UqMethod):
    """
    Multifidelity Monte Carlo based on control variates

    Based on Peherstorfer et al., 2016: https://doi.org/10.1137/15M1046472

    Differences to the reference: 
    - Pilot simulations can be re-used for estimators; This can introduce a bias in the estimators, 
      but was found in practice to be more efficient in most cases 
    - If pilot simulations are re-used, estimates of CV coefficients can be updated using full sample size
    - An ad-hoc extension to vectorial or field-valued QoIs is added
    """

    cname = "mfmc"

    defaults_ = {
        "total_work" : "NODEFAULT",           # computational budget
        "n_warmup_samples": "NODEFAULT",      # pilot sample size
        "reuse_warmup_samples": False,        # reuse pilot simulations for estimators
        "update_alpha": False                 # update CV coefficients
        }

    defaults_add = { 
        "Solver": { 
            "name": "NODEFAULT",              # models are named to be distinguished in MFMC 
            "is_surrogate": False,            # model is surrogate model
            "is_auxiliary": False             # model is used as input to construct surrogate model
                                              # (sample independently & exclude from postproc)
            },
        "QoI": {
            "optimize": False,                # require to specify one QoI for which models, sample size etc are optimized
            }
        }


    def __init__(self, input_prm_dict):
        """
        Called at beginning of config routine.
        """
        # Attributes are initialized from input prms and defaults in BaseClass init: 
        super().__init__(input_prm_dict)

        self.has_simulation_postproc = True
        self.n_max_iter = 2
        self.has_simulation_postproc = False
        if self.update_alpha and not self.reuse_warmup_samples: 
            raise Exception("update alpha only possible if warmup samples are resued!")


    def setup(self, prms):
        """
        Called from config for all the MFMC-specific parts of the setup.

        Set up data structure for an MFMC simulation
        Includes models and quantities of interest, 
        each initialized according to chosen solver, 
        and stages according to chosen machine.
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
                sampler = MonteCarlo(sampling_prms)
            else: 
                sampler = Empty()
                sampler.n = self.n_warmup_samples
            sampler.n_previous = 0
            sampler.stoch_vars = self.stoch_vars
            self.samplers.append(sampler)

        # stages 
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

        # common sample drawing, from which samples for models are taken
        self.sampling = MonteCarlo(sampling_prms)
        self.sampling.seed_id = 0
        self.sampling.nodes_all = np.empty((0,len(self.stoch_vars)))
        self.sampling.stoch_vars = self.stoch_vars

        # set up stages 
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
        set up and initialize quantity of interest for a model
        """
        qoi = QoILoc.create_by_stage(subdict,"iteration_postproc",self)
        qoi.participants = [model]
        qoi.name = model.name + " " + qoi.cname
        qoi.samples = model.samples
        if qoi.optimize: 
            model.n_optimize += 1 # for check that n_optimize == 1
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
        Overwrites parent class routine. 
        In MFMC, samples are re-used across models.
        Samples are therefore only drawn once, and then distributed to the models.
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
        """
        Calculate square of correlation coeficient between given LF modeli QoI and HF model QoI.
        POUNCE allows vectorial QoIs, for which an integration method is provided.
        The integration corresponds to a weighting of the components
        """
        qoi.u_sum      = np.sum(qoi.u[:n],axis=0)
        qoi.u_sq_sum   = np.sum(qoi.u[:n]**2,axis=0)
        qoi.u_uhfm_sum = np.sum(qoi.u[:n]*qoi_hfm.u[:n],axis=0)

        # calculate field-valued quantities
        qoi.sigma_sq_field = (qoi.u_sq_sum - (qoi.u_sum**2 / n)) / (n-1)
        enumerator  = (qoi.u_uhfm_sum - qoi.u_sum*qoi_hfm.u_sum/n) / (n-1.)
        denominator = safe_sqrt(qoi.sigma_sq_field * qoi_hfm.sigma_sq_field)
        # sanity check with fallback to rho=1 for sigma = 0 or very small, 
        # where correlation coefficient is not defined.
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        qoi.rho_sq_field = np.where(enumerator**2 < denominator**2, enumerator**2/denominator**2,1.)
        warnings.filterwarnings("default", category=RuntimeWarning)

        # calculate integrated quantities
        qoi.sigma_sq = qoi.integrate(qoi.sigma_sq_field)
        # since hfm is always first, sigma_sq of qoi_hfm is already computed at this point.

        qoi.rho_sq   = qoi.integrate(enumerator)**2/qoi.sigma_sq*qoi_hfm.sigma_sq


    def prepare_next_iteration(self):
        """
        MFMC consists of two iterations: 
        Pilot runs in iteration 1 and main simulation in iteration 2. 
        The stochastic evaluation therefore contains the optimal choice of models and sample sizes 
        at the end of iteration 1, and the calculation of the eventual mean and variance estimmator 
        at the end of iteration 2. 
        This routine therefore is different depending on the iteration count.
        """
        if len(self.iterations) == 1: 
            # calculate optimal configuration (between pilot simulations and main simulations)

            # create dummy "very low fidelity" model to append to list of models
            self.dummy_model = Empty()
            self.dummy_model.internal_qois = [Empty() for q in self.hfm.internal_qois]
            for q in self.dummy_model.internal_qois: 
                q.rho_sq = 0.

            # evaluate all internal quantities of interest independently of each other
            # Only one QoI is used for optimized model and sample size selection. For the others, 
            # The according calculations are done as well and the info is printed to stdout. 
            for i, qoi_hfm in enumerate(self.hfm.internal_qois): 

                # get QoI response for all sample points, get correlation coefficients.
                for model in self.all_models: 
                    qoi = model.internal_qois[i]
                    qoi.u = qoi.get_response()[0]
                    qoi.work_mean_static = qoi.work_mean
                    if model.is_auxiliary: 
                        continue
                    self.get_rho(self.sampling.n,qoi,qoi_hfm)
                    qoi.om_rho_sq = 1. - qoi.rho_sq

                # print info to stdout
                add_str = " (OPTIMIZED!)" if qoi_hfm is self.hfm.qoi_opt else ""
                p_print("Evaluate QoI " + qoi_hfm.cname + add_str)
                table = PrettyTable()
                for model in self.all_models: 
                    qoi = model.internal_qois[i]
                    table.add_row([model.name,qoi.om_rho_sq,qoi.work_mean_static])
                table.field_names = ["Model","1-Rho^2","mean work"]
                print_table(table)

                # select optimal set of models
                models_opt, v_opt = self.select_optimal_model_subset(i)
                qois_opt = [m.internal_qois[i] for m in models_opt]


                # Get optimal sample sizes mlopt and CV coefficients alpha
                # --------------------------------------------------------
                q1, q2 = qois_opt[0:2]
                for q, qn in zip( qois_opt[:-1], qois_opt[1:] ):
                    q.r = safe_sqrt(q1.work_mean_static * (q.rho_sq - qn.rho_sq)/(q.work_mean_static * (1. - q2.rho_sq)))
                # remove dummy at the end
                models_opt.pop(-1) 
                qois_opt.pop(-1) 

                rv = [q.r         for q in qois_opt]
                wv = [q.work_mean_static for q in qois_opt] # possible improvement (TODO): get work for model, not QoI
                mlopt1 = self.total_work/np.dot(rv, wv)

                # evaluate work for warm-up samples, which can be added to the total simulation cost 
                # for a fair comparison with other approaches.
                if self.reuse_warmup_samples: 
                    work_warmup = 0.
                else: 
                    work_warmup = np.sum(wv)*self.n_warmup_samples

                for qoi in qois_opt: 
                    qoi.alpha = safe_sqrt(qoi.rho_sq * qoi_hfm.sigma_sq / qoi.sigma_sq)

                # calc eventual mlopt and print to stdout
                p_print("\nSelected Models and optimal number of samples:")
                table = PrettyTable()
                table.field_names = ["Model","M_opt","alpha"]
                for m, q in zip(models_opt,qois_opt): 
                    mlopt = mlopt1*q.r
                    q.mlopt = int(round(mlopt))
                    # for values > 1, the integer mlopt is the relevant information. 
                    # for values < 1, the exact value gives more information than a plain 0.
                    mlopt_print = q.mlopt if q.mlopt > 1 else mlopt
                    table.add_row([m.name,mlopt_print,q.alpha])
                print_table(table)

                # print estimates for simulation performance to stdout
                total_cost = np.dot(wv, [q.mlopt for q in qois_opt])
                print()
                p_print("Estimated actual required total work: {}".format(total_cost))
                p_print("Estimated achieved RMSE: {}".format(safe_sqrt(v_opt)))
                
                # if this QoI is optimized, save local optimal variables as global attributes of the simulation
                if qoi_hfm.optimize: 
                    self.models_opt = models_opt
                    self.qois_optimize = qois_opt
                    self.work_warmup = work_warmup
                    self.total_cost = total_cost
                    self.v_opt = v_opt

            # update sample size
            if self.reuse_warmup_samples: 
                for m in self.all_models: 
                    m.samples.n_previous = m.samples.n
                self.sampling.n_previous = self.sampling.n
            for m in self.all_models: 
                m.samples.n = 0
            for m in self.models_opt: 
                m.samples.n = max(m.qoi_opt.mlopt - m.samples.n_previous, 0)
        else: 
            # End of simulation: 
            # Calculate mean and variance estimators of QoIs

            # get QoI respone of model evalutions in iteration 2
            for model in self.models_opt: 
                if model.samples.n == 0: 
                    # no new evaluations since pilot samples, as mlopt < ml_pilot
                    continue
                for qoi in model.internal_qois: 
                    if self.reuse_warmup_samples: 
                        qoi.u = np.concatenate((qoi.u,qoi.get_response()[0]))
                    else: 
                        qoi.u = qoi.get_response()[0]
                    qoi.work_mean_static = qoi.work_mean

            # high-fidelity model sample size
            n_hfm = self.hfm.samples.n + self.hfm.samples.n_previous

            # get mean and variance estimators; print to stdout and write to file, if applicable.
            # -----------------------------------------------------------------------------------

            # prepare stdout
            table = PrettyTable()
            table.field_names = ["QoI","Mean","Standard Deviation"]

            for i, qoi_hfm in enumerate(self.hfm.internal_qois): 
                if self.update_alpha: 
                    # optionally update CV coefficient based on increased number of sample points after iteration 2
                    for m in self.models_opt:
                        if model.is_auxiliary: 
                            continue
                        q = m.internal_qois[i]
                        self.get_rho(n_hfm,q,qoi_hfm)
                        q.alpha = safe_sqrt(q.rho_sq * qoi_hfm.sigma_sq / q.sigma_sq)

                u = qoi_hfm.u[:n_hfm+1]#.astype(np.float64)

                # get estimators for mean and variance 
                # ------------------------------------

                # store mean and variance in high-fidelity model QoI
                # initialize with high-fidelity modle contribution
                qoi_hfm.mean = np.mean(u,axis = 0)
                qoi_hfm.var = np.var(u,axis=0,ddof=1)
                for mp, m in zip(self.models_opt[:-1], self.models_opt[1:]):
                    q = m.internal_qois[i]
                    n   =  m.samples.n +  m.samples.n_previous
                    u   = q.u[:n+1]#.astype(np.float64)
                    np_ = mp.samples.n + mp.samples.n_previous
                    up  = q.u[:np_+1]#.astype(np.float64)

                    # sum over control variates
                    qoi_hfm.mean += q.alpha * (np.mean(u,axis = 0) - np.mean(up,axis=0))
                    qoi_hfm.var  += q.alpha * (np.var(u,axis=0,ddof=1) - np.var(up,axis=0,ddof=1))

                qoi_hfm.stddev = safe_sqrt(qoi_hfm.var)

                # Optionally write result to file (if implemented for this QoI)
                # Especially useful for field-valued QoIs
                qoi_hfm.write_to_file()

                # prepare print to stdout
                if isinstance(qoi_hfm.mean,float):
                    table.add_row([qoi_hfm.cname,qoi_hfm.mean,qoi_hfm.stddev])
                else:
                    table.add_row([qoi_hfm.cname + " (Int.)",
                                   qoi_hfm.integrate(qoi_hfm.mean),
                                   safe_sqrt(qoi_hfm.integrate(qoi_hfm.var))])

            # copy end result to attributed of main simulation
            self.mean   = self.hfm.internal_qois[0].mean
            self.stddev = self.hfm.internal_qois[0].stddev

            # print to stdout
            print_table(table)
           

    def select_optimal_model_subset(self,i_qoi): 
        """
        Get subset of proposed low-fidelity models with the lowest expected error.
        """
        # models sorted descendingly by correlation with the high-fidelity model
        models = sorted(self.models, key=lambda m: m.internal_qois[i_qoi].rho_sq, reverse=True)

        # get list of all subsets
        model_subsets = []
        self.get_all_subsets(model_subsets,[models[0]],models[1:])

        # append dummmy model
        for s in model_subsets:
            s.append(self.dummy_model)

        # get MSE for all subsets
        estimator_variances = [self.get_estimator_variance(s,i_qoi) for s in model_subsets]

        # get subsets with lowest MSE
        v_opt,models_opt = min(zip(estimator_variances,model_subsets))

        return models_opt,v_opt


    def get_all_subsets(self,subset_collecion, current_subset, remaining_elements):
        """
        Recursive function to get all subsets of a set: 
        Iterate over all elements of the original set.
        Start with a subset containing the high-fidelity model (which is in all subsets)
        For each element in the set, create one copy of the subset wit the element in it, and one without. 
        If no elements remain, add each subset to the list of subsets. 
        """

        if remaining_elements: 
            self.get_all_subsets(subset_collecion, current_subset,                           remaining_elements[1:])
            self.get_all_subsets(subset_collecion, current_subset + [remaining_elements[0]], remaining_elements[1:])
        else: 
            subset_collecion.append(current_subset)


    def get_estimator_variance(self,set_,i_qoi): 
        """
        Estimate the mean squared error of the mean estimator with a given subset of models.
        """
        for mp, m, mn in zip(set_[:-2], set_[1:-1], set_[2:]):
            qp, q, qn = mp.internal_qois[i_qoi], m.internal_qois[i_qoi], mn.internal_qois[i_qoi]
            if (qp.work_mean_static / q.work_mean_static) <= (qp.rho_sq - q.rho_sq) / (q.rho_sq - qn.rho_sq):
                # invalid choice, return large value for subset to be discarded
                return 1.E100
        v = 0.
        for m, mn in zip(set_[:-1], set_[1:]):
            q, qn = m.internal_qois[i_qoi], mn.internal_qois[i_qoi]
            v += safe_sqrt(q.work_mean_static * (q.rho_sq - qn.rho_sq))
        return v**2 * set_[0].internal_qois[i_qoi].sigma_sq / self.total_work


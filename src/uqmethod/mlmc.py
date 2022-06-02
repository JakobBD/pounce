import numpy as np
import os
import copy
from prettytable import PrettyTable
from scipy.stats import chi2, norm

from .uqmethod import UqMethod
from helpers.printtools import *
from helpers.tools import *
from sampling.sampling import MonteCarlo
from solver.solver import Solver,register_batch_series
from machine.machine import Machine
from stochvar.stochvar import StochVar
from helpers import config


class Mlmc(UqMethod):
    """
    Multilevel Monte Carlo
    The number of levels is prescribed, the number of samples is 
    adapted iteratively in a prescribed number of iterations
    (convergence rate and work per sample are obtained empirically).
    """

    cname = "mlmc"

    defaults_ = {
        "n_max_iter" : "NODEFAULT",   # number of iterations to safely approach optimal sample size
        "eps" : None,                 # prescribed means estimator RMSE 
        "total_work" : None,          # computational budget
        "use_ci" : False,             # use confidence inerval-based calculation of sample size per iteration
                                      # alternative is a heuristic approach
        "ci_conf_tot" : 0.95,         # confidence level for sample size calculation in each level
        "dof_adj" : False             # use DOF-adjusted confidence intervals (strongly discouraged!!)
        }

    defaults_add = { 
        "Solver": { 
            "n_warmup_samples": "NODEFAULT" # number of pilot runs per level
            },
        "QoI": {
            "optimize": False         # require to specify one QoI for which sample size is optimized
            }
        }


    def __init__(self, input_prm_dict):
        """
        Called at beginning of config routine.
        """
        # Attributes are initialized from input prms and defaults in BaseClass init: 
        super().__init__(input_prm_dict)

        if bool(self.eps) == bool(self.total_work): 
            raise Exception("MLMC: Prescribe either eps or total_work")
        self.has_simulation_postproc = True


    def setup(self, prms):
        """
        Set up data structure for an MLMC simulation. 
        Called from config for all the MLMC-specific parts of the setup.

        The difference levels with a common sample set are called 'level' here. 
        Each level consists of a coarse and a fine sub-level 
        (there is no coarse sub-level on the coarsest level )
        Level batches are initialized according to chosen solver.
        """

        SolverLoc = Solver.subclass(prms["solver"]["_type"])
        # MachineLoc = Machine.subclass(prms["machine"]["_type"])

        # initialize StochVars
        self.stoch_vars = config.config_list("stoch_vars", 
                                             prms, 
                                             StochVar.create,
                                             SolverLoc)

        sampling_prms = prms["sampling"] if "sampling" in prms else {}
        
        for i_stage, stage in enumerate(self.stages): 
            # initialize sublevels
            subs_fine = config.config_list("solver", 
                                           prms, 
                                           Solver.create_by_stage_from_list, 
                                           i_stage, 
                                           stage.name, 
                                           self, 
                                           stage.__class__, 
                                           sub_list_name="levels")
            n_levels = len(subs_fine)
            subs_coarse=[Empty()]
            subs_coarse.extend(copy.deepcopy(subs_fine[:-1]))
            if i_stage == 0: 
                samplers = [self.setup_samples(sampling_prms,s.n_warmup_samples) for s in subs_fine]

            # initialize levels and connect to sublevels
            iterator=zip(range(1,len(subs_fine)+1),subs_fine,subs_coarse,samplers)
            stage.levels = [self.setup_level(*args,n_levels) for args in iterator]

            #add batches to each stage
            stage.batches = []
            for level in stage.levels:
                stage.batches.extend(level.sublevels)

        self.levels = self.stages[-1].levels 

        register_batch_series(self.stages) 

        iter_postproc = config.config_postproc_stage(prms,self,"iteration_postproc")
        self.stages.append(iter_postproc)
        self.simulation_postproc = config.config_postproc_stage(prms,self,"simulation_postproc")

        # set up quantities of interest
        self.qois_optimize = []
        for level in self.levels:
            level.n_optimize = 0
            level.qois = []
            for sub_dict in prms["qois"]: 
                self.setup_qoi(sub_dict,level,SolverLoc.QoI)
            if level.n_optimize != 1: 
                raise Exception("Please specify exactly "
                                "one QoI to optimize")

        self.internal_qois = []
        for i,sub_dict in enumerate(prms["qois"]): 
            QoILoc = Solver.subclass(prms["solver"]["_type"]).QoI
            qoi = QoILoc.create_by_stage(sub_dict,"simulation_postproc",self)
            # qoi.name = "combinelevels"
            qoi.participants = [l.qois[i] for l in self.levels]
            if qoi.internal: 
                self.internal_qois.append(qoi)
            else:
                self.simulation_postproc.batches.append(qoi)

        if self.use_ci: 
            self.ci_conf_loc = 1.- (1.-self.ci_conf_tot) / (3.*len(self.levels))

    def setup_level(self, i, sub_fine, sub_coarse, sampler, n_levels):
        """
        set up a level, connect to its sublevels, and 
        add the samples container
        """ 
        level=Empty()
        level.name = str(i)

        level.samples = sampler
        level.samples.seed_id = n_levels - i # = 0 for finest level to be consistent with MFMC

        sublevels = [sub_fine, sub_coarse]
        for sub, sub_name in zip(sublevels,['f', 'c']):
            sub.samples = level.samples
            sub.name = level.name+sub_name
        if i == 1:
            # remove coarse on coarsest level
            sublevels = [sub_fine]

        level.sublevels = sublevels
        level.internal_qois = []
        return level


    def setup_samples(self,prms,n_warmup): 
        """
        Set up sampling method for a level
        """
        samples = MonteCarlo(prms)
        samples.stoch_vars = self.stoch_vars # copy to each sampler
        # initialize sample size
        samples.n = n_warmup
        samples.n_previous = 0
        return samples


    def setup_qoi(self, subdict, level, QoILoc):
        """ 
        Set up quantity of interest for a level and make the 
        sublevels its participants
        """
        qoi = QoILoc.create_by_stage(subdict,"iteration_postproc", self)
        qoi.participants = level.sublevels
        qoi.name = level.name+"_"+qoi.cname
        qoi.levelname = level.name

        qoi.samples = level.samples

        if qoi.optimize: 
            level.n_optimize += 1
            self.qois_optimize.append(qoi)
        level.qois.append(qoi)

        if qoi.internal: 
            # stochastic post-proc is done internally 
            level.internal_qois.append(qoi)
            # initialize sums: 
            # Storing these sums, mean, variance and difference variance can be calculated
            # Without storing the solution at every sample point. Sums can be updated 
            # after every iteration, then estimators can be updated also.
            qoi.u_fine_sum      = 0.
            qoi.u_fine_sq_sum   = 0.
            qoi.u_coarse_sum    = 0.
            qoi.u_coarse_sq_sum = 0.
            qoi.du_sq_sum       = 0.
            if self.use_ci: 
                if self.dof_adj: 
                    qoi.du_e3_sum = 0.
                    qoi.du_e4_sum = 0.
                qoi.w_sum = 0.
                qoi.w_sq_sum = 0.
        else:
            # stochastic post-proc is done by solver-specific tool 
            # (useful for large field-valued QoIs)
            if self.use_ci: 
                raise Exception("Confidence intervals only implemented for internal QoIs")
            self.stages[1].batches.append(qoi)


    def internal_iteration_postproc(self): 
        """
        Calculate sigma^2 for QoI's internally. 
        Used for scalar or small vectorial QoI's
        """
        for level in self.levels: 
            if level.samples.n == 0: 
                continue
            for qoi in level.internal_qois: 
                u_out = qoi.get_response()
                if len(u_out) == 2: 
                    u_fine, u_coarse = u_out
                else: 
                    u_fine, u_coarse = u_out[0], 0.*u_out[0]
                n = qoi.samples.n_previous+qoi.samples.n
                # Storing these sums, mean, variance and difference variance can be calculated
                # Without storing the solution at every sample point. Sums can be updated 
                # after every iteration, then estimators can be updated also.
                qoi.u_fine_sum      += sum(u_fine)
                qoi.u_fine_sq_sum   += sum(u_fine**2)
                qoi.u_coarse_sum    += sum(u_coarse)
                qoi.u_coarse_sq_sum += sum(u_coarse**2)
                qoi.du_sq_sum       += sum([(f-c)**2 for f,c in zip(u_fine,u_coarse)])
                qoi.SigmaSq = ( qoi.du_sq_sum - (qoi.u_fine_sum-qoi.u_coarse_sum)**2 / n) / (n-1)
                qoi.SigmaSq = qoi.integrate(qoi.SigmaSq)
                if self.use_ci: 

                    ## TODO: hack for convergence test: 
                    ## In convtest, the simulation setup is modified later and use_ci and dof_adj may be switched on.
                    ## In this case, the necessary quantities were not initialized during the (previous) config.

                    # if qoi.samples.n_previous == 0: 
                        # if self.dof_adj: 
                            # qoi.du_e3_sum = 0.
                            # qoi.du_e4_sum = 0.
                        # qoi.w_sum = 0.
                        # qoi.w_sq_sum = 0.
                        # self.ci_conf_loc = 1.- (1.-self.ci_conf_tot) / (3.*len(self.levels))
                    ## end hack

                    # get upper and lower bound for level difference variance
                    if self.dof_adj: 
                        qoi.du_e3_sum   += sum([(f-c)**3 for f,c in zip(u_fine,u_coarse)])
                        qoi.du_e4_sum   += sum([(f-c)**4 for f,c in zip(u_fine,u_coarse)])
                        mu = (qoi.u_fine_sum-qoi.u_coarse_sum)/n
                        mom4 = qoi.du_e4_sum - 4.*mu*qoi.du_e3_sum + 6.*mu**2*qoi.du_sq_sum - 4.*mu**3*mu*n + n*mu**4
                        ex_kurt = n*(n+1.)/((n-1.)*(n-2.)*(n-3.))*mom4/qoi.SigmaSq**2 - 3*(n-1.)**2/((n-2.)*(n-3.))
                        dof = 2*n/(ex_kurt+2*n/(n-1.))
                    else: 
                        dof = n-1
                    alpha = (1.-self.ci_conf_loc)*2.
                    qoi.v_lower = dof*qoi.SigmaSq/chi2.interval(1.-alpha,dof)[1]
                    qoi.v_upper = dof*qoi.SigmaSq/chi2.interval(1.-alpha,dof)[0]

                    # get upper and lower bound for mean computational work per model evaluation.
                    # potential improvement (TODO): more explicit / specific case distinction
                    try: 
                        # if vector w of work for each sample point evaluation is available, 
                        # then upper and lower bound can be calculated
                        w = np.array(qoi.participants[0].w)
                        if len(qoi.participants)>1:
                            w += np.array(qoi.participants[1].w)
                        qoi.w_sum += np.sum(w)
                        qoi.w_sq_sum += np.sum(w**2)
                        mean_w = qoi.w_sum/n
                        var_w  = (qoi.w_sq_sum-(qoi.w_sum**2)/n)/(n-1.)
                        qoi.w_lower = mean_w - norm.interval(1.-alpha)[1]*safe_sqrt(var_w/n)
                        qoi.w_upper = mean_w + norm.interval(1.-alpha)[1]*safe_sqrt(var_w/n)
                    except: 
                        # fallback: if implemented solver API only provides mean work, then set
                        # upper and lower bound for mean work to that value (corresponds to zero 
                        # variance in compuational work across samples)
                        qoi.work_mean_static = qoi.work_mean
                        qoi.w_lower = qoi.work_mean_static
                        qoi.w_upper = qoi.work_mean_static


    def internal_simulation_postproc(self): 
        """
        Calculate mean and variance estimators internally at end of computation 
        (The alternative is external post-processing using a solver-specific tool, 
        which might be necessary for large field-valued QoIs)
        """

        if not self.internal_qois:
            return

        # prepare stdout
        table = PrettyTable()
        table.field_names = ["QoI","Mean","Standard Deviation"]
         
        for qoi in self.internal_qois: 
            qoi.mean, qoi.variance = 0., 0.
            # loop over levels
            for p in qoi.participants:
                n = p.samples.n_previous
                # level mean
                p.mean = (p.u_fine_sum - p.u_coarse_sum)/n
                # level variance
                f = (p.u_fine_sq_sum - p.u_fine_sum**2/n)
                c = (p.u_coarse_sq_sum - p.u_coarse_sum**2/n)
                p.variance = (f - c) / (n-1)

                # add to sum
                qoi.mean += p.mean
                qoi.variance += p.variance
            qoi.stddev = safe_sqrt(qoi.variance)

            # update stdout
            if isinstance(qoi.mean,float):
                table.add_row([qoi.cname,qoi.mean,qoi.stddev])
            else:
                table.add_row([qoi.cname + " (Int.)",
                               qoi.integrate(qoi.mean),
                               np.sqrt(qoi.integrate(qoi.variance))])

            # Optionally write result to file (if implemented for this QoI)
            # Especially useful for field-valued QoIs
            qoi.write_to_file()

        # copy first QoI estimators to main simulation attributes as result
        self.mean = self.internal_qois[0].mean
        self.stddev = self.internal_qois[0].stddev

        # stdout
        print_table(table)



    def prepare_next_iteration(self):
        """
        Compute number of samples for next iteration. 
        - evaluate sigma^2 and avg work. 
        - get optimal number of samples on every level
          (given prescribed eps or total work) 
        - approach this number carefully and iteratively
        """

        self.internal_iteration_postproc()

        self.all_est_total_work = []
        self.all_est_eps = []

        # Evaluate all QoIs one after another
        for i_qoi, qoi1 in enumerate(self.levels[0].qois): 

            is_opt = qoi1 is self.qois_optimize[0]

            # stdout
            print()
            add_str = " (OPTIMIZED!)" if is_opt else ""
            p_print("Evaluate QoI " + qoi1.cname + add_str)
            table = PrettyTable()
            table.field_names = ["Level","SigmaSq","mean work","ML_opt",
                                 "finished Samples","new Samples"]

            # build sum over levels of sqrt(sigma^2*w) and its upper or lower bound
            sum_sigma_w = 0.
            sum_sigma_w_bound = 0.

            for level in self.levels:

                qoi = level.qois[i_qoi]

                # new samples? => update level difference variances
                if qoi.samples.n > 0:
                    qoi.sigma_sq = float(qoi.get_derived_quantity("SigmaSq"))

                if qoi.samples.n_total_current > 1:

                    # estimated value
                    sum_sigma_w += safe_sqrt(qoi.sigma_sq*qoi.work_mean)

                    # upper or lower bounds
                    if self.use_ci: 
                        if self.eps: 
                            sum_sigma_w_bound += safe_sqrt(qoi.v_lower*qoi.w_lower)
                        elif self.total_work: 
                            sum_sigma_w_bound += safe_sqrt(qoi.v_upper*qoi.w_upper)


            # get number of sample points for next iteration
            # ----------------------------------------------

            for level in self.levels:

                qoi = level.qois[i_qoi]
                # get optimal numer of sample points on every level
                if self.eps: # prescribed RMSE
                    qoi.mlopt = (sum_sigma_w
                                 * safe_sqrt(qoi.sigma_sq/qoi.work_mean)
                                 / self.eps**2)
                elif self.total_work: # prescribed computational budget
                    qoi.mlopt = (self.total_work
                                 * safe_sqrt(qoi.sigma_sq/qoi.work_mean)
                                 / sum_sigma_w)

                qoi.mlopt_rounded = int(round(qoi.mlopt)) if qoi.mlopt > 1 \
                    else qoi.mlopt

                # approach mlopt carefully
                n_iter_remain = self.n_max_iter-self.current_iter.n
                if n_iter_remain > 0: 

                    if self.use_ci: # confidence interval-based approach
                        if self.eps: # precribed RMSE
                            qoi.ml_lower = (sum_sigma_w_bound
                                         * safe_sqrt(qoi.v_lower/qoi.w_upper)
                                         / self.eps**2)

                        elif self.total_work: # prescribed computational budget
                            qoi.ml_lower = (self.total_work
                                         * safe_sqrt(qoi.v_lower/qoi.w_upper)
                                         / sum_sigma_w_bound)

                        # factor to weight mlopt and its lower bound depending on iteration number
                        if self.n_max_iter == 2:
                            xi = 0.
                        else: 
                            xi = (self.n_max_iter-self.current_iter.n-1.)/(self.n_max_iter-2.)
                        n_total_new = xi*qoi.ml_lower + (1.-xi)*qoi.mlopt

                    else: # heuristic approach
                        expo = 1./sum(0.15**i for i in range(n_iter_remain))
                        n_total_new = qoi.mlopt**expo * qoi.samples.n_total_current**(1-expo)
                    qoi.n_new_samples = max(int(np.ceil(n_total_new))-qoi.samples.n_total_current , 0)

                else: # last iteration
                    qoi.n_new_samples = 0

                # prepare stdout
                table.add_row([qoi.levelname, qoi.sigma_sq, qoi.work_mean, qoi.mlopt_rounded,
                               qoi.samples.n_total_current, qoi.n_new_samples])

            print_table(table)

            # print stdout for global quantities (required computational budget or achieved RMSE)
            print()
            if self.eps: # precribed RMSE
                est_total_work = sum(
                    [l.qois[i_qoi].work_mean \
                        * max(l.qois[i_qoi].mlopt, 
                              l.qois[i_qoi].samples.n_total_current) \
                        for l in self.levels] )

                p_print("Estimated required total work to achieve prescribed "
                        "eps: %d core-seconds"%(int(est_total_work)))

                # save global estimates as attribute of simulation 
                self.all_est_total_work.append(est_total_work)
                if is_opt: 
                   self.est_total_work=est_total_work

            elif self.total_work: # prescribed computational budget
                est_eps_sq = sum(
                    [l.qois[i_qoi].sigma_sq \
                        / max(l.qois[i_qoi].mlopt, 
                              l.qois[i_qoi].samples.n_total_current) \
                        for l in self.levels] )
                est_eps = np.sqrt(est_eps_sq)

                p_print("Estimated achieved RMSE for given total work: %e" \
                        %(est_eps))

                # save global estimates as attribute of simulation 
                self.all_est_eps.append(est_eps)
                if is_opt: 
                   self.est_eps=est_eps

        # Update sample size for next iteration
        for qoi in self.qois_optimize:
            qoi.samples.n_previous += qoi.samples.n
            qoi.samples.n = qoi.n_new_samples

        # check if iteration loop should be exited
        self.iter_loop_finished = len(self.stages[0].active_batches) == 0


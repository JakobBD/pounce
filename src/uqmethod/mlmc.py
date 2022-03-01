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
        "n_max_iter" : "NODEFAULT",
        "eps" : None,
        "total_work" : None,
        "use_ci" : False,
        "ci_conf_tot" : 0.95,
        "dof_adj" : False
        }

    defaults_add = { 
        "Solver": { 
            "n_warmup_samples": "NODEFAULT"
            },
        "QoI": {
            "optimize": False
            }
        }

    def __init__(self, input_prm_dict):
        super().__init__(input_prm_dict)
        if bool(self.eps) == bool(self.total_work): 
            raise Exception("MLMC: Prescribe either eps or total_work")
        self.has_simulation_postproc = True

    def setup(self, prms):
        """
        Set up data structure for an MLMC simulation
        Includes levels and sublevels, quantities of interest, 
        each initiallized according to chosen solver, 
        and stages (main simulation and post proc) according to
        chosen machine.
        """

        SolverLoc = Solver.subclass(prms["solver"]["_type"])
        # MachineLoc = Machine.subclass(prms["machine"]["_type"])

        # initialize StochVars
        self.stoch_vars = config.config_list("stoch_vars", prms, StochVar.create,
                                             SolverLoc)

        sampling_prms = prms["sampling"] if "sampling" in prms else {}
        
        for i_stage, stage in enumerate(self.stages): 
            # initialize sublevels
            subs_fine = config.config_list("solver", prms, Solver.create_by_stage_from_list, i_stage, 
                                           stage.name, self, stage.__class__, sub_list_name="levels")
            n_levels = len(subs_fine)
            subs_coarse=[Empty()]
            subs_coarse.extend(copy.deepcopy(subs_fine[:-1]))
            if i_stage == 0: 
                samplers = [self.setup_samples(sampling_prms,s.n_warmup_samples) for s in subs_fine]
            # initialize levels and connect to sublevels
            iterator=zip(range(1,len(subs_fine)+1),subs_fine,subs_coarse,samplers)
            stage.levels = [self.setup_level(*args,n_levels) for args in iterator]

            #setup stages 
            stage.batches = []
            for level in stage.levels:
                stage.batches.extend(level.sublevels)

        self.levels = self.stages[-1].levels 
        register_batch_series(self.stages) 

        iter_postproc = config.config_pp_mach(prms,self,"iteration_postproc")
        self.stages.append(iter_postproc)
        self.simulation_postproc = config.config_pp_mach(prms,self,"simulation_postproc")

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
        level.samples.seed_id = n_levels - i # = 0 for finest level
        sublevels = [sub_fine, sub_coarse]
        for sub, sub_name in zip(sublevels,['f', 'c']):
            sub.samples = level.samples
            sub.name = level.name+sub_name
        if i == 1:
            sublevels = [sub_fine]
        level.sublevels = sublevels
        level.internal_qois = []
        return level

    def setup_samples(self,prms,n_warmup): 
        samples = MonteCarlo(prms)
        samples.stoch_vars = self.stoch_vars
        samples.n = n_warmup
        samples.n_previous = 0
        return samples

    def setup_qoi(self, subdict, level, QoILoc):
        """ 
        set up quantity of interest for a level and make the 
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
            level.internal_qois.append(qoi)
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
                qoi.u_fine_sum      += sum(u_fine)
                qoi.u_fine_sq_sum   += sum(u_fine**2)
                qoi.u_coarse_sum    += sum(u_coarse)
                qoi.u_coarse_sq_sum += sum(u_coarse**2)
                qoi.du_sq_sum       += sum([(f-c)**2 for f,c in zip(u_fine,u_coarse)])
                qoi.SigmaSq = ( qoi.du_sq_sum - (qoi.u_fine_sum-qoi.u_coarse_sum)**2 / n) / (n-1)
                qoi.SigmaSq = qoi.integrate(qoi.SigmaSq)
                if self.use_ci: 
                    # # TODO: hack for convtest
                    # if qoi.samples.n_previous == 0: 
                        # if self.dof_adj: 
                            # qoi.du_e3_sum = 0.
                            # qoi.du_e4_sum = 0.
                        # qoi.w_sum = 0.
                        # qoi.w_sq_sum = 0.
                        # self.ci_conf_loc = 1.- (1.-self.ci_conf_tot) / (3.*len(self.levels))
                    # # end hack
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

                    # TODO: this is dirty
                    try: 
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
                        qoi.work_mean_static = qoi.work_mean
                        qoi.w_lower = qoi.work_mean_static
                        qoi.w_upper = qoi.work_mean_static


    def internal_simulation_postproc(self): 
        """
        Calculate sigma^2 for QoI's internally. 
        Used for scalar or small vectorial QoI's
        """
        if not self.internal_qois:
            return
        table = PrettyTable()
        table.field_names = ["QoI","Mean","Standard Deviation"]
        for qoi in self.internal_qois: 
            qoi.mean, qoi.variance = 0., 0.
            for p in qoi.participants: 
                n = p.samples.n_previous
                p.mean = (p.u_fine_sum - p.u_coarse_sum)/n
                f = (p.u_fine_sq_sum - p.u_fine_sum**2/n)
                c = (p.u_coarse_sq_sum - p.u_coarse_sum**2/n)
                p.variance = (f - c) / (n-1)
                qoi.mean += p.mean
                qoi.variance += p.variance
            qoi.stddev = safe_sqrt(qoi.variance)
            if isinstance(qoi.mean,(float,np.float)):
                table.add_row([qoi.cname,qoi.mean,qoi.stddev])
            else:
                table.add_row([qoi.cname + " (Int.)",
                               qoi.integrate(qoi.mean),
                               np.sqrt(qoi.integrate(qoi.variance))])
            qoi.write_to_file()
        self.mean = self.internal_qois[0].mean
        self.stddev = self.internal_qois[0].stddev
        print_table(table)


    def prepare_next_iteration(self):
        """
        Compute number of samples for next iteration. 
        - evaluate sigma^2 and avg work. 
        - get optimal number of samples on every level
          (given prescribed eps or total work) 
        - approach this numbr carefully and iteratively
        """

        self.internal_iteration_postproc()

        self.all_est_total_work = []
        self.all_est_eps = []
        for i_qoi, qoi1 in enumerate(self.levels[0].qois): 
            print()
            is_opt = qoi1 is self.qois_optimize[0]
            add_str = " (OPTIMIZED!)" if is_opt else ""
            p_print("Evaluate QoI " + qoi1.cname + add_str)
            table = PrettyTable()
            table.field_names = ["Level","SigmaSq","mean work","ML_opt",
                                 "finished Samples","new Samples"]

            # build sum over levels of sqrt(sigma^2/w)
            sum_sigma_w = 0.
            sum_sigma_w_bound = 0.
            # for qoi in self.qois_optimize:
            for level in self.levels:
                qoi = level.qois[i_qoi]
                if qoi.samples.n > 0:
                    qoi.sigma_sq = float(qoi.get_derived_quantity("SigmaSq"))
                if qoi.samples.n_total_current > 1:
                    sum_sigma_w += safe_sqrt(qoi.sigma_sq*qoi.work_mean)
                    if self.use_ci: 
                        if self.eps: 
                            sum_sigma_w_bound += safe_sqrt(qoi.v_lower*qoi.w_lower)
                        elif self.total_work: 
                            sum_sigma_w_bound += safe_sqrt(qoi.v_upper*qoi.w_upper)


            # for qoi in self.qois_optimize:
            for level in self.levels:
                qoi = level.qois[i_qoi]
                if self.eps: 
                    qoi.mlopt = (sum_sigma_w
                                 * safe_sqrt(qoi.sigma_sq/qoi.work_mean)
                                 / self.eps**2)
                elif self.total_work: 
                    qoi.mlopt = (self.total_work
                                 * safe_sqrt(qoi.sigma_sq/qoi.work_mean)
                                 / sum_sigma_w)

                qoi.mlopt_rounded = int(round(qoi.mlopt)) if qoi.mlopt > 1 \
                    else qoi.mlopt

                n_iter_remain = self.n_max_iter-self.current_iter.n
                if n_iter_remain > 0: 
                    if self.use_ci: 
                        if self.eps: 
                            qoi.ml_lower = (sum_sigma_w_bound
                                         * safe_sqrt(qoi.v_lower/qoi.w_upper)
                                         / self.eps**2)
                        elif self.total_work: 
                            qoi.ml_lower = (self.total_work
                                         * safe_sqrt(qoi.v_lower/qoi.w_upper)
                                         / sum_sigma_w_bound)
                        if self.n_max_iter == 2:
                            xi = 0.
                        else: 
                            xi = (self.n_max_iter-self.current_iter.n-1.)/(self.n_max_iter-2.)
                            # xi = 1.
                        n_total_new = xi*qoi.ml_lower + (1.-xi)*qoi.mlopt
                    else: 
                        # slowly approach mlopt... heuristic solution
                        expo = 1./sum(0.15**i for i in range(n_iter_remain))
                        n_total_new = qoi.mlopt**expo * qoi.samples.n_total_current**(1-expo)
                    qoi.n_new_samples = max(int(np.ceil(n_total_new))-qoi.samples.n_total_current , 0)
                else: 
                    qoi.n_new_samples = 0

                table.add_row([qoi.levelname, qoi.sigma_sq, qoi.work_mean, qoi.mlopt_rounded,
                               qoi.samples.n_total_current, qoi.n_new_samples])

            print_table(table)

            print()
            if self.eps: 
                est_total_work = sum(
                    [l.qois[i_qoi].work_mean*max(l.qois[i_qoi].mlopt, l.qois[i_qoi].samples.n_total_current) \
                        for l in self.levels])
                p_print("Estimated required total work to achieve prescribed "
                        "eps: %d core-seconds"%(int(est_total_work)))
                self.all_est_total_work.append(est_total_work)
                if is_opt: 
                   self.est_total_work=est_total_work
            elif self.total_work: 
                est_eps = sum(
                    [l.qois[i_qoi].sigma_sq/max(l.qois[i_qoi].mlopt, l.qois[i_qoi].samples.n_total_current) \
                        for l in self.levels])
                est_eps = np.sqrt(est_eps)
                p_print("Estimated achieved RMSE for given total work: %e" \
                        %(est_eps))
                self.all_est_eps.append(est_eps)
                if is_opt: 
                   self.est_eps=est_eps


        # Set optimized QoI valid
        for qoi in self.qois_optimize:
            qoi.samples.n_previous += qoi.samples.n
            qoi.samples.n = qoi.n_new_samples


        self.iter_loop_finished = len(self.stages[0].active_batches) == 0

        # sys.exit() # TODO DEBUG




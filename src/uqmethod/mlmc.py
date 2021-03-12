import numpy as np
import os
import copy
from prettytable import PrettyTable
from scipy.stats import chi2, norm

from .uqmethod import UqMethod
from helpers.printtools import *
from helpers.tools import *
from sampling.sampling import MonteCarlo
from solver.solver import Solver
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

    defaults_ = {
        "n_max_iter" : "NODEFAULT",
        "eps" : None,
        "total_work" : None,
        "use_ci" : False,
        "ci_conf_tot" : 0.95,
        "dof_adj" : False,
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
        if bool(self.eps) == bool(self.total_work): 
            raise Exception("MLMC: Prescribe either eps or total_work")
        self.has_simulation_postproc = True
        if self.reset_seed:
            p_print("Reset RNG seed to 0")
            np.random.seed(0)

    def setup(self, prms):
        """
        Set up data structure for an MLMC simulation
        Includes levels and sublevels, quantities of interest, 
        each initiallized according to chosen solver, 
        and stages (main simulation and post proc) according to
        chosen machine.
        """

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

        self.internal_qois = []
        for i,sub_dict in enumerate(prms["qois"]): 
            SolCls = Solver.subclass(prms["solver"]["_type"])
            QoILoc = SolCls.QoI
            qoi = QoILoc.create_by_stage("simulation_postproc",sub_dict,SolCls,self)
            # qoi.name = "combinelevels"
            qoi.participants = [l.qois[i] for l in self.levels]
            if qoi.internal: 
                self.internal_qois.append(qoi)
            else:
                self.simulation_postproc.batches.append(qoi)

        if self.use_ci: 
            self.ci_conf_loc = 1.- (1.-self.ci_conf_tot) / (3.*len(self.levels))

    def setup_level(self, i, sub_fine, sub_coarse):
        """
        set up a level, connect to its sublevels, and 
        add the samples container
        """ 
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
        level.internal_qois = []
        return level

    def setup_qoi(self, subdict, level):
        """ 
        set up quantity of interest for a level and make the 
        sublevels its participants
        """
        SolCls = level.sublevels[0].__class__
        QoILoc = SolCls.QoI
        qoi = QoILoc.create_by_stage("iteration_postproc",subdict, SolCls, self)
        qoi.participants = level.sublevels
        qoi.name = level.name+"_"+qoi.qoiname
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
                if self.use_ci: 
                    # TODO: hack for convtest
                    if qoi.samples.n_previous == 0: 
                        if self.dof_adj: 
                            qoi.du_e3_sum = 0.
                            qoi.du_e4_sum = 0.
                        qoi.w_sum = 0.
                        qoi.w_sq_sum = 0.
                        self.ci_conf_loc = 1.- (1.-self.ci_conf_tot) / (3.*len(self.levels))
                    # end hack
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

                    w = np.array(qoi.participants[0].w)
                    if len(qoi.participants)>1:
                        w += np.array(qoi.participants[1].w)
                    qoi.w_sum += np.sum(w)
                    qoi.w_sq_sum += np.sum(w**2)
                    mean_w = qoi.w_sum/n
                    var_w  = (qoi.w_sq_sum-(qoi.w_sum**2)/n)/(n-1.)
                    qoi.w_lower = mean_w - norm.interval(1.-alpha)[1]*safe_sqrt(var_w/n)
                    qoi.w_upper = mean_w + norm.interval(1.-alpha)[1]*safe_sqrt(var_w/n)


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
            if qoi.do_print:
                table.add_row([qoi.qoiname,qoi.mean,qoi.stddev])
            qoi.write_to_file()
        self.mean = self.internal_qois[0].mean
        self.stddev = self.internal_qois[0].stddev
        print_table(table)


    @classmethod
    def default_yml(cls,d):
        """
        MLMC specific layout of the default yml file.
        """
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

    def prepare_next_iteration(self):
        """
        Compute number of samples for next iteration. 
        - evaluate sigma^2 and avg work. 
        - get optimal number of samples on every level
          (given prescribed eps or total work) 
        - approach this numbr carefully and iteratively
        """

        self.internal_iteration_postproc()

        table = PrettyTable()
        table.field_names = ["Level","SigmaSq","mean work","ML_opt",
                             "finished Samples","new Samples"]

        # build sum over levels of sqrt(sigma^2/w)
        sum_sigma_w = 0.
        sum_sigma_w_bound = 0.
        for qoi in self.qois_optimize:
            if qoi.samples.n > 0:
                qoi.sigma_sq = float(qoi.get_derived_quantity("SigmaSq"))
                qoi.get_work_mean()
            if qoi.samples.n_previous+qoi.samples.n > 0:
                sum_sigma_w += safe_sqrt(qoi.sigma_sq*qoi.work_mean)
                if self.use_ci: 
                    if self.eps: 
                        sum_sigma_w_bound += safe_sqrt(qoi.v_lower*qoi.w_lower)
                    elif self.total_work: 
                        sum_sigma_w_bound += safe_sqrt(qoi.v_upper*qoi.w_upper)


        for qoi in self.qois_optimize:
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
            qoi.samples.n_previous += qoi.samples.n

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
                    n_total_new = qoi.mlopt**expo * qoi.samples.n**(1-expo)
                qoi.samples.n = max(int(np.ceil(n_total_new))-qoi.samples.n_previous , 0)
            else: 
                qoi.samples.n = 0

            if qoi.do_print:
                table.add_row([qoi.levelname, qoi.sigma_sq, qoi.work_mean, qoi.mlopt_rounded,
                               qoi.samples.n_previous, qoi.samples.n])

        print_table(table)

        print()
        if self.eps: 
            self.est_total_work = sum(
                [q.work_mean*max(q.mlopt, q.samples.n_previous) \
                    for q in self.qois_optimize])
            p_print("Estimated required total work to achieve prescribed "
                    "eps: %d core-seconds"%(int(self.est_total_work)))
        elif self.total_work: 
            self.est_eps = sum(
                [q.sigma_sq/max(q.mlopt, q.samples.n_previous) \
                    for q in self.qois_optimize])
            self.est_eps = np.sqrt(self.est_eps)
            p_print("Estimated achieved RMSE for given total work: %e" \
                    %(self.est_eps))

        self.iter_loop_finished = len(self.stages[0].active_batches) == 0




import numpy as np
import os
import copy

from .uqmethod import UqMethod
from helpers.printtools import *
from helpers.tools import *


@UqMethod.register_subclass('mlmc')
class Mlmc(UqMethod):

    subclass_defaults={
        "n_max_iter" : "NODEFAULT",
        "tolerance" : "NODEFAULT",
        "reset_seed" : False
        }

    level_defaults={
        "n_warmup_samples": "NODEFAULT",
        "solver_prms" : {},
        }

    qoi_defaults={
        "exe_paths": {"iteration_postproc": "", "simulation_postproc": ""},
        "optimize": False
        }

    def __init__(self,input_prm_dict):
        super().__init__(input_prm_dict)
        self.has_simulation_postproc=True
        if self.reset_seed:
            p_print("Reset RNG seed to 0")
            np.random.seed(0)

    def setup_batches(self,qois):
        self.all_sublevels=[]
        for i_level,level in enumerate(self.levels):
            level.name=str(i_level+1)
            level.samples=Empty()
            level.samples.n=level.n_warmup_samples
            level.samples.n_previous = 0
            level.sublevels= [ SubLevel(level,level,'f') ]
            self.all_sublevels.append(level.sublevels[-1])
            if i_level > 0:
                level.sublevels.append(SubLevel(level,self.levels[i_level-1],'c'))
                self.all_sublevels.append(level.sublevels[-1])
            self.setup_qois(qois,level)
            for qoi in level.qois:
                qoi.participants=level.sublevels
                qoi.name="postproc_"+level.name
                qoi.avg_walltime=level.avg_walltime_postproc
        self.get_active_batches()
        self.setup_qois(qois,self)
        for qoi in self.qois:
            qoi.name="combinelevels"
            qoi.participants=self.levels

    @staticmethod
    def setup_qois(qois_in,level):
        level.qois=[]
        for qoi_in in qois_in:
            # init qoi with exe_paths, _type etc
            qoi=copy.deepcopy(qoi_in)
            level.qois.append(qoi)
            if qoi.optimize: 
                level.qoi_optimize=qoi
        if len([qoi for qoi in qois_in if qoi.optimize ]) != 1: 
            raise Exception("Please specify exactly one QoI to optimize")

    def get_active_batches(self):
        self.active_sublevels=[sub for sub in self.all_sublevels if sub.samples.n > 0]
        self.active_levels=[l for l in self.levels if l.samples.n > 0]
        # external naming
        self.solver_batches = self.active_sublevels
        self.postproc_batches=[qoi for level in self.active_levels for qoi in level.qois]

        self.do_continue = len(self.active_levels) > 0

    def get_nodes_and_weights(self):
        for level in self.active_levels:
            level.samples.nodes=[]
            for var in self.stoch_vars:
                level.samples.nodes.append(var.draw_samples(level.samples.n))
            level.samples.nodes=np.transpose(level.samples.nodes)
            level.samples.weights=[]
        p_print("Number of current samples for this iteration:")
        [p_print("  Level %2s: %6d samples"%(level.name,level.samples.n)) for level in self.levels]


    def get_new_n_current_samples(self,solver):

        stdout_table=StdOutTable( "sigma_sq","work_mean" ,"mlopt" ,"samples__n_previous","samples__n")
        stdout_table.descriptions("SigmaSq","mean work","ML_opt","finished Samples"  ,"new Samples")

        # build sum over levels of sqrt(sigma^2/w)
        sum_sigma_w = 0.
        for level in self.levels:
            if level.samples.n > 0:
                level.sigma_sq = solver.get_postproc_quantity_from_file(level.qoi_optimize,"SigmaSq")
                work_mean = solver.get_work_mean(level.qoi_optimize)
                if level.samples.n_previous > 0:
                    level.work_mean = (level.samples.n_previous*level.work_mean + level.samples.n*work_mean)/\
                                          (level.samples.n+level.samples.n_previous)
                else:
                    level.work_mean = work_mean
            if level.samples.n_previous+level.samples.n > 0:
                sum_sigma_w += safe_sqrt(level.sigma_sq*level.work_mean)

        for level in self.levels:
            #TODO: add formula for given max_work
            level.mlopt = sum_sigma_w * safe_sqrt(level.sigma_sq/level.work_mean) / (self.tolerance*self.tolerance/4.)
            level.samples.n_previous += level.samples.n
            level.samples.n = max(int(np.ceil(level.mlopt))-level.samples.n_previous , 0)
            stdout_table.update(level)

        stdout_table.p_print("Level")

        self.get_active_batches()


class SubLevel():
    def __init__(self,diff_level,resolution_level,name):
        self.solver_prms = resolution_level.solver_prms
        self.cores_per_sample = resolution_level.cores_per_sample
        self.avg_walltime = resolution_level.avg_walltime
        self.samples=diff_level.samples
        self.name=diff_level.name+name



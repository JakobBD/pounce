import sys,os
import inspect
import copy
import types

from helpers.baseclass import BaseClass
from helpers.printtools import *
from helpers.tools import *
from helpers import config
from helpers import globels
# from uqmethod.uqmethod import UqMethod


class Batch(BaseClass):
    """
    A batch consists of a set of computations.
    This can be either simulations or post-processing.
    It is therefore the parent class to Solver and QoI
    """

    defaults_ = {
        'cores_per_sample' : 1,
        "exe_path": "NODEFAULT"
        }

    def __init__(self,*args): 
        super().__init__(*args)
        self.sum_work = { 0 : 0. }
        self.current_avg_work = 0.

    def check_finished(self):
        """
        default: do not carry out a check after a batch is run
        simply assume all are finished.
        """
        return True

    def prepare(self):
        """
        placeholder; should be overwritten by each subclass.
        """
        raise Exception("not yet implemented")

    @property
    def full_name(self): 
        l = [globels.project_name, self.name, globels.sim.current_iter.n]
        if hasattr(self,"stage_name"):
            l += self.stage_name 
        return "_".join(l)

    @property
    def logfile_names(self): 
        return [self.full_name+self.run_id(i+1)+"_LOG.dat" for i in range(self.n_runs)]

    @property
    def errfile_names(self): 
        return [self.full_name+self.run_id(i+1)+"_ERR.dat" for i in range(self.n_runs)]

    @property
    def n_runs(self):
        return len(self.run_commands)

    def run_id(self,i):
        """
        needed to distinguish input and output files 
        in the case of several runs per batch (i.e. if one solver is
        run several times instead of a loop over all samples as part 
        of the external solver)
        """
        if self.n_runs == 1:
            return ""
        else:
            return "_run"+str(i)


    @classmethod
    def create_by_stage(cls,prms,stage_name,*args): 
        typename = prms["_type"]
        TypeSub =cls.subclass(typename)
        stage_subs = []
        TypeSub.recursive_subclasses(stage_subs,TypeSub) 
        for StageSub in stage_subs: 
            if StageSub.stages & {stage_name, "all"}:
                inst = StageSub(prms,*args)
                inst.stage_name = stage_name
                return inst
        raise InputPrmError(
            "no {} subclass for stage {}".format(TypeSub,stage_name))


    @property
    def avg_work(self):
        """
        Wrapper: get mean work of current simulation, then update 
        total mean work
        """
        n_samples_tot = self.samples.n+self.samples.n_previous
        if not n_samples_tot in self.sum_work: 
            self.sum_work[n_samples_tot] = self.samples.n*self.current_avg_work \
                                         + self.sum_work[self.samples.n_previous]
        return self.sum_work[n_samples_tot] / n_samples_tot


def register_batch_series(stages): 
    """
    to be called before postproc is appended
    """
    l = [s.batches for s in stages]
    l = [list(i) for i in zip(*l)]
    for i_stage, stage in enumerate(stages): 
        for bl,b in zip(l,stage.batches):
            b.other_stages = bl


class Solver(Batch):
    """
    Solver is the parent class to subclasses which include 
    routines specidifc to the used solver. Here only the main
    simulation is considered as opposed to the according QoI's, 
    which are defined separately. 
    """

    stages = {"all"}

    defaults_ = {
        'cores_per_sample' : "NODEFAULT",
        "solver_prms" :  "NODEFAULT"#,
        # "stages" :  [{}]
        }

    multi_sample = True
    is_surrogate = False

    @classmethod
    def create_by_stage_from_list(cls,prms,i_stage,stage_name,*args): 
        if "stages" in prms: 
            prms_loc = config.expand_prms_by_sublist(prms,"stages")[i_stage]
        else: 
            prms_loc = prms
        return cls.create_by_stage(prms_loc,stage_name,*args)


class QoI(Batch):
    """
    QoIs are always chosen automatically according 
    to the chosen Solver. 
    """

    multi_sample=False
    internal=False

    def write_to_file(self): 
        """ 
        optional for internal QoIs: Write result to file
        """
        pass 

    def integrate(self,qty): 
        """
        For vectorial internal QoIs: integration rule to obtain norm
        Scalar QoIs need not be integrated, hence scalar value is simplyy returned.
        """
        return qty

    @property
    def work_mean(self):
        w = 0.
        for p in self.participants: 
            w += sum(s.avg_work for s in p.other_stages) 
        return w



from . import *


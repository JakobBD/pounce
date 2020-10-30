import sys,os
import inspect
import copy
import types

from helpers.baseclass import BaseClass
from helpers.printtools import *
# from uqmethod.uqmethod import UqMethod


class Batch(BaseClass):
    """
    A batch consists of a set of computations.
    This can be either simulations or post-processing.
    It is therefore the parent class to Solver and QoI
    """

    defaults_ = {
        'cores_per_sample' : 1,
        'avg_walltime' : 300.,
        "exe_path": "NODEFAULT"
        }

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
    def logfile_names(self): 
        return ["log_"+self.name+self.run_id(i+1)+".dat" for i in range(self.n_runs)]

    @property
    def errfile_names(self): 
        return ["err_"+self.name+self.run_id(i+1)+".dat" for i in range(self.n_runs)]

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


class Solver(Batch):
    """
    Solver is the parent class to subclasses which include 
    routines specidifc to the used solver. Here only the main
    simulation is considered as opposed to the according QoI's, 
    which are defined separately. 
    """

    defaults_ = {
        'cores_per_sample' : "NODEFAULT",
        'avg_walltime' : "NODEFAULT",
        "solver_prms" :  "NODEFAULT"
        }

    def __init__(self,*args):
        super().__init__(*args)
        self.multi_sample=True


class QoI(Batch):
    """
    QoIs are always chosen automatically according 
    to the chosen Solver. 
    """

    def __init__(self,*args):
        super().__init__(*args)
        self.multi_sample=False
        self.internal=False

    @classmethod
    def create_by_stage(cls,stage_name,prms,SolCls,*args): 
        """
        Some QoI's contain prepare functions for different stages. 
        Here, the functions are renamed to the general "prepare" 
        according to the respective stage string given in "stage_name".
        QoI parameters are joined: some are given for all stages
        (prms_other), others are stage-specific (prms_loc).
        """
        if "stages" in prms:
            prms_loc=prms["stages"][stage_name]
            prms_other=copy.deepcopy(prms)
            del prms_other["stages"]
            prms_loc.update(prms_other)
        else: 
            prms_loc=prms
        tmp = prms_loc["_type"]
        prms_loc["_type"] = SolCls.name()+"_"+prms_loc["_type"]
        inst = cls.create(prms_loc,*args)
        prms_loc["_type"] = tmp
        if getattr(inst,"internal",False): 
            return inst

        method_name = "prepare_" + stage_name
        if method_name not in inst.__class__.__dict__:
            raise Exception(method_name 
                + " not found in class " + inst.__class__.__name__)
        inst.prepare=getattr(inst,method_name,None)
        return inst

    def get_work_mean(self):
        """
        Wrapper: get mean work of current simulation, then update 
        total mean work
        """
        work_mean = self.get_current_work_mean()
        if self.samples.n_previous > 0:
            self.work_mean = ((self.samples.n_previous*self.work_mean
                               + self.samples.n*work_mean)
                               / (self.samples.n+self.samples.n_previous))
        else:
            self.work_mean = work_mean


from . import *


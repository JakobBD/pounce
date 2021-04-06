import sys,os
import inspect
import copy
import types

from helpers.baseclass import BaseClass
from helpers.printtools import *
from helpers.tools import *
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


    @classmethod
    def create_by_stage(cls,stage_name,prms,*args): 
        """
        Some batches contain functions for different stages. 
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
        qoiname = prms_loc["_type"]
        QoiSub =cls.subclass(qoiname)
        # stagesub = QoiSub.subclass(stage_name,id_func=lambda c:c.stage)
        stage_subs = []
        QoiSub.recursive_subclasses(stage_subs,QoiSub) 
        for StageSub in stage_subs: 
            if StageSub.stages & {stage_name, "all"}:
                return StageSub(prms_loc,*args)
        raise InputPrmError(
            "no {} subclass for stage {}".format(QoiSub,stage_name))



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

    multi_sample = True
    is_surrogate = False


class QoI(Batch):
    """
    QoIs are always chosen automatically according 
    to the chosen Solver. 
    """

    multi_sample=False
    internal=False

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


from . import *


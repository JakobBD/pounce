import sys,os
import inspect
import copy
import types

from helpers.baseclass import BaseClass
from helpers.printtools import *
from uqmethod.uqmethod import UqMethod


class Batch(BaseClass):

    defaults_ = {
        'cores_per_sample' : 1,
        'avg_walltime' : 300.,
        "exe_path": "NODEFAULT"
        }

    def check_finished(self):
        """default: do not carry out a check after a batch is run
        """
        return True

    def prepare(self,simulation):
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
        if self.n_runs == 1:
            return ""
        else:
            return "_run"+str(i+1)


class Solver(Batch):

    defaults_ = {
        'cores_per_sample' : "NODEFAULT",
        'avg_walltime' : "NODEFAULT",
        "solver_prms" :  "NODEFAULT"
        }

    def __init__(self,*args):
        super().__init__(*args)
        self.multi_sample=True

    @classmethod
    def create(cls,class_dict,*args):
        inst = super().create(class_dict,*args)
        for arg in args:
            if isinstance(arg,UqMethod):
                inst.stoch_vars = arg.stoch_vars
                inst.uqmethod_prms = types.MethodType(arg.uqmethod_prms, inst)
                return inst
        raise Exception("no subclass of UqMethod found")

    def uqmethod_prms(self):
        """This is a placeholder. The actual routine is added to the batch 
        during setup from the chosen UqMethod (see above)
        """
        raise Exception("see routine description")


class QoI(Batch):

    def __init__(self,*args):
        super().__init__(*args)
        self.multi_sample=False

    @classmethod
    def create_by_stage(cls,name,prms,*args): 
        if "stages" in prms:
            prms_loc=prms["stages"][name]
            prms_other=copy.deepcopy(prms)
            del prms_other["stages"]
            prms_loc.update(prms_other)
        else: 
            prms_loc=prms
        inst = cls.create(prms_loc,*args)

        method_name =  "prepare_" + name
        if method_name not in inst.__class__.__dict__:
            raise Exception(method_name 
                + " not found in class " + inst.__class__.__name__)
        inst.prepare=getattr(inst,method_name,None)
        return inst



from . import *


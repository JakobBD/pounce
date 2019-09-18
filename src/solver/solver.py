import sys,os
import inspect
import copy

from helpers.baseclass import BaseClass
from helpers.printtools import *

class Batch(BaseClass):

    defaults_ = {
        'cores_per_sample' : 1,
        'avg_walltime' : 300.,
        "exe_path": "NODEFAULT"
        }

    def check_finished(self):
        return True

    def prepare(self,simulation):
        raise Exception("not yet implemented")


class Solver(Batch):

    defaults_ = {
        'cores_per_sample' : "NODEFAULT",
        'avg_walltime' : "NODEFAULT",
        "solver_prms" :  "NODEFAULT"
        }

    def __init__(self,*args):
        super().__init__(*args)
        self.multi_sample=True


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
            print(inst.__dict__)
            raise Exception(method_name 
                + " not found in class " + inst.__class__.__name__)
        inst.prepare=getattr(inst,method_name,None)
        return inst



from . import *


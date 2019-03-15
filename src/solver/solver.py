import sys,os
import inspect

from helpers.baseclass import BaseClass
from helpers.printtools import *

class Solver(BaseClass):
    subclasses = {}
    class_defaults = {
        "exe_path": "NODEFAULT"
        }

    def check_all_finished(self,batches):
        finished = [self.check_finished(batch) for batch in batches]
        if all(finished): 
                p_print("All jobs finished.")
        else:
            tmp=[batch.name for batch,is_finished in zip(batches,finished) \
                 if not is_finished]
            raise Exception("not all jobs finished. "
                            +"Problems with batch(es) "+", ".join(tmp)+".")



class QoI(BaseClass):

    subclasses = {}
    class_defaults={
        "exe_paths": {"iteration_postproc": ""}
        }

    # we have to overwrite the register_subclass method to create a 
    # nested dictionary. outer level is solver, inner level is QoI. 
    # This allows for QoIs with the same name in different solvers.
    @classmethod
    def register_subclass(cls, solver, subclass_key):
        """
        this is called before defining a cubclass of a parent class.
        It adds each subclass to a dict, so that the subclass can be 
        chosen via a user input string.
        """
        def decorator(subclass):
            if solver not in cls.subclasses: 
                cls.subclasses[solver]={}
            cls.subclasses[solver][subclass_key] = subclass
            return subclass
        return decorator


from . import *


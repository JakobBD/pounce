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

    def prepare_postproc(self,qois,simulation):
        """ Prepares the postprocessing by generating the
        run_postproc_command.
        """
        for qoi in qois:
            p_print("Generate postproc command for "
                    +qoi.name+" "+qoi._type)
            names=[p.name for p in qoi.participants]
            p_print("  Participants: "+", ".join(names))
            qoi.prepare(simulation)





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

    def prepare_iter_postproc(self,simulation):
        raise Exception("not yet implemented")

    def prepare_simu_postproc(self,simulation):
        raise Exception("not yet implemented")


from . import *


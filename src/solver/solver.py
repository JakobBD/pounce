import sys,os

from helpers.baseclass import BaseClass
from helpers.printtools import *

class Solver(BaseClass):
    subclasses = {}
    class_defaults = {
        "project_name":"NODEFAULT",
        "exe_paths": {"main_solver": "","iteration_postproc": "", "simulation_postproc": ""}
        }

    def check_all_finished(self,batches):
        finished = [self.check_finished(batch) for batch in batches]
        if all(finished): 
                p_print("All jobs finished.")
        else:
            tmp=[batch.name for batch,is_finished in zip(batches,finished) if not is_finished]
            raise Exception("not all jobs finished. Problems with batch(es) "+", ".join(tmp)+".")

from . import *


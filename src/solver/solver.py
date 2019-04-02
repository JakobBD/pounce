import sys,os
import inspect

from helpers.baseclass import BaseClass
from helpers.printtools import *

class Solver(BaseClass):
    defaults_ = {
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

    defaults_={
        "exe_paths": {"iteration_postproc": ""}
        }


    def prepare_iter_postproc(self,simulation):
        raise Exception("not yet implemented")

    def prepare_simu_postproc(self,simulation):
        raise Exception("not yet implemented")


from . import *


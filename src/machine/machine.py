from helpers.printtools import *
from helpers.baseclass import BaseClass
from simulation.simulation import Stage

class Machine(BaseClass,Stage):

    def check_all_finished(self):
        finished = [batch.check_finished() for batch in self.batches]
        if all(finished): 
                p_print("All jobs finished.")
        else:
            tmp=[batch.name for batch,is_finished in zip(batches,finished) \
                 if not is_finished]
            raise Exception("not all jobs finished. "
                            +"Problems with batch(es) "+", ".join(tmp)+".")


from . import *

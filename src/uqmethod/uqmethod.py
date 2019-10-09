from helpers.baseclass import BaseClass
from simulation.simulation import Simulation
from helpers.printtools import *
from helpers.tools import *
from solver.solver import Solver


class UqMethod(Simulation,BaseClass):

    def get_samples(self,batches):
        p_print("Number of current samples for this iteration:")
        for batch in self.stages[0].active_batches:
            batch.samples.get()
            p_print("  Level %2s: %6d samples"%(batch.name,batch.samples.n))

    @classmethod
    def default_yml(cls,d):
        d.get_machine()
        solver = d.process_subclass(Solver)
        d.all_defaults["qois"] = d.get_list_defaults(solver.QoI)


# import subclasses
from . import *

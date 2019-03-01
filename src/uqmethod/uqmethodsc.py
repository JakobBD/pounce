import chaospy as cp
import numpy as np

from .uqmethod import UqMethod
from helpers.printtools import *
from helpers.tools import *

@UqMethod.register_subclass('sc')
class Sc(UqMethod):

   subclass_defaults={
      "sparse_grid" : "NODEFAULT"
      }

   level_defaults={
      "poly_deg": "NODEFAULT",
      'solver_prms' : {}
      }

   def __init__(self,input_prm_dict):
      super().__init__(input_prm_dict)
      self.has_simulation_postproc=False
      self.n_max_iter=1

   def setup_batches(self):
      for i_level,level in enumerate(self.levels):
         level.name=str(i_level+1)
         level.samples=Empty()
         level.postproc=Empty()
         level.postproc.participants=[level]
         level.postproc.name="postproc_"+level.name
         try:
            level.postproc.avg_walltime=level.avg_walltime_postproc
         except:
            AttributeError
         level.samples.n_previous = 0
      self.solver_batches=self.levels
      self.postproc_batches=[l.postproc for l in self.levels]

   def get_nodes_and_weights(self):
      distributions=[var.distribution for var in self.stoch_vars]
      for level in self.levels:
         nodes,level.samples.weights = cp.generate_quadrature(level.poly_deg,
                                                              cp.J(*distributions),
                                                              rule='G',
                                                              sparse=self.sparse_grid)
         level.samples.nodes=np.transpose(nodes)
         level.samples.n = len(level.samples.nodes)
      p_print("Number of current samples for this iteration:")
      [p_print("  Level %2s: %6d samples"%(level.name,level.samples.n)) for level in self.levels]

   def get_new_n_samples(self,solver):
      raise Exception("the GetNewNSamples routine should not be called for stochastic collocation")


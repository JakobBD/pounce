import chaospy as cp
import numpy as np

from .uqmethod import UqMethod
from helpers.printtools import *
from helpers.tools import *

@UqMethod.RegisterSubclass('sc')
class Sc(UqMethod):

   subclassDefaults={
      "sparseGrid" : "NODEFAULT"
      }

   levelDefaults={
      "polyDeg": "NODEFAULT",
      'solverPrms' : {}
      }

   def __init__(self,inputPrmDict):
      super().__init__(inputPrmDict)
      self.nMaxIter=1

   def SetupBatches(self):
      for iLevel,level in enumerate(self.levels):
         level.name=str(iLevel+1)
         level.samples=Empty()
         level.postproc=Empty()
         level.postproc.participants=[level]
         level.postproc.name="postproc_"+level.name
         level.samples.nPrevious = 0
      self.solverBatches=self.levels
      self.postprocBatches=[l.postproc for l in self.levels]
       
   def GetNodesAndWeights(self):
      distributions=[var.distribution for var in self.stochVars]
      for level in self.levels:
         nodes,level.samples.weights = cp.generate_quadrature(level.polyDeg,
                                                              cp.J(*distributions),
                                                              rule='G',
                                                              sparse=self.sparseGrid)
         level.samples.nodes=np.transpose(nodes)
         level.samples.n = len(level.samples.nodes)
      Print("Number of current samples for this iteration:")
      [Print("  Level %2s: %6d samples"%(level.name,level.samples.n)) for level in self.levels]

   def GetNewNSamples(self):
      raise Exception("the GetNewNSamples routine should not be called for stochastic collocation")


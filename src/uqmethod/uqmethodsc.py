import chaospy as cp

from .uqmethod import UqMethod

@UqMethod.RegisterSubclass('sc')
class Sc(UqMethod):
   subclassDefaults={
      "sparseGrid" : "NODEFAULT"
      }

   levelDefaults={
      "polyDeg": "NODEFAULT",
      'solverPrms' : {}
      }

   def OwnConfig(self):
      for iLevel,level in enumerate(self.levels):
         level.ind=iLevel+1
      self.nMaxIter=1
   # def InitLoc(self):



   def GetNodesAndWeights(self):
      for level in self.levels:
         level.distributions=[]
         for var in self.stochVars:
            level.distributions.append(var.GetDistribution())
         level.samples, level.weights= cp.generate_quadrature(level.polyDeg,cp.J(*level.distributions),\
         rule='G',sparse=self.sparseGrid)

   def PrepareSimulation(self):
      for level in self.levels:
         furtherAttrs=level.solverPrms
         furtherAttrs.update({"Level":level.ind})
         fileNameSubStr=str(level.ind)
         self.solver.PrepareSimulation(level,self.stochVars,fileNameSubStr,furtherAttrs)

class SubLevel():
   def __init__(self,level):
      self.solverPrms=level.solverPrms
      self.nCoresPerSample=level.nCoresPerSample

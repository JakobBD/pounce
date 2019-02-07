import chaospy as cp

from .uqmethod import UqMethod

@UqMethod.RegisterSubclass('sc')
class Sc(UqMethod):
   stochVarDefaults={
      'polyDeg': 'NODEFAULT'
      }
   subclassDefaults={
      "sparseGrid" : "NODEFAULT"
      }

   def InitLoc(self):
      self.nMaxIter=1


   def GetNodesAndWeights(self):
      for level in self.levels:
         level.distributions=[]
         for var in self.stochVars:
            level.distributions.append(var.GetDistribution())
         level.samples, level.weights= cp.generate_quadrature(level.polyDeg+1,cp.J(*level.distributions),\
         rule='G',sparse=self.sparseGrid)

   def PrepareSimulation(self):
      for level in self.levels:
         for subName,sublevel in level.sublevels.items():
             furtherAttrs=sublevel.solverPrms
             furtherAttrs.update({"Level":level.ind})
             fileNameSubStr=str(level.ind)+str(subName)
             self.solver.PrepareSimulation(level,self.stochVars,fileNameSubStr,furtherAttrs)

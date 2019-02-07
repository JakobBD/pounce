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

   def SetupLevels(self):
      for iLevel,level in enumerate(self.levels):
         level.ind=iLevel+1

   def InitLoc(self):
      self.nMaxIter=1

   def GetNodesAndWeights(self):
      for level in self.levels:
         level.distributions=[]
         for var in self.stochVars:
            level.distributions.append(var.GetDistribution())
         level.samples, level.weights= cp.generate_quadrature(level.polyDeg,cp.J(*level.distributions),\
         rule='G',sparse=self.sparseGrid)

   def PrepareAllSimulations(self):
      for level in self.levels:
         furtherAttrs=level.solverPrms
         furtherAttrs.update({"Level":level.ind})
         fileNameSubStr=str(level.ind)
         level.runCommand=self.solver.PrepareSimulation(level,self.stochVars,fileNameSubStr,furtherAttrs)

   def RunAllBatches(self):
      for level in self.levels:
         self.machine.RunBatch(level.runCommand,level.nCoresPerSample,self.solver)

   def GetNewNSamples(self):
      raise Exception("the GetNewNSamples routine should not be called for stochastic collocation")

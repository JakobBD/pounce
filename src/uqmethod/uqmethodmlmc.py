import numpy as np
import os

from .uqmethod import UqMethod

@UqMethod.RegisterSubclass('mlmc')
class Mlmc(UqMethod):
   subclassDefaults={
      "nMaxIter" : "NODEFAULT"
      }

   levelDefaults={
      "nSamples": "NODEFAULT",
      'solverPrms' : {}
      }

   def OwnConfig(self):
      for iLevel,level in enumerate(self.levels):
         level.ind=iLevel+1
         level.sublevels = {'f' : SubLevel(level) }
         if iLevel > 0: 
            level.sublevels['c']=SubLevel(self.levels[iLevel-1])
      

   def GetNodesAndWeights(self):
      for level in self.levels:
         level.samples=[]
         for var in self.stochVars:
            level.samples.append(var.DrawSamples(level.nSamples))
         level.samples=np.transpose(level.samples)
         level.weights=np.ones(level.nSamples)/level.nSamples

   def PrepareAllSimulations(self):
      for level in self.levels:
         for subName,sublevel in level.sublevels.items():
             furtherAttrs=sublevel.solverPrms
             furtherAttrs.update({"Level":level.ind})
             furtherAttrs.update({"Sublevel":subName})
             fileNameSubStr=str(level.ind)+str(subName)
             sublevel.runCommand=self.solver.PrepareSimulation(level,self.stochVars,fileNameSubStr,furtherAttrs)

   def RunAllBatches(self):
      for level in self.levels:
         for subName,sublevel in level.sublevels.items():
             self.machine.RunBatch(sublevel.runCommand,sublevel.nCoresPerSample,self.solver)

class SubLevel():
   def __init__(self,level):
      self.solverPrms=level.solverPrms
      self.nCoresPerSample=level.nCoresPerSample

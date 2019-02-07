import numpy as np
import os

from .uqmethod import UqMethod

@UqMethod.RegisterSubclass('mlmc')
class Mlmc(UqMethod):
   subclassDefaults={
      "nMaxIter" : "NODEFAULT",
      "tolerance" : "NODEFAULT"
      }

   levelDefaults={
      "nCurrentSamples": "NODEFAULT",
      'solverPrms' : {}
      }

   def SetupLevels(self):
      for iLevel,level in enumerate(self.levels):
         level.nTotalSamples = 0
         level.ind=iLevel+1
         level.sublevels = {'f' : SubLevel(level) }
         if iLevel > 0:
            level.sublevels['c']=SubLevel(self.levels[iLevel-1])


   def GetNodesAndWeights(self):
      for level in self.levels:
         level.samples=[]
         for var in self.stochVars:
            level.samples.append(var.DrawSamples(max(level.nCurrentSamples-level.nTotalSamples,0)))
         level.samples=np.transpose(level.samples)
         level.weights=np.ones(level.nCurrentSamples)/level.nCurrentSamples

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
         level.nTotalSamples += max(level.nCurrentSamples-level.nTotalSamples,level.nTotalSamples)
         print(level.nTotalSamples)

   def PrepareAllPostprocessing(self):
      for level in self.levels:
         fileNameSubStr = []
         for subName,sublevel in level.sublevels.items():
            fileNameSubStr.append("{}{}".format(level.ind,subName))
         level.runPostprocCommand=self.solver.PreparePostprocessing(fileNameSubStr)

   def RunAllBatchesPostprocessing(self):
      for level in self.levels:
         self.machine.RunBatch(level.runPostprocCommand,1,self.solver)

   def GetNewNCurrentSamples(self):
      for level in self.levels:
         fileNameSubStr = str(level.ind)
         level.sigmaSq = self.solver.GetSigmaSq(fileNameSubStr)
         level.workMean = 10.*level.ind
         level.nCurrentSamples = int(np.ceil(np.dot(np.sqrt(level.sigmaSq),np.sqrt(level.workMean))\
                          /(self.tolerance**2/4.)\
                          *np.sqrt(level.sigmaSq/(level.workMean)) ))
         print(level.nCurrentSamples)


class SubLevel():
   def __init__(self,level):
      self.solverPrms=level.solverPrms
      self.nCoresPerSample=level.nCoresPerSample

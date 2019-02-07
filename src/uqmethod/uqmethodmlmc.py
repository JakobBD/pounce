import numpy as np
import os

from .uqmethod import UqMethod
from helpers.printtools import *

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
         level.nFinshedSamples = 0
         level.ind=iLevel+1
         level.sublevels = {'f' : SubLevel(level) }
         if iLevel > 0:
            level.sublevels['c']=SubLevel(self.levels[iLevel-1])

   def GetNodesAndWeights(self):
      for level in self.levels:
         level.samples=[]
         for var in self.stochVars:
            level.samples.append(var.DrawSamples(level.nCurrentSamples))
         level.samples=np.transpose(level.samples)
         level.weights=[]

   def PrepareAllSimulations(self):
      for level in self.levels:
         for subName,sublevel in level.sublevels.items():
             furtherAttrs=sublevel.solverPrms
             furtherAttrs.update({"Level":level.ind})
             furtherAttrs.update({"Sublevel":subName})
             fileNameSubStr=str(level.ind)+str(subName)
             sublevel.runCommand=self.solver.PrepareSimulation(level,self.stochVars,fileNameSubStr,furtherAttrs)
         del level.samples

   def RunAllBatches(self):
      for level in self.levels:
         for subName,sublevel in level.sublevels.items():
            self.machine.RunBatch(sublevel.runCommand,sublevel.nCoresPerSample,self.solver)
         level.nFinshedSamples += level.nCurrentSamples
         print(level.nFinshedSamples)

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
      sumSigmaW = 0.
      headerStr   = "                | "
      sigmaSqStr  = "        SigmaSq | "
      meanWorkStr = "      mean work | "
      mloptStr    = "         ML_opt | "
      fininshedStr= "finshed Samples | "
      newStr      = "    new Samples | "
      for level in self.levels:
         fileNameSubStr = str(level.ind)
         level.sigmaSq = self.solver.GetSigmaSq(fileNameSubStr)
         level.workMean = 10.*level.ind #TODO
         sigmaSqW=level.sigmaSq*level.workMean
         sumSigmaW += np.sqrt(sigmaSqW) if sigmaSqW > 0. else 0.
         headerStr+="     Level %2d | "%(level.ind)
         sigmaSqStr+="%13.4e | "%(level.sigmaSq)
         meanWorkStr+="%13.4e | "%(level.workMean)
      for level in self.levels:
         sqrtTmp= np.sqrt(level.sigmaSq/level.workMean) if level.sigmaSq/level.workMean > 0. else 0.
         mlopt=sumSigmaW*sqrtTmp/(self.tolerance*self.tolerance/4.)
         level.nCurrentSamples = max(int(np.ceil(mlopt))-level.nFinshedSamples , 0)
         mloptStr+="%13.3f | "%(mlopt)
         fininshedStr+="%13d | "%(level.nFinshedSamples)
         newStr+="%13d | "%(level.nCurrentSamples)
      Print(headerStr)
      Print("-"*len(headerStr))
      Print(sigmaSqStr)
      Print(meanWorkStr)
      Print(mloptStr)
      Print(fininshedStr)
      Print(newStr)


class SubLevel():
   def __init__(self,level):
      self.solverPrms=level.solverPrms
      self.nCoresPerSample=level.nCoresPerSample

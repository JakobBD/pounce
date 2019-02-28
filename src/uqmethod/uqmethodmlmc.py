import numpy as np
import os
import copy

from .uqmethod import UqMethod
from helpers.printtools import *
from helpers.tools import *


@UqMethod.RegisterSubclass('mlmc')
class Mlmc(UqMethod):

   subclassDefaults={
      "nMaxIter" : "NODEFAULT",
      "tolerance" : "NODEFAULT",
      "resetSeed" : False
      }

   levelDefaults={
      "nWarmupSamples": "NODEFAULT",
      "solverPrms" : {},
      }

   def __init__(self,inputPrmDict):
      super().__init__(inputPrmDict)
      self.hasSimulationPostproc=True
      if self.resetSeed:
         Print("Reset RNG seed to 0")
         np.random.seed(0)

   def SetupBatches(self):
      self.allSublevels=[]
      for iLevel,level in enumerate(self.levels):
         level.name=str(iLevel+1)
         level.samples=Empty()
         level.samples.n=level.nWarmupSamples
         level.samples.nPrevious = 0
         level.sublevels= [ SubLevel(level,level,'f') ]
         self.allSublevels.append(level.sublevels[-1])
         if iLevel > 0:
            level.sublevels.append(SubLevel(level,self.levels[iLevel-1],'c'))
            self.allSublevels.append(level.sublevels[-1])
         level.postproc=Empty()
         level.postproc.participants=level.sublevels
         level.postproc.name="postproc_"+level.name
         level.postproc.avgWalltime=getattr(level,"avgWalltimePostproc",None)
      self.getActiveBatches()
      self.simuPostproc=Empty()
      self.simuPostproc.name="combinelevels"
      self.simuPostproc.participants=self.levels

   def getActiveBatches(self):
      self.activeSublevels=[sub for sub in self.allSublevels if sub.samples.n > 0]
      self.activeLevels=[l for l in self.levels if l.samples.n > 0]
      # external naming
      self.solverBatches = self.activeSublevels
      self.postprocBatches=[l.postproc for l in self.activeLevels]

      self.doContinue = len(self.activeLevels) > 0

   def GetNodesAndWeights(self):
      for level in self.activeLevels:
         level.samples.nodes=[]
         for var in self.stochVars:
            level.samples.nodes.append(var.DrawSamples(level.samples.n))
         level.samples.nodes=np.transpose(level.samples.nodes)
         level.samples.weights=[]
      Print("Number of current samples for this iteration:")
      [Print("  Level %2s: %6d samples"%(level.name,level.samples.n)) for level in self.levels]


   def GetNewNCurrentSamples(self,solver):

      stdoutTable=StdOutTable( "sigmaSq","workMean" ,"mlopt" ,"samples__nPrevious","samples__n")
      stdoutTable.Descriptions("SigmaSq","mean work","ML_opt","finished Samples"  ,"new Samples")

      # build sum over levels of sqrt(sigma^2/w)
      sumSigmaW = 0.
      for level in self.levels:
         if level.samples.n > 0:
            level.sigmaSq = solver.GetPostprocQuantityFromFile(level.postproc,"SigmaSq")
            workMean = solver.GetWorkMean(level.postproc)
            if level.samples.nPrevious > 0:
               level.workMean = (level.samples.nPrevious*level.workMean + level.samples.n*workMean)/\
                                (level.samples.n+level.samples.nPrevious)
            else:
               level.workMean = workMean
         if level.samples.nPrevious+level.samples.n > 0:
            sumSigmaW += SafeSqrt(level.sigmaSq*level.workMean)

      for level in self.levels:
         #TODO: add formula for given maxWork
         level.mlopt = sumSigmaW * SafeSqrt(level.sigmaSq/level.workMean) / (self.tolerance*self.tolerance/4.)
         level.samples.nPrevious += level.samples.n
         level.samples.n = max(int(np.ceil(level.mlopt))-level.samples.nPrevious , 0)
         stdoutTable.Update(level)

      stdoutTable.Print("Level")

      self.getActiveBatches()


class SubLevel():
   def __init__(self,diffLevel,resolutionLevel,name):
      self.solverPrms = resolutionLevel.solverPrms
      self.nCoresPerSample = resolutionLevel.nCoresPerSample
      #todo: nicer
      try:
         self.avgWalltime = resolutionLevel.avgWalltime
      except AttributeError:
         pass
      self.samples=diffLevel.samples
      self.name=diffLevel.name+name



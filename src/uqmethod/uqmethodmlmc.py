import numpy as np
import os

from .uqmethod import UqMethod
from helpers.printtools import *
from helpers.tools import *

@UqMethod.RegisterSubclass('mlmc')
class Mlmc(UqMethod):
   subclassDefaults={
      "nMaxIter" : "NODEFAULT",
      "tolerance" : "NODEFAULT"
      }

   levelDefaults={
      "nCurrentSamples": "NODEFAULT",
      "solverPrms" : {},
      "workMean" :  {},
      "avgNodes" :  {}
      }

   def SetupLevels(self):
      self.allSublevels=[]
      for iLevel,level in enumerate(self.levels):
         level.nFinshedSamples = 0
         level.ind=iLevel+1
         level.sublevels= [ SubLevel(level,level,'f') ]
         self.allSublevels.append(level.sublevels[-1])
         if iLevel > 0:
            level.sublevels.append(SubLevel(level,self.levels[iLevel-1],'c'))
            self.allSublevels.append(level.sublevels[-1])

   def GetNodesAndWeights(self):
      for level in self.levels:
         level.samples=[]
         for var in self.stochVars:
            level.samples.append(var.DrawSamples(level.nCurrentSamples))
         level.samples=np.transpose(level.samples)
         level.weights=[]

   def PrepareAllSimulations(self):
      for sublevel in self.allSublevels:
         furtherAttrs=sublevel.solverPrms
         furtherAttrs.update({"Level":sublevel.level.ind})
         furtherAttrs.update({"Sublevel":sublevel.subName})
         sublevel.runCommand=self.solver.PrepareSimulation(sublevel.level,self.stochVars,sublevel.wholeName,furtherAttrs)
      for level in self.levels:
         del level.samples

   def RunAllBatches(self):
      jobHandles=[]
      for sublevel in self.allSublevels:
         fileNameStr = str(sublevel.level.ind) + sublevel.subName
         jobHandle = self.machine.RunBatch(sublevel.runCommand,sublevel.nCoresPerSample,\
                     sublevel.level.nCurrentSamples,sublevel.avgNodes,self.solver,fileNameStr)
         jobHandles.append(jobHandle)
      PrintMinorSection("Waiting for jobs to finish:")
      if self.machine.WaitFinished(jobHandles): Print("Computations finished.")
      if self.machine.CheckAllFinished(): Print("All jobs finished.")
      for level in self.levels:
         level.nFinshedSamples += level.nCurrentSamples


   def PrepareAllPostprocessing(self):
      for level in self.levels:
         fileNameSubStr = [sublevel.wholeName for sublevel in level.sublevels]
         level.runPostprocCommand=self.solver.PreparePostprocessing(fileNameSubStr)

   def RunAllBatchesPostprocessing(self):
      for level in self.levels:
         self.machine.RunBatch(level.runPostprocCommand,1,self.solver)

   def GetNewNCurrentSamples(self):

      stdoutTable=StdOutTable()

      # build sum over levels of sqrt(sigma^2/w)
      sumSigmaW = 0.
      for level in self.levels:
         fileNameSubStr = str(level.ind)
         level.sigmaSq = self.solver.GetPostProcQuantityFromFile(fileNameSubStr,"sigmaSq")
         level.workMean = self.solver.GetPostProcQuantityFromFile(fileNameSubStr,"WorkMean")
         sumSigmaW += SafeSqrt(level.sigmaSq*level.workMean)
         stdoutTable.Update1(level)

      for level in self.levels:
         #TODO: add formula for given maxWork
         level.mlopt = sumSigmaW * SafeSqrt(level.sigmaSq/level.workMean) / (self.tolerance*self.tolerance/4.)
         level.nCurrentSamples = max(int(np.ceil(level.mlopt))-level.nFinshedSamples , 0)
         stdoutTable.Update2(level)

      stdoutTable.Print()


class SubLevel():
   def __init__(self,diffLevel,resolutionLevel,name):
      self.solverPrms=resolutionLevel.solverPrms
      self.nCoresPerSample=resolutionLevel.nCoresPerSample
      self.level = diffLevel
      self.subName=name
      self.wholeName=str(diffLevel.ind)+name
      self.avgNodes=resolutionLevel.avgNodes
      self.workMean=resolutionLevel.workMean



class StdOutTable():
   """
   Helper class for GetNewNCurrentSamples routine.
   Outsourced for improved readability.
   Prints values for each level in ordered table to stdout.
   """
   def __init__(self):
      self.headerStr   = "                ║ "
      self.sigmaSqStr  = "        SigmaSq ║ "
      self.meanWorkStr = "      mean work ║ "
      self.mloptStr    = "         ML_opt ║ "
      self.fininshedStr= "finshed Samples ║ "
      self.newStr      = "    new Samples ║ "

   def Update1(self,level):
      self.headerStr  +="     Level %2d ║ "%(level.ind)
      self.sigmaSqStr +="%13.4e ║ "%(level.sigmaSq)
      self.meanWorkStr+="%13.4e ║ "%(level.workMean)

   def Update2(self,level):
      self.mloptStr    +="%13.3f ║ "%(level.mlopt)
      self.fininshedStr+="%13d ║ "%(level.nFinshedSamples)
      self.newStr      +="%13d ║ "%(level.nCurrentSamples)

   def Print(self):
      Print(self.headerStr)
      sepStr="═"*14+"╬═"
      Print("══"+sepStr*int(len(self.headerStr)/len(sepStr)))
      Print(self.sigmaSqStr)
      Print(self.meanWorkStr)
      Print(self.mloptStr)
      Print(self.fininshedStr)
      Print(self.newStr)

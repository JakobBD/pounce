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
      jobHandles=[]
      for level in self.levels:
         for subName,sublevel in level.sublevels.items():
            jobHandle = self.machine.RunBatch(sublevel.runCommand,sublevel.nCoresPerSample,self.solver)
            jobHandles.append(jobHandle)
      PrintMinorSection("Waiting for jobs to finish:")
      self.machine.WaitFinished(jobHandles)
      Print("All jobs finished.")
      for level in self.levels:
         level.nFinshedSamples += level.nCurrentSamples

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
   def __init__(self,level):
      self.solverPrms=level.solverPrms
      self.nCoresPerSample=level.nCoresPerSample



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

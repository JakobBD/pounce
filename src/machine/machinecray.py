import time
import glob
import os
import math
import numpy as np
import subprocess

from .machine import Machine
from helpers.time import *
from helpers.printtools import *
from helpers.tools import *

@Machine.RegisterSubclass('cray')
class Cray(Machine):
   """Definition of Cray Hazelhen machine.
   """
   subclassDefaults={
      "username" : "NODEFAULT",
      "walltimeFactor" : 1.2,
      "nMaxCores" : 10000,
      "maxWalltime" : 86400, # 24h
      "maxTotalWork" : 36E5  # 1.000 CoreH
      }

   levelDefaults={
      "avgWalltime" : "NODEFAULT",
      "avgWalltimePostproc" : 120.
      }

   def __init__(self,classDict):
      self.nCoresPerNode = 24
      self.totalWork = 0.
      super().__init__(classDict)


   def AllocateResourcesPostproc(self,batches):
      for batch in batches:
         batch.nCores=self.nCoresPerNode


   def RunBatches(self,batches,simulation,solver,postprocType=False):
      """Runs a job by generating the necessary jobfile
          and submitting it.
      """
      # in case of a restart, only submit
      for batch in self.Unfinished(batches):
         if not getattr(batch,"queueStatus",None):
            self.SubmitJob(batch,solver,simulation)
      self.WaitFinished(batches,simulation)

      if not postprocType:
         solver.CheckAllFinished(batches)
      # reset for next iteration
      for batch in batches:
         batch.finished=False

   def Unfinished(self,batches):
      return [batch for batch in batches if not getattr(batch,"finished",False)]


   def SubmitJob(self,batch,solver,simulation):
      """Generates the necessary jobfile and submits job.
      """
      jobfileString = (
        '#!/bin/bash\n'
      + '#PBS -N {}\n'.format(solver.projectName)
      + '#PBS -l nodes={}:ppn=24\n'.format(batch.nCores)
      + '#PBS -l walltime='+Time(batch.batchWalltime).str+"\n\n"
      + 'cd $PBS_O_WORKDIR\n\n'
      + 'aprun -n  {}  -N 24 {}  &> calc_{}.log\n'.format(batch.nCores,batch.runCommand,batch.name)
      )
      batch.jobfileName = 'jobfile_{}'.format(batch.name)
      with open(batch.jobfileName,'w+') as jf:
         jf.write(jobfileString)
      # submit job
      job = subprocess.run(['qsub',jobfile],stdout=subprocess.PIPE,universal_newlines=True)
      batch.jobID=int(job.stdout.read().split(".")[0])
      batch.queueStatus="submitted"
      simulation.iterations[-1].UpdateStep(simulation)


   def WaitFinished(self,batches,simulation):
      """Monitors all jobs on Cray Hazelhen HPC queue. Checks if jobfile finished.
      """
      while True:
         statuses=self.ReadQstat()
         for batch in self.Unfinished(batches):
            if batch.jobID in statuses:
               queueStatus = statuses[batch.jobID]
            else:
               queueStatus = "C"
            if not queueStatus == batch.queueStatus:
               Print("Job {} with ID {} has status {}.".format(batch.name,batch.jobID,queueStatus))
               batch.queueStatus=queueStatus
            if queueStatus=='C':
               self.CheckErrorfile(batch,batches,simulation)
         if not self.Unfinished(batches):
            return
         time.sleep(1)


   def ReadQstat(self):
      """run 'qstat' on cray and read output
      """
      job = subprocess.Popen(['qstat','-u',self.username],stdout=subprocess.PIPE,universal_newlines=True)
      lines = str(job.stdout.read()).split('\n')
      if len(lines)<4:
         return {}
      else:
         return {int(line.split(".")[0]): line.split()[9] for line in lines[5:-1]}


   def CheckErrorfile(self,batch,batches,simulation):
      """open error file and parse errrors. Well, parse is a strong word here.
      """
      with open(glob.glob('*.e{}'.format(batch.jobID))[0]) as f:
         lines = f.read().splitlines()
      # empty error file: all good
      if len(lines)==0:
         batch.finished=True
         batch.queueStatus=None
         Print('job ID {} is now complete! {} jobs remaining'.format(batch.jobID,len(self.Unfinished(batches))))
         return
      # check if walltime excced in error file (also means that solver did not otherwise crash)
      longlines=[line.split() for line in lines if len(line.split())>=7]
      for words in longlines:
         if words[4]=='walltime' and words[6]=='exceeded':
            Print("Job {} exceeded walltime ({}). Re-submit with double walltime.".format(batch.name,Time(batch.walltime).str))
            batch.walltime *= 2
            self.SubmitJob(batch,solver,simulation)
            return
      # non-empty error file and not walltime excceded: other error
      raise Exception('Error in jobfile execution! See file *.e{} for details.\n'.format(batch.jobID))


   def AllocateResources(self,batches):
      """Takes the properties of the batch (number of current samples, walltime and cores of current sample)
      as well as the machine properties or machine input (number of cores per node, max nodes etc.)
      and outputs number of cores and number of parallel runs for this batch.
      """

      self.walltimeFactor = 1.2
      stdoutTable=StdOutTable( "queue","rating","nParallelRuns","nSequentialRuns","nCores","nNodes","batchWalltime")
      stdoutTable.Descriptions("Queue","Rating","nParallelRuns","nSequentialRuns","nCores","nNodes","batchWalltime")

      for batch in batches:
         batch.scaledAvgWalltime=self.walltimeFactor*batch.avgWalltime
         batch.work=batch.scaledAvgWalltime*batch.nCoresPerSample*batch.samples.n

         # make sure to fill a node
         self.GetPackageProperties(batch)

         # decide which queue to use 
         GetQueue(batch)

         # get nParallelRuns and nSequentialRuns (core of this routine)
         self.GetBestOption(batch)

         # some serived quantities
         batch.nCores = batch.nParallelRuns * batch.nCoresPerSample
         batch.batchWalltime = batch.nSequentialRuns * batch.scaledAvgWalltime
         batch.nNodes = batch.nCores / self.nCoresPerNode

         self.totalWork += batch.nCores * batch.batchWalltime
         if self.totalWork > self.maxTotalWork:
            raise Exception("Max total core hours exceeded!")

         stdoutTable.Update(batch)
      stdoutTable.Print("Batch")


   def GetPackageProperties(self,batch):
      """define a "package" of runs to fill a node, e.g. 4 parallel runs with nCoresPerSample=6.
      trivial if nCoresPerSample >= 24.
      """
      batch.nParallelRunsPackage = max( 1, self.nCoresPerNode // batch.nCoresPerSample)
      batch.nCoresPackage = batch.nCoresPerSample*batch.nParallelRunsPackage
      if batch.nCoresPackage%self.nCoresPerNode:
         raise Exception("nCoresPerSample has to be multiple of nCoresPerNode or vice versa")
      if batch.nCoresPackage > self.nMaxCores:
         raise Exception("nMaxCores (%i) too small for smallest batch nCores (%i)"%(self.nMaxCores,nCores))


   def GetBestOption(self,batch):
      """Loop over all possible combinations of nParallelRuns and nSequentialRuns.
      Get Rating for all of them. Pick the best one.
      """
      batch.maxRating = -1.
      nMax=int(math.ceil(np.sqrt(batch.samples.n/batch.nParallelRunsPackage)))

      for i in range(1,nMax+1):
         opt1 = Option( batch,nParallelRuns=i*batch.nParallelRunsPackage)
         opt2 = Option( batch,nSequentialRuns=i)

         for opt in [opt1,opt2]:
            if opt.valid and (opt.rating > batch.maxRating):
               batch.maxRating = opt.rating
               batch.nParallelRuns = opt.nParallelRuns
               batch.nSequentialRuns = opt.nSequentialRuns

      if batch.maxRating <= 0.:
         raise Exception("Something went wrong in AllocateResources. No valid option found")


class Option():
   """One combination of nParallelRuns and nSequentialRuns. 
   Has a Rating based on efficiency (few idling cores) and expcted queuing time.
   Invalid if does not match criteria of selected queue.
   """

   def __init__(self,batch,nSequentialRuns=None,nParallelRuns=None):
      if nSequentialRuns:
         self.nSequentialRuns = nSequentialRuns
         self.nParallelRuns = ( batch.nParallelRunsPackage *
                                int(math.ceil(batch.samples.n / (self.nSequentialRuns*batch.nParallelRunsPackage))) )
      elif nParallelRuns:
         self.nParallelRuns = nParallelRuns
         self.nSequentialRuns = int(math.ceil( batch.samples.n / self.nParallelRuns ))
      self.walltime = self.nSequentialRuns*batch.scaledAvgWalltime
      self.nCores= self.nParallelRuns*batch.nCoresPerSample

      self.Rating(batch)
      self.CheckValid(batch)

   def Rating(self,batch):
      """Rating based on efficiency (few idling cores) and expcted queuing time.
      """
      self.queueRating = min( batch.idealCores / self.nCores , batch.idealWt / self.walltime )
      self.effiencyRating = batch.samples.n / (self.nParallelRuns * self.nSequentialRuns)
      self.rating = self.effiencyRating ** 3. * self.queueRating

   def CheckValid(self,batch):
      """Invalid if does not match criteria of selected queue.
      """
      self.valid = ( ( batch.boundsParallel[0]   <= self.nParallelRuns   <= batch.boundsParallel[1]   ) and
                     ( batch.boundsSequential[0] <= self.nSequentialRuns <= batch.boundsSequential[1] ) )


def GetQueue(batch):
   """check which queue the job is eligible for: 
   if possible, run on multi. If too small, run on small. If too large, run on long (>4h)
   """
   # in order for the multi queue to be used, nParallelRunsMultiMin
   batch.nSequentialRunsMultiMin = int(math.ceil( 5*60 / batch.scaledAvgWalltime  ))
   batch.nParallelRunsMultiMin = batch.nParallelRunsPackage * int(math.ceil( 48*24 / batch.nCoresPackage ))

   batch.nSequentialRuns4hMax = batch.scaledAvgWalltime* ( 4*3600 // batch.scaledAvgWalltime )
   efficiencyVsQueueFactor = 0.9
   nSamplesMulti = (
   efficiencyVsQueueFactor     *max( batch.nParallelRunsMultiMin   *(batch.nSequentialRunsMultiMin-1),
                                    (batch.nParallelRunsMultiMin-1)* batch.nSequentialRunsMultiMin    ) +
   (1.-efficiencyVsQueueFactor)*min( batch.nParallelRunsMultiMin   *(batch.nSequentialRunsMultiMin-1),
                                    (batch.nParallelRunsMultiMin-1)* batch.nSequentialRunsMultiMin    ) )

   if nSamplesMulti >= batch.samples.n:
      SmallQueue(batch)
   elif batch.nSequentialRuns4hMax*batch.nParallelRunsMax < batch.samples.n:
      LongQueue(batch)
   else:
      MultiQueue(batch)

   #fill ideal values according to queue
   batch.workFunc = [a*b for a,b in zip(batch.wtFunc,batch.coresFunc)]
   batch.expWt = np.log(batch.wtFunc[1]/batch.wtFunc[0]) / np.log(batch.workFunc[1]/batch.workFunc[0])
   batch.expCores = 1 - batch.expWt
   batch.idealWt = batch.wtFunc[0] * (batch.work / batch.workFunc[0])**batch.expWt
   batch.idealCores = batch.coresFunc[0] * (batch.work / batch.workFunc[0])**batch.expCores


def SmallQueue(batch):
   """multi queue cannot be filled with walltime > 5 min
   """
   batch.queue = "small"
   batch.wtFunc = [5.*60, 24.*60 ]
   batch.coresFunc = [1*24, 10*24]
   batch.boundsParallel = [batch.nParallelRunsPackage, batch.nParallelRunsMax]
   batch.boundsSequential = [1, batch.nSequentialRunsMax]

def MultiQueue(batch):
   """preferred queue: nNodes>=48, walltime < 4h
   """
   batch.queue = "multi"
   batch.wtFunc = [30.*60, 4.*3600 ]
   batch.coresFunc = [48*24, 192*24]
   batch.boundsParallel = [batch.nParallelRunsMultiMin, batch.nParallelRunsMax]
   batch.boundsSequential = [batch.nSequentialRunsMultiMin, batch.nSequentialRuns4hMax]

def LongQueue(batch):
   """with maxCores, walltime exceeds 4h
   """
   batch.queue = "long"
   batch.wtFunc = [4.*3600, 8.*3600 ]
   batch.coresFunc = [500*24, 500*24]
   batch.boundsParallel = [batch.nParallelRunsMultiMin, batch.nParallelRunsMax]
   batch.boundsSequential = [1, batch.nSequentialRunsMax]


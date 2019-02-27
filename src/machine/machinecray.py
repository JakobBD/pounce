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
      }

   def __init__(self,classDict):
      self.nCoresPerNode = 24
      self.totalWork = 0.
      super().__init__(classDict)


   def AllocateResourcesPostproc(self,batches):
      for batch in batches: 
         batch.nCores=self.nCoresPerNode
         batch.walltime=120.


   def RunBatches(self,batches,solver,postProc=False):
      """Runs a job by generating the necessary jobfile
          and submitting it.
      """
      self.unfinished_batches=batches
      for batch in self.unfinished_batches:
         batch.jobfile=self.GenerateJobFile(batch,solver)
         batch.jobID=self.SubmitJob(batch.jobfile)
      self.waitingForJobs=True
      self.unfinished_batches=self.WaitFinished(self.unfinished_batches)
      self.waitingForJobs=False
      if not postProc:
         solver.CheckAllFinished(batches)
      #TODO: restart unfinished jobs


   def GenerateJobFile(self,batch,solver):
      """Generates the necessary jobfile.
      """
      jobfileString = (
        '#!/bin/bash\n'
      + '#PBS -N {}\n'.format(solver.projectName)
      + '#PBS -l nodes={}:ppn=24\n'.format(batch.nCores)
      + '#PBS -l walltime='+Time(batch.batchWalltime).str+"\n\n"
      + 'cd $PBS_O_WORKDIR\n\n'
      + 'aprun -n  {}  -N 24 {}  &> calc_{}.log\n'.format(batch.nCores,batch.runCommand,batch.name)
      )
      jobfileName = 'jobfile_{}'.format(batch.name)
      with open(jobfileName,'w+') as jf:
         jf.write(jobfileString)
      return jobfileName


   def SubmitJob(self,jobfile):
      """Submits a job into the Cray Hazelhen HPC queue.
      """
      job = subprocess.run(['qsub',jobfile],stdout=subprocess.PIPE,universal_newlines=True)
      return int(job.stdout.read().split(".")[0])


   def WaitFinished(self,batches):
      """Monitors all jobs on Cray Hazelhen HPC queue. Checks if jobfile finished.
      """
      jobHandles=[batch.jobID for batch in batches]
      status_list=[]
      comp_finished=None
      unfinished_jobs=None
      n_remain=len(jobHandles)
      while not comp_finished:
         job = subprocess.Popen(['qstat','-u',self.username],stdout=subprocess.PIPE\
                                                            ,universal_newlines=True)
         status_tmp = str(job.stdout.read())
         status_tmp = status_tmp.split('\n')
         if len(status_tmp)<4:
            jobs_in_queue=None
         else:
            jobs_in_queue=True
            status_tmp = status_tmp[5:]
            del status_tmp[-1]
         for index,i in enumerate(jobHandles):
            if i > 0:
               found=None
               if jobs_in_queue:
                  for line in status_tmp:
                     id = int(line.split(".")[0])
                     if i==id:
                        found=True
                        status = line.split()[9]
                        if status=='C':
                           [jobHandles,unfinished_jobs,n_remain]=self.CheckErrorfile(i,jobHandles,unfinished_jobs,index,n_remain)
                        else:
                           status_string="id {} has status {}".format(i,status)
                           if not status_string in status_list:
                              status_list.append(status_string)
                              print("Job with {}!".format(status_string))
               if not found: # jobID is not in st: pretend it is finished
                  [jobHandles,unfinished_jobs,n_remain]=self.CheckErrorfile(i,jobHandles,unfinished_jobs,index,n_remain)
         if sum(jobHandles)==0:
            comp_finished=True
         else:
            time.sleep(1)
      return([batch for batch in batches if batch.jobID in unfinished_jobs])


   def CheckErrorfile(self,i,jobID,unfinished_jobs,index,n_remain):
      with open(glob.glob('*.e{}'.format(i))[0]) as f:
         lines = f.read().splitlines()
         if len(lines)==0:
            error=None
         else:
            error=True
            for errortext in lines:
               errortext=errortext.split()
               if len(errortext)>=7:
                  if errortext[4]=='walltime' and errortext[6]=='exceeded':
                     error=None
                     unfinished_jobs=True
                     break
      if error:
         print('\nWARNING: Error in jobfile execution! See file *.e{} for details.\n'.format(i))
         unfinished_jobs=True
      jobID[index]=0
      n_remain-=1
      print('job ID {} is now complete! {} jobs remaining'.format(i,n_remain))
      return(jobID,unfinished_jobs,n_remain)


   def AllocateResources(self,batches):
      """Takes the properties of the batch (number of current samples, walltime and cores of current sample) 
      as well as the machine properties or machine input (number of cores per node, max nodes etc.) 
      and outputs number of cores and number of parallel runs for 
      """

      self.walltimeFactor = 1.2
      for batch in batches:
         batch.scaledAvgWalltime=self.walltimeFactor*batch.avgWalltime
         batch.work=batch.scaledAvgWalltime*batch.nCoresPerSample*batch.samples.n

         self.GetPackageProperties(batch)

         self.GetNRunsMax(batch)
         
         GetQueue(batch)

         self.GetBestOption(batch)

         batch.nCores = batch.nParallelRuns * batch.nCoresPerSample
         batch.batchWalltime = batch.nSequentialRuns * batch.scaledAvgWalltime
         batch.nNodes = batch.nCores / self.nCoresPerNode

         self.totalWork += batch.nCores * batch.batchWalltime
         if self.totalWork > self.maxTotalWork:
            raise Exception("Max total core hours exceeded!")

         Print("")
         Print("Queue = %s"%(batch.queue))
         Print("Rating = %s"%(batch.maxRating))
         Print("nParallelRuns = %i"%(batch.nParallelRuns))
         Print("nSequentialRuns = %i"%(batch.nSequentialRuns))
         Print("nCores = %i"%(batch.nCores))
         Print("nNodes = %i"%(batch.nNodes))
         Print("batchWalltime = %f"%(batch.batchWalltime))


   def GetPackageProperties(self,batch):
      batch.nParallelRunsPackage = max( 1, self.nCoresPerNode // batch.nCoresPerSample)
      batch.nCoresPackage = batch.nCoresPerSample*batch.nParallelRunsPackage
      if batch.nCoresPackage%self.nCoresPerNode: 
         raise Exception("nCoresPerSample has to be multiple of nCoresPerNode or vice versa")
      if batch.nCoresPackage > self.nMaxCores:
         raise Exception("nMaxCores (%i) too small for smallest batch nCores (%i)"%(self.nMaxCores,nCores))

   def GetNRunsMax(self,batch):
      batch.nSequentialRunsMax = batch.scaledAvgWalltime * ( self.maxWalltime // batch.scaledAvgWalltime )
      if batch.nSequentialRunsMax == 0: 
         raise Exception("A single job takes longer than the set walltime maximum. I cannot work like this.")

      batch.nParallelRunsMax = ( batch.nCoresPackage * (self.nMaxCores // batch.nCoresPackage) ) / batch.nCoresPerSample
      if batch.nParallelRunsMax*batch.nSequentialRunsMax < batch.samples.n: 
         PrintWarning("The limits set for #Cores and walltime are too small for this batch. nSamples is reduced.")


   def GetBestOption(self,batch):
      baseOpt = Option(batch)
      batch.nParallelRuns = baseOpt.nParallelRuns
      batch.nSequentialRuns = baseOpt.nSequentialRuns

      furtherOpts = []
      for i in range(-50,50): 
         furtherOpts.append( Option( batch,nParallelRuns=batch.nParallelRuns+i*batch.nParallelRunsPackage) )
         furtherOpts.append( Option( batch,nSequentialRuns=batch.nSequentialRuns+i) )

      if baseOpt.valid: 
         batch.maxRating = baseOpt.rating
      else:
         batch.nParallelRuns = -1
         batch.nSequentialRuns = -1
         batch.maxRating = -1.

      for opt in furtherOpts:
         if opt.valid and (opt.rating > batch.maxRating):
            batch.maxRating = opt.rating
            batch.nParallelRuns = opt.nParallelRuns
            batch.nSequentialRuns = opt.nSequentialRuns
      if batch.maxRating <= 0.:
         raise Exception("Something went wrong in AllocateResources. No valid option found")


def GetQueue(batch):
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



class Option():
   def __init__(self,batch,**kwargs):
      if np.any([a<=0 for a in kwargs.values()]):
         self.rating=-1.
         self.valid=False
         return
      if "nSequentialRuns" in kwargs:
         self.nSequentialRuns = kwargs["nSequentialRuns"]
         self.nParallelRuns = ( batch.nParallelRunsPackage *   
                                int(math.ceil(batch.samples.n / (self.nSequentialRuns*batch.nParallelRunsPackage))) )
      else:
         if "nParallelRuns" in kwargs:
            self.nParallelRuns = kwargs["nParallelRuns"]
         else:
            self.nParallelRuns = batch.nParallelRunsPackage*int(math.ceil(batch.idealCores / batch.nCoresPackage))
         self.nSequentialRuns = int(math.ceil( batch.samples.n / self.nParallelRuns ))
      self.walltime = self.nSequentialRuns*batch.scaledAvgWalltime
      self.nCores= self.nParallelRuns*batch.nCoresPerSample

      self.Rating(batch)
      self.CheckValid(batch)


   def Rating(self,batch): 
      self.queueRating = min( batch.idealCores / self.nCores , batch.idealWt / self.walltime ) 
      self.effiencyRating = batch.samples.n / (self.nParallelRuns * self.nSequentialRuns)
      self.rating = self.effiencyRating ** 3. * self.queueRating

   def CheckValid(self,batch):
      self.valid = ( ( batch.boundsParallel[0]   <= self.nParallelRuns   <= batch.boundsParallel[1]   ) and
                     ( batch.boundsSequential[0] <= self.nSequentialRuns <= batch.boundsSequential[1] ) )

def SmallQueue(batch):
   batch.queue = "small"
   batch.wtFunc = [5.*60, 24.*60 ]
   batch.coresFunc = [1*24, 10*24]
   batch.boundsParallel = [batch.nParallelRunsPackage, batch.nParallelRunsMax]
   batch.boundsSequential = [1, batch.nSequentialRunsMax]

def MultiQueue(batch):
   batch.queue = "multi"
   batch.wtFunc = [30.*60, 4.*3600 ]
   batch.coresFunc = [48*24, 192*24]
   batch.boundsParallel = [batch.nParallelRunsMultiMin, batch.nParallelRunsMax]
   batch.boundsSequential = [batch.nSequentialRunsMultiMin, batch.nSequentialRuns4hMax]

def LongQueue(batch):
   batch.queue = "long"
   batch.wtFunc = [4.*3600, 8.*3600 ]
   batch.coresFunc = [500*24, 500*24]
   batch.boundsParallel = [batch.nParallelRunsMultiMin, batch.nParallelRunsMax]
   batch.boundsSequential = [1, batch.nSequentialRunsMax]


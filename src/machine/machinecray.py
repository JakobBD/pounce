import time
import glob
import os
import math
import numpy as np
import subprocess

from .machine import Machine
from helpers.time import *
from helpers.printtools import *

@Machine.RegisterSubclass('cray')
class Cray(Machine):
   """Definition of Cray Hazelhen machine.
   """
   subclassDefaults={
      "username" : "NODEFAULT",
      "walltimeFactor" : 1.2,
      "nMaxCores" : 10000,
      "maxWalltime" : 86400, # 24h
      "maxTotalWork" : 36E6  # 10.000 CoreH
      }

   levelDefaults={
      "avgWalltime" : "NODEFAULT",
      }

   def __init__(self,classDict):
      self.nCoresPerNode = 24
      self.totalWork = 0.
      super().__init__(classDict)

   def RunBatch(self,runCommand,nCoresPerSample,nCurrentSamples,avgNodes,solver,fileNameStr):
      """Runs a job by generating the necessary jobfile
          and submitting it.
      """
      self.GenerateJob(runCommand,nCoresPerSample,nCurrentSamples,avgNodes,solver,fileNameStr)
      return self.SubmitJob(fileNameStr)

   def GenerateJob(self,runCommand,nCoresPerSample,nCurrentSamples,avgNodes,solver,fileNameStr):
      """Generates the necessary jobfile.
      """
      jobfileString = '#!/bin/bash\n'
      jobfileString = jobfileString + '#PBS -N {}\n'.format(solver.projectName)
      timeHelper=Time(nCurrentSamples*nCoresPerSample)
      jobfileString = jobfileString + '#PBS -l nodes={}:ppn=24\n'.format(avgNodes)
      jobfileString = jobfileString + '#PBS -l walltime={}\n'.format( timeHelper.list())
      jobfileString = jobfileString + 'WORKDIR=\'{}\'\n'.format(os.getcwd())
      jobfileString = jobfileString + 'cd $WORKDIR \n'
      jobfile = open('jobfile_{}'.format(fileNameStr),'w')
      jobfile.write(jobfileString)
      avg_cores=int(nCoresPerSample*24)
      jobfile.write('aprun -n  {}  -N 24 {}  &> calc_{}.log \
      \n'.format(avg_cores,runCommand,fileNameStr))
      jobfile.close()

   def SubmitJob(self,fileNameStr):
      """Submits a job into the Cray Hazelhen HPC queue.
      """
      job = subprocess.Popen(['qsub','jobfile_{}'.format(fileNameStr)],stdout=subprocess.PIPE)
      jobID_tmp = job.stdout.read()
      jobID_tmp = jobID_tmp.split(".")[0]
      jobID = int(jobID_tmp)
      return jobID

   def WaitFinished(self,jobHandles):
      """Monitors all jobs on Cray Hazelhen HPC queue. Checks if jobfile finished.
      """
      status_list=[]
      comp_finished=None
      unfinished_jobs=None
      n_remain=len(jobHandles)
      while not comp_finished:
         job = subprocess.Popen(['qstat','-u',self.username],stdout=subprocess.PIPE)
         status_tmp = job.stdout.read()
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
                           [jobHandles,unfinished_jobs,n_remain]=CheckErrorfile(i,jobHandles,unfinished_jobs,index,n_remain)
                        else:
                           status_string="id {} has status {}".format(i,status)
                           if not status_string in status_list:
                              status_list.append(status_string)
                              print("Job with {}!".format(status_string))
               if not found: # jobID is not in st: pretend it is finished
                  [jobHandles,unfinished_jobs,n_remain]=CheckErrorfile(i,jobHandles,unfinished_jobs,index,n_remain)
         if sum(jobHandles)==0:
            comp_finished=True
         else:
            time.sleep(1)
      return(unfinished_jobs)

   def CheckErrorfile(i,jobID,unfinished_jobs,index,n_remain):
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

   def CheckAllFinished(self):
      """Checks if all computations finished and all files are available.
      """
      return True

   def AllocateResources(self,level):
      """Takes the properties of the level (number of current samples, walltime and cores of current sample) 
      as well as the machine properties or machine input (number of cores per node, max nodes etc.) 
      and outputs number of cores and number of parallel runs for 
      """

      self.walltimeFactor = 1.2
      level.scaledAvgWalltime=self.walltimeFactor*level.avgWalltime
      level.work=level.scaledAvgWalltime*level.nCoresPerSample*level.nCurrentSamples

      self.GetPackageProperties(level)

      self.GetNRunsMax(level)
      
      GetQueue(level)

      self.GetBestOption(level)

      level.nCores = level.nParallelRuns * level.nCoresPerSample
      level.batchWalltime = level.nSequentialRuns * level.scaledAvgWalltime
      level.nNodes = level.nCores / self.nCoresPerNode

      self.totalWork += level.nCores * level.batchWalltime
      if self.totalWork > self.maxTotalWork:
         raise Exception("Max total core hours exceeded!")

      Print("")
      Print("nParallelRuns = %i"%(level.nParallelRuns))
      Print("nSequentialRuns = %i"%(level.nSequentialRuns))
      Print("")
      Print("nCores = %i"%(level.nCores))
      Print("batchWalltime = %f"%(level.batchWalltime))


   def GetPackageProperties(self,level):
      level.nParallelRunsPackage = max( 1, self.nCoresPerNode // level.nCoresPerSample)
      level.nCoresPackage = level.nCoresPerSample*level.nParallelRunsPackage
      if level.nCoresPackage%self.nCoresPerNode: 
         raise Exception("nCoresPerSample has to be multiple of nCoresPerNode or vice versa")
      if level.nCoresPackage > self.nMaxCores:
         raise Exception("nMaxCores (%i) too small for smallest batch nCores (%i)"%(self.nMaxCores,nCores))

   def GetNRunsMax(self,level):
      level.nSequentialRunsMax = level.scaledAvgWalltime * ( self.maxWalltime // level.scaledAvgWalltime )
      if level.nSequentialRunsMax == 0: 
         raise Exception("A single job takes longer than the set walltime maximum. I cannot work like this.")

      level.nParallelRunsMax = ( level.nCoresPackage * (self.nMaxCores // level.nCoresPackage) ) / level.nCoresPerSample
      if level.nParallelRunsMax*level.nSequentialRunsMax < level.nCurrentSamples: 
         PrintWarning("The limits set for #Cores and walltime are too small for this batch. nSamples is reduced.")


   def GetBestOption(self,level):
      baseOpt = Option(level)
      level.nParallelRuns = baseOpt.nParallelRuns
      level.nSequentialRuns = baseOpt.nSequentialRuns

      furtherOpts = []
      for i in range(-50,50): 
         furtherOpts.append( Option( level,nParallelRuns=level.nParallelRuns+i*level.nParallelRunsPackage) )
         furtherOpts.append( Option( level,nSequentialRuns=level.nSequentialRuns+i) )

      if baseOpt.valid: 
         level.maxRating = baseOpt.rating
      else:
         level.nParallelRuns = -1
         level.nSequentialRuns = -1
         level.maxRating = -1.

      for opt in furtherOpts:
         if opt.valid and (opt.rating > level.maxRating):
            level.maxRating = opt.rating
            level.nParallelRuns = opt.nParallelRuns
            level.nSequentialRuns = opt.nSequentialRuns
      if level.maxRating <= 0.:
         raise Exception("Something went wrong in AllocateResources. No valid option found")


def GetQueue(level):
   # in order for the multi queue to be used, nParallelRunsMultiMin
   level.nSequentialRunsMultiMin = int(math.ceil( 5*60 / level.scaledAvgWalltime  ))
   level.nParallelRunsMultiMin = level.nParallelRunsPackage * int(math.ceil( 48*24 / level.nCoresPackage ))

   level.nSequentialRuns4hMax = level.scaledAvgWalltime* ( 4*3600 // level.scaledAvgWalltime )
   efficiencyVsQueueFactor = 0.9
   nSamplesMulti = (
   efficiencyVsQueueFactor     *max( level.nParallelRunsMultiMin   *(level.nSequentialRunsMultiMin-1),
                                    (level.nParallelRunsMultiMin-1)* level.nSequentialRunsMultiMin    ) + 
   (1.-efficiencyVsQueueFactor)*min( level.nParallelRunsMultiMin   *(level.nSequentialRunsMultiMin-1),
                                    (level.nParallelRunsMultiMin-1)* level.nSequentialRunsMultiMin    ) )

   if nSamplesMulti >= level.nCurrentSamples:
      Print("Small Queue")
      SmallQueue(level)
   elif level.nSequentialRuns4hMax*level.nParallelRunsMax < level.nCurrentSamples: 
      LongQueue(level)
      Print("Long Queue")
   else: 
      MultiQueue(level)
      Print("Multi Queue")

   #fill ideal values according to queue
   level.workFunc = [a*b for a,b in zip(level.wtFunc,level.coresFunc)]
   level.expWt = np.log(level.wtFunc[1]/level.wtFunc[0]) / np.log(level.workFunc[1]/level.workFunc[0])
   level.expCores = 1 - level.expWt
   level.idealWt = level.wtFunc[0] * (level.work / level.workFunc[0])**level.expWt
   level.idealCores = level.coresFunc[0] * (level.work / level.workFunc[0])**level.expCores
   Print("")
   Print("expWt = %f"%(level.expWt))
   Print("idealCores = %f"%(level.idealCores))
   Print("idealWt = %f"%(level.idealWt))



class Option():
   def __init__(self,level,**kwargs):
      if np.any([a<=0 for a in kwargs.values()]):
         self.rating=-1.
         self.valid=False
         return
      if "nSequentialRuns" in kwargs:
         self.nSequentialRuns = kwargs["nSequentialRuns"]
         self.nParallelRuns = ( level.nParallelRunsPackage *   
                                int(math.ceil(level.nCurrentSamples / (self.nSequentialRuns*level.nParallelRunsPackage))) )
      else:
         if "nParallelRuns" in kwargs:
            self.nParallelRuns = kwargs["nParallelRuns"]
         else:
            self.nParallelRuns = level.nParallelRunsPackage*int(math.ceil(level.idealCores / level.nCoresPackage))
         self.nSequentialRuns = int(math.ceil( level.nCurrentSamples / self.nParallelRuns ))
      self.walltime = self.nSequentialRuns*level.scaledAvgWalltime
      self.nCores= self.nParallelRuns*level.nCoresPerSample

      self.Rating(level)
      self.CheckValid(level)
      Print("OPTION:")
      Print("OPTION:")
      Print("nParallelRuns = %i"%(self.nParallelRuns))
      Print("nSequentialRuns = %i"%(self.nSequentialRuns))
      Print("queueRating = %f"%(self.queueRating))
      Print("effiencyRating = %f"%(self.effiencyRating))
      Print("rating = %f"%(self.rating))
      Print("valid = {}".format(self.valid))


   def Rating(self,level): 
      self.queueRating = min( level.idealCores / self.nCores , level.idealWt / self.walltime ) 
      self.effiencyRating = level.nCurrentSamples / (self.nParallelRuns * self.nSequentialRuns)
      self.rating = self.effiencyRating ** 3. * self.queueRating

   def CheckValid(self,level):
      self.valid = ( ( level.boundsParallel[0]   <= self.nParallelRuns   <= level.boundsParallel[1]   ) and
                     ( level.boundsSequential[0] <= self.nSequentialRuns <= level.boundsSequential[1] ) )

def SmallQueue(level):
   level.wtFunc = [5.*60, 24.*60 ]
   level.coresFunc = [1*24, 10*24]
   level.boundsParallel = [level.nParallelRunsPackage, level.nParallelRunsMax]
   level.boundsSequential = [1, level.nSequentialRunsMax]

def MultiQueue(level):
   level.wtFunc = [30.*60, 4.*3600 ]
   level.coresFunc = [48*24, 192*24]
   level.boundsParallel = [level.nParallelRunsMultiMin, level.nParallelRunsMax]
   level.boundsSequential = [level.nSequentialRunsMultiMin, level.nSequentialRuns4hMax]

def LongQueue(level):
   level.wtFunc = [4.*3600, 8.*3600 ]
   level.coresFunc = [500*24, 500*24]
   level.boundsParallel = [level.nParallelRunsMultiMin, level.nParallelRunsMax]
   level.boundsSequential = [1, level.nSequentialRunsMax]

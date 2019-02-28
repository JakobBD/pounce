import shlex
import subprocess

from .machine import Machine
from helpers.printtools import *

@Machine.RegisterSubclass('local')
class Local(Machine):
   """Class: Defines local machine. Machine executes Samples.
   Args:

   Returns:
   """
   subclassDefaults={
      "mpi" : "NODEFAULT"
      }

   def RunBatches(self,batches,simulation,solver,postProc=False):
      """Runs a job by calling a subprocess.
      """
      # TODO: enable parallel runs of jobs
      for batch in batches:
         batch.logfileName="log_"+batch.name+".dat"
         if self.mpi:
            args=["mpirun", "-n %d"%(batch.nCoresPerSample), batch.runCommand]
         else:
            args=shlex.split(batch.runCommand)
         Print("run command "+yellow(batch.runCommand))
         with open(batch.logfileName,'w+') as f:
            subprocess.run(args,stdout=f)
      if not postProc:
         solver.CheckAllFinished(batches)

   def AllocateResources(self,batches):
      for batch in batches:
         batch.nParallelRuns=1
         batch.nSequentialRuns=batch.samples.n

   def PreparePostProc(self,batches,solver):
      for batch in batches:
         solver.PreparePostprocessing(batch)

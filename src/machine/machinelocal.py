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

   def RunBatch(self,runCommand,nCoresPerSample,solver):
      """Runs a job by calling a subprocess.
      """
      self.SubmitJob(runCommand,nCoresPerSample,solver)

   def SubmitJob(self,runCommand,nCoresPerSample,solver):
      """Call the subprocess command to run the solver.
      """
      # TODO: enable parallel runs of jobs
      if self.mpi:
         args=["mpirun", "-n %d"%(nCoresPerSample), runCommand]
         Print("run command "+yellow(" ".join(args)))
         subprocess.run(args)
      else:
         Print("run command "+yellow(runCommand))
         subprocess.call(shlex.split(runCommand))
      pass

   def AllocateResources(self):
      """Allocates the recources depending on the job to be executed.
      """
      pass

   def WaitFinished(self,jobHandles):
      """
      Since we are on a local machine without submit script, all jobs are already finished.
      """
      pass


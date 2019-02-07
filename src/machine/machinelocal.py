import shlex
import subprocess

from .machine import Machine
from helpers.printtools import *

@Machine.RegisterSubclass('local')
class LocalSystem(Machine):
   """Class: Defines local machine. Machine executes Samples.
   Args:

   Returns:
   """
   subclassDefaults={
      "mpi" : "NODEFAULT"
      }

   def RunBatch(self,runCommand,nCoresPerSample,solver):
      self.SubmitJob(runCommand,nCoresPerSample,solver)

   def SubmitJob(self,runCommand,nCoresPerSample,solver):
      if self.mpi:
         args=["mpirun", "-n %d"%(nCoresPerSample), runCommand]
         Print("run command "+yellow(" ".join(args)))
         subprocess.run(args)
      else:
         Print("run command "+yellow(runCommand))
         subprocess.call(shlex.split(runCommand))
      pass

   def AllocateRecources(self):
      pass


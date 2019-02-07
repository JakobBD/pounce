import shlex
import subprocess

from .machine import Machine

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
         # print("mpirun -n %d"%(nCoresPerSample)+" "+runCommand)
         subprocess.run(["mpirun", "-n %d"%(nCoresPerSample), runCommand])
      else:
         print(runCommand + "\n")
         subprocess.call(shlex.split(runCommand))
      pass

   def AllocateRecources(self):
      pass


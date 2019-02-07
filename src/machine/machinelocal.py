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

   def RunBatch(self,sublevel,solver):
      self.SubmitJob(sublevel,solver)

   def SubmitJob(self,sublevel,solver):
      if self.mpi:
         # print("mpirun -n %d"%(sublevel.nCoresPerSample)+" "+sublevel.runCommand)
         subprocess.run(["mpirun", "-n %d"%(sublevel.nCoresPerSample), sublevel.runCommand])
      else:
         print(sublevel.runCommand + "\n")
         subprocess.call(shlex.split(sublevel.runCommand))
      pass

   def AllocateRecources(self):
      pass


import shlex
import subprocess

from .machine import Machine

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
      if self.mpi:
         # print("mpirun -n %d"%(nCoresPerSample)+" "+runCommand)
         subprocess.run(["mpirun", "-n %d"%(nCoresPerSample), runCommand])
      else:
         print(runCommand + "\n")
         subprocess.call(shlex.split(runCommand))
      pass

   def AllocateResources(self):
      """Allocates the recources depending on the job to be executed.
      """
      pass


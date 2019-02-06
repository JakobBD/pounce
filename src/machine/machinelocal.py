import subprocess

from .machine import Machine

@Machine.RegisterSubclass('local')
class LocalSystem(Machine):
   """Class: Defines local machine. Machine executes Samples. 
   Args:

   Returns:
   """
   pass

   def RunBatch(self,sovler):
      self.submitJob(solver)
   
   def SubmitJob(self,solver):
      if self.mpi:
         subprocess.run(["mpirun", "-n%d"%(solver.coresPerSample), solver.runCommand])
      else:
         subprocess.run([solver.runCommand])
      pass
   
   def AllocateRecources(self):
      pass


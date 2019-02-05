import subprocess

from .machine import Machine

@Machine.RegisterSubclass('local')
class LocalSystem(Machine):
   """Class: Defines local machine. Machine executes Samples. 
   Args:

   Returns:
   """
   pass

def runBatch(self,sovler):
   self.submitJob(solver)

def submitJob(self,solver):
   if self.mpi:
      subprocess.run(["mpirun", "-n%d"%(solver.coresPerSample), solver.runCommand])
   else:
      subprocess.run([solver.runCommand])
   pass

def allocateRecources(self):
   pass


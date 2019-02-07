from .machine import Machine

@Machine.RegisterSubclass('cray')
class CrayCluster(Machine):
   """Class: Defines CrayCluster machine. Machine executes Samples.
   Args:

   Returns:
   """
   pass

def runBatch(self,sovler):
   self.generateJob(solver)
   self.submitJob(solver)
   self.monitorJob(solver)

def generateJob(self):
   pass

def submitJob(self,solver):
   if self.mpi:
      subprocess.run(["mpirun", "-n%d"%(solver.coresPerSample), solver.runCommand])
   else:
      subprocess.run([solver.runCommand])
   pass

def monitorJob(self):
   pass

def allocateRecources(self):
   pass



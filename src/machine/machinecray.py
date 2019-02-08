from .machine import Machine

@Machine.RegisterSubclass('cray')
class Cray(Machine):
   """Definition of Cray Hazelhen machine. 
   """
   pass

   def RunBatch(self,sovler):
      """Runs a job by generating the necessary jobfile,
      submitting the jobfile and monitoring this job in the HPC queue.
      """
      self.generateJob(solver)
      self.submitJob(solver)
      self.monitorJob(solver)
   
   def GenerateJob(self):
      """Generates the necessary jobfile to submit a job in the queue.
      """
      pass
   
   def SubmitJob(self,solver):
      """Submits a job into the Cray Hazelhen HPC queue.
      """
      pass
   
   def MonitorJob(self):
      """Monitors a job in the Cray Hazelhen HPC queue.
      """
      pass
   
   def AllocateResources(self):
      """Allocates the recources depending on the job to be executed.
      """
      pass
   


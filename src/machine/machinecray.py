import subprocess
from .machine import Machine

@Machine.RegisterSubclass('cray')
class Cray(Machine):
   """Definition of Cray Hazelhen machine.
   """
   subclassDefaults={
      "username" : "NODEFAULT"
      }

   def RunBatch(self,runCommand,nCoresPerSample,solver):
      """Runs a job by generating the necessary jobfile
          and submitting it.
      """
      self.GenerateJob(runCommand,nCoresPerSample,solver)
      return self.submitJob()

   def GenerateJob(self,runCommand,nCoresPerSample,solver):
      """Generates the necessary jobfile.
      """
      jobfile = open('jobfile_{}{}'.format(sublevel.level.ind,sublevel.subName),'w')
      avg_cores=int(nCoresPerSample*24)
      jobfile.write('aprun -n  {}  -N 24 {}  &> calc_{}{}.log \
      \n'.format(avg_cores,sublevel.runCommand,sublevel.level.ind, sublevel.subName))

   def SubmitJob(self,solver):
      """Submits a job into the Cray Hazelhen HPC queue.
      """
      job = subprocess.Popen(['qsub',jobfile],stdout=subprocess.PIPE)
      jobID_tmp = job.stdout.read()
      jobID_tmp = jobID_tmp.split(".")[0]
      jobID = int(jobID_tmp)
      return jobID

   def WaitFinished(self,jobHandles):
      """Monitors all jobs on Cray Hazelhen HPC queue. Checks if jobfile finished.
      """
      status_list=[]
      comp_finished=None
      unfinished_jobs=None
      n_remain=len(jobHandles)
      while not comp_finished:
         job = subprocess.Popen(['qstat','-u',self.username],stdout=subprocess.PIPE)
         status_tmp = job.stdout.read()
         status_tmp = status_tmp.split('\n')
         if len(status_tmp)<4:
            jobs_in_queue=None
         else:
            jobs_in_queue=True
            status_tmp = status_tmp[5:]
            del status_tmp[-1]
         for index,i in enumerate(jobHandles):
            if i > 0:
               found=None
               if jobs_in_queue:
                  for line in status_tmp:
                     id = int(line.split(".")[0])
                     if i==id:
                        found=True
                        status = line.split()[9]
                        if status=='C':
                           [jobHandles,unfinished_jobs,n_remain]=check_errorfile(i,jobHandles,unfinished_jobs,index,n_remain,do_exit)
                        else:
                           status_string="id {} has status {}".format(i,status)
                           if not status_string in status_list:
                              status_list.append(status_string)
                              print("Job with {}!".format(status_string))
               if not found: # jobID is not in st: pretend it is finished
                  [jobHandles,unfinished_jobs,n_remain]=check_errorfile(i,jobHandles,unfinished_jobs,index,n_remain,do_exit)
         if sum(jobHandles)==0:
            comp_finished=True
         else:
            time.sleep(1)
      return(unfinished_jobs)

   def CheckAllFinished(self):
      """Checks if all computations finished and all files are available.
      """
      return True

   def AllocateResources(self):
      """Allocates the recources depending on the job to be executed.
      """
      pass

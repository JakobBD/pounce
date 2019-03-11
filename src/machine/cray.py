import time
import glob
import os
import math
import numpy as np
import subprocess

from .machine import Machine
from helpers.time import *
from helpers.printtools import *
from helpers.tools import *

@Machine.register_subclass('cray')
class Cray(Machine):
    """Definition of Cray Hazelhen machine.
    """
    subclass_defaults={
        "username" : "NODEFAULT",
        "walltime_factor" : 1.2,
        "n_max_cores" : 10000,
        "max_walltime" : 86400, # 24h
        "max_total_work" : 36e5  # 1.000 CoreH
        }

    level_defaults={
        "avg_walltime_postproc" : 120.
        }

    def __init__(self,class_dict):
        self.cores_per_node = 24
        self.total_work = 0.
        super().__init__(class_dict)


    def allocate_resources_postproc(self,batches):
        for batch in batches:
            batch.n_cores=self.cores_per_node


    def run_batches(self,batches,simulation,solver,postproc_type=False):
        """Runs a job by generating the necessary jobfile
             and submitting it.
        """
        # in case of a restart, only submit
        for batch in self.unfinished(batches):
            if not getattr(batch,"queue_status",None):
                self.submit_job(batch,solver,simulation)
        self.wait_finished(batches,simulation)

        if not postproc_type:
            solver.check_all_finished(batches)
        # reset for next iteration
        for batch in batches:
            batch.finished=False

    def unfinished(self,batches):
        return [b for b in batches if not getattr(b,"finished",False)]


    def submit_job(self,batch,solver,simulation):
        """Generates the necessary jobfile and submits job.
        """
        jobfile_string = (
              '#!/bin/bash\n'
            + '#PBS -N {}\n'.format(solver.project_name)
            + '#PBS -l nodes={}:ppn=24\n'.format(batch.n_cores)
            + '#PBS -l walltime='+Time(batch.batch_walltime).str+"\n\n"
            + 'cd $PBS_O_WORKDIR\n\n'
            + 'aprun -n  {}  -N 24 {}  &> calc_{}.log\n'.format(
                batch.n_cores,batch.run_command,batch.name))
        batch.jobfile_name = 'jobfile_{}'.format(batch.name)
        with open(batch.jobfile_name,'w+') as jf:
            jf.write(jobfile_string)
        # submit job
        job = subprocess.run(
            ['qsub',batch.jobfile_name],stdout=subprocess.PIPE,
            universal_newlines=True)
        batch.job_id=int(job.stdout.split(".")[0])
        p_print("submitted job "+str(batch.job_id))
        batch.queue_status="submitted"
        simulation.iterations[-1].update_step(simulation)


    def wait_finished(self,batches,simulation):
        """Monitors all jobs on Cray Hazelhen HPC queue. 
        Checks if jobfile finished.
        """
        while True:
            statuses=self.read_qstat()
            for batch in self.unfinished(batches):
                if batch.job_id in statuses:
                    queue_status = statuses[batch.job_id]
                else:
                    queue_status = "C"
                if not queue_status == batch.queue_status:
                    p_print("Job {} with ID {} has status {}.".format(
                        batch.name,batch.job_id,queue_status))
                    batch.queue_status=queue_status
                if queue_status=='C':
                    self.check_errorfile(batch,batches,simulation)
            if not self.unfinished(batches):
                return
            time.sleep(1)


    def read_qstat(self):
        """run 'qstat' on cray and read output
        """
        job = subprocess.Popen(['qstat','-u',self.username],
                               stdout=subprocess.PIPE,universal_newlines=True)
        lines = str(job.stdout.read()).split('\n')
        if len(lines)<4:
            return {}
        else:
            def id(line): 
                return int(line.split(".")[0])
            def stat(line):
                return line.split()[9]
            return {id(line):stat(line) for line in lines[5:-1]}


    def check_errorfile(self,batch,batches,simulation):
        """open error file and parse errrors. 
        Well, parse is a strong word here.
        """
        with open(glob.glob('*.e{}'.format(batch.job_id))[0]) as f:
            lines = f.read().splitlines()
        # empty error file: all good
        if len(lines)==0:
            batch.finished=True
            batch.queue_status=None
            p_print('job ID {} is now complete! {} jobs remaining'.format(
                batch.job_id,len(self.unfinished(batches))))
            return
        # check if walltime excced in error file (also means that solver did not otherwise crash)
        longlines=[line.split() for line in lines if len(line.split())>=7]
        for words in longlines:
            if words[4]=='walltime' and words[6]=='exceeded':
                p_print("Job {} exceeded walltime ({}). ".format(
                            batch.name,Time(batch.walltime).str)
                        +"Re-submit with double walltime.")
                batch.walltime *= 2
                self.submit_job(batch,solver,simulation)
                return
        # non-empty error file and not walltime excceded: other error
        raise Exception('Error in jobfile execution! '
                        + 'See file *.e{} for details.'.format(batch.job_id))


    def allocate_resources(self,batches):
        """Takes the properties of the batch (number of current samples,
        walltime and cores of current sample) as well as the machine 
        properties or machine input (number of cores per node, max nodes
        etc.) and outputs number of cores and number of parallel runs 
        for this batch.
        """

        self.walltime_factor = 1.2
        stdout_table=StdOutTable(
            "queue","max_rating","n_parallel_runs","n_sequential_runs",
            "n_cores","n_nodes","batch_walltime")
        stdout_table.descriptions(
            "Queue","Rating","n_parallel_runs","n_sequential_runs",
            "n_cores","n_nodes","batch_walltime")

        for batch in batches:
            batch.scaled_avg_walltime=self.walltime_factor*batch.avg_walltime
            batch.work=batch.scaled_avg_walltime * batch.cores_per_sample\
                * batch.samples.n

            # make sure to fill a node
            self.get_package_properties(batch)

            # decide which queue to use 
            get_queue(batch)

            # core of this routine:
            # get n_parallel_runs and n_sequential_runs
            self.get_best_option(batch)

            # some serived quantities
            batch.n_cores = batch.n_parallel_runs * batch.cores_per_sample
            batch.batch_walltime = batch.n_sequential_runs \
                * batch.scaled_avg_walltime
            batch.n_nodes = batch.n_cores / self.cores_per_node

            self.total_work += batch.n_cores * batch.batch_walltime
            if self.total_work > self.max_total_work:
                raise Exception("Max total core hours exceeded!")

            stdout_table.update(batch)
        stdout_table.p_print("Batch")


    def get_package_properties(self,batch):
        """define a "package" of runs to fill a node, 
        e.g. 4 parallel runs with cores_per_sample=6.
        trivial if cores_per_sample >= 24.
        """
        batch.parallel_runs_package = \
            max( 1, self.cores_per_node // batch.cores_per_sample)
        batch.n_cores_package = \
            batch.cores_per_sample*batch.parallel_runs_package
        if batch.n_cores_package%self.cores_per_node:
            raise Exception("cores_per_sample has to be multiple of"
                            "cores_per_node or vice versa")
        batch.parallel_runs_max= (self.n_max_cores // batch.n_cores_package) \
            * batch.parallel_runs_package
        if batch.n_cores_package > self.n_max_cores:
            raise Exception("n_max_cores (%i) too small "%(self.n_max_cores)
                            + "for smallest batch n_cores (%i)"%(
                                batch.n_cores_package))
        batch.sequential_runs_max=int(self.max_walltime//batch.avg_walltime)


    def get_best_option(self,batch):
        """Loop over all possible combinations of n_parallel_runs and 
        n_sequential_runs.
        Get Rating for all of them. Pick the best one.
        """
        batch.max_rating = -1.
        n_max=int(math.ceil(np.sqrt(
            batch.samples.n/batch.parallel_runs_package)))

        for i in range(1,n_max+1):
            opt1 = Option( batch,n_parallel_runs=i*batch.parallel_runs_package)
            opt2 = Option( batch,n_sequential_runs=i)

            for opt in [opt1,opt2]:
                if opt.valid and (opt.rating > batch.max_rating):
                    batch.max_rating = opt.rating
                    batch.n_parallel_runs = opt.n_parallel_runs
                    batch.n_sequential_runs = opt.n_sequential_runs

        if batch.max_rating <= 0.:
            raise Exception("Something went wrong in allocate_resources. "
                            "No valid option found")


class Option():
    """One combination of n_parallel_runs and n_sequential_runs. 
    Has a Rating based on efficiency (few idling cores) and expcted 
    queuing time.
    Invalid if does not match criteria of selected queue.
    """

    def __init__(self,batch,n_sequential_runs=None,n_parallel_runs=None):
        if n_sequential_runs:
            self.n_sequential_runs = n_sequential_runs

            n_seq=n_sequential_runs
            n_par=batch.parallel_runs_package
            n = batch.samples.n
            self.n_parallel_runs = (n_par*int(math.ceil(n/(n_seq *n_par))))
        elif n_parallel_runs:
            self.n_parallel_runs = n_parallel_runs
            self.n_sequential_runs = \
                int(math.ceil( batch.samples.n / self.n_parallel_runs ))
        self.walltime = self.n_sequential_runs*batch.scaled_avg_walltime
        self.n_cores= self.n_parallel_runs*batch.cores_per_sample

        self.rating(batch)
        self.check_valid(batch)

    def rating(self,batch):
        """Rating based on efficiency (few idling cores) and expcted 
        queuing time.
        """
        self.queue_rating = min(batch.ideal_cores / self.n_cores, 
                                batch.ideal_wt / self.walltime)
        self.effiency_rating = batch.samples.n \
                               / (self.n_parallel_runs*self.n_sequential_runs)
        self.rating = self.effiency_rating ** 3. * self.queue_rating

    def check_valid(self,batch):
        """Invalid if does not match criteria of selected queue.
        """
        self.valid = (    (batch.bounds_parallel[0]    
                           <= self.n_parallel_runs
                           <= batch.bounds_parallel[1]) 
                      and (batch.bounds_sequential[0] 
                           <= self.n_sequential_runs 
                           <= batch.bounds_sequential[1]))


def get_queue(batch):
    """check which queue the job is eligible for: 
    if possible, run on multi. If too small, run on small. 
    If too large, run on long (>4h)
    """
    # in order for the multi queue to be used, runs_multi_min
    batch.sruns_multi_min = int(math.ceil( 5*60 / batch.scaled_avg_walltime ))
    batch.pruns_multi_min = batch.parallel_runs_package \
                            * int(math.ceil( 48*24 / batch.n_cores_package ))

    batch.sequential_runs4h_max = batch.scaled_avg_walltime \
                                  * ( 4*3600 // batch.scaled_avg_walltime )
    # the clean solution: 
    # this is the maximum number of samples that should still be run in
    # the small queue, as the number of parallel or sequential runs
    # is too small for multi queue
    n_samples_no_waste = \
        max( batch.pruns_multi_min   *(batch.sruns_multi_min-1),
            (batch.pruns_multi_min-1)* batch.sruns_multi_min   )
    # this variant puts more jobs into the multi queue, at the cost of
    # reduced efficiency
    n_samples_often_multi = \
        min( batch.pruns_multi_min   *(batch.sruns_multi_min-1),
            (batch.pruns_multi_min-1)* batch.sruns_multi_min   )
    # weight both
    vs_queue_factor = 0.9
    n_samples_small = (       vs_queue_factor  * n_samples_no_waste
                        + (1.-vs_queue_factor) * n_samples_often_multi)

    if n_samples_small >= batch.samples.n:
        small_queue(batch)
    elif batch.sequential_runs4h_max*batch.parallel_runs_max < batch.samples.n:
        long_queue(batch)
    else:
        multi_queue(batch)

    #fill ideal values according to queue
    batch.work_func = [a*b for a,b in zip(batch.wt_func,batch.cores_func)]
    batch.exp_wt = np.log(batch.wt_func[1]/batch.wt_func[0]) \
                   / np.log(batch.work_func[1]/batch.work_func[0])
    batch.exp_cores = 1 - batch.exp_wt
    batch.ideal_wt = batch.wt_func[0] \
                     * (batch.work / batch.work_func[0])**batch.exp_wt
    batch.ideal_cores = batch.cores_func[0] \
                        * (batch.work / batch.work_func[0])**batch.exp_cores


def small_queue(batch):
    """multi queue cannot be filled with walltime > 5 min
    """
    batch.queue = "small"
    batch.wt_func = [5.*60, 24.*60 ]
    batch.cores_func = [1*24, 10*24]
    batch.bounds_parallel = \
        [batch.parallel_runs_package, batch.parallel_runs_max]
    batch.bounds_sequential = [1, batch.sequential_runs_max]

def multi_queue(batch):
    """preferred queue: n_nodes>=48, walltime < 4h
    """
    batch.queue = "multi"
    batch.wt_func = [30.*60, 4.*3600 ]
    batch.cores_func = [48*24, 192*24]
    batch.bounds_parallel = [batch.pruns_multi_min, batch.parallel_runs_max]
    batch.bounds_sequential = \
        [batch.sruns_multi_min, batch.sequential_runs4h_max]

def long_queue(batch):
    """with max_cores, walltime exceeds 4h
    """
    batch.queue = "long"
    batch.wt_func = [4.*3600, 8.*3600 ]
    batch.cores_func = [500*24, 500*24]
    batch.bounds_parallel = [batch.pruns_multi_min, batch.parallel_runs_max]
    batch.bounds_sequential = [1, batch.sequential_runs_max]


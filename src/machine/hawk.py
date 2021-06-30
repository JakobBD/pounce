import time
import glob
import os
import math
import numpy as np
import subprocess
import socket
import getpass
import prettytable as pt

from .machine import Machine
from helpers.printtools import *
from helpers.tools import *
from .local import Local
from helpers import globels

class Hawk(Machine):
    """
    Definition of HPE Hawk machine.
    """

    cname = "hawk"

    defaults_={
        "parallelization" : "mpi", # change default (options: "none", "mpi", "gnu")
        "work_safety_fac" : 1.2,
        "n_max_nodes" : 1024,
        "max_walltime" : 86400, # 24h
        "max_total_work" : 36e5, # 1.000 CoreH
        "remote" : False
        }

    defaults_add = { 
        "Batch": {
            'cores_per_sample': "dummy_unused",
            'cores_per_sample_min': "NODEFAULT",
            'cores_per_sample_max': "NODEFAULT",
            'est_work': "NODEFAULT", # in Core-s
            'n_elems': None
            }
        }

    # TODO: coherent errfiles in local/hawk; 
    #       piped or not? where does walltime exceeded go? 
    #       test check_errorfile on hawk (probably not functional)

    def __init__(self,class_dict):
        """
        check if POUNCE is run on Hawk or locally on a mounted
        directory. In the latter case, ssh is used to submit jobs
        and supervise the queuing status.
        """
        super().__init__(class_dict)
        self.cores_per_node = 128
        self.total_work = 0.
        # self.remote = not socket.gethostname().startswith('hawk-login')
        if self.remote: 
            args = "df -P .".split()
            job = subprocess.run(args,stdout=subprocess.PIPE,
                                 universal_newlines=True)
            line = job.stdout.split('\n')[1]
            self.ssh_command = line.split(":")[0]
            mount_dir_on_hawk = line.split()[0].split(":")[1]
            mount_dir_local = line.split()[-1]
            cwd = os.getcwd()
            self.dir_on_hawk=mount_dir_on_hawk+cwd.replace(mount_dir_local,"")


    def run_batches(self):
        """
        Runs batches by generating the necessary jobfiles,
        submitting them, and supervising the queuing status.
        """
        # in case of a restart, only submit
        for batch in self.unfinished_batches:
            if not getattr(batch,"queue_status",None):
                self.submit_job(batch)

        # stdout 
        print()
        table = pt.PrettyTable()
        table.field_names = [" "] + [yellow(b.name) for b in self.active_batches]
        table.add_row([yellow("Job ID")] + [b.job_id       for b in self.active_batches])
        table.add_row([yellow("Status")] + [b.queue_status for b in self.active_batches])
        table.vertical_char = "║"
        table.horizontal_char = "═"
        table.junction_char = "╬"

        for row in table.__str__().split("\n")[:-1]: 
            print(row)
        table.header = False
        table.hrules = pt.NONE

        self.wait_finished(table)

        table.hrules = pt.FRAME
        print(table.__str__().split("\n")[-1]) 

        self.check_all_finished()

        # reset for next iteration
        for batch in self.active_batches:
            batch.finished=False
            batch.queue_status=None


    def submit_job(self,batch,resub=False):
        """
        Generates the necessary jobfile and submits job for a batch
        """
        jobfile_string = (
              '#!/bin/bash\n'
            + '#PBS -N {}\n'.format(batch.full_name)
            + '#PBS -l select={}:node_type=rome:mpiprocs=128\n'.format(batch.n_nodes)
            + '#PBS -l walltime='+time_to_str(batch.batch_walltime)+"\n\n"
            + 'module load aocl/2.1.0\n'
            # + 'module load hfd5/1.10.5\n\n'
            + 'cd $PBS_O_WORKDIR\n\n')

        if not resub: 
            self.prepare_run_commands(batch)

        for i,run in enumerate(batch.run_commands): 
            jobfile_string += '{} 1> {} 2> {}\n'.format( run,
                batch.logfile_names[i], batch.logfile_names[i] )
        batch.jobfile_name = batch.full_name + "_jobfile"
        with open(batch.jobfile_name,'w+') as jf:
            jf.write(jobfile_string)
        # submit job
        args=['qsub',batch.jobfile_name]
        # args=['qsub','-q','test',batch.jobfile_name]
        if self.remote: 
           args=self.to_ssh(args)
        job = subprocess.run(args,shell=self.remote,stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,universal_newlines=True)
        lines = job.stdout.split("\n")
        # if self.remote: 
        lines = lines[:-1]
        batch.job_id=int(lines[-1].split(".")[0])
        p_print("submitted job "+str(batch.job_id)+" for batch "+batch.name)
        batch.queue_status="submitted"
        globels.update_step()
    
    def to_ssh(self,args): 
        """
        converts a command into the same command passed via ssh
        (each argument is an item of a list; in the ssh command, 
        the original command appears as one argument and thus one 
        string)
        """
        command = "cd "+self.dir_on_hawk+" && "+" ".join(args)
        return "echo '"+command+"' | ssh "+self.ssh_command

    def wait_finished(self,table):
        """
        Monitors all jobs on HPE Hawk HPC queue. 
        Checks if jobfile finished.
        """
        while True:
            # loop until all jobs are finished
            statuses=self.read_qstat()
            has_changes=False
            for batch in self.unfinished_batches:
                if batch.job_id in statuses:
                    queue_status = statuses[batch.job_id]
                else:
                    # after restart, completed job can be removed from qstat
                    queue_status = "C"
                if not queue_status == batch.queue_status:
                    # new status
                    batch.queue_status=queue_status
                    table.clear_rows()
                    table.add_row(["Status"] + ["    "+b.queue_status+"    " for b in self.active_batches])
                    has_changes=True
                if queue_status=='C':
                    self.check_errorfile(batch)
            if has_changes:
                print_table(table,add_cr=False)
            if not self.unfinished_batches:
                return
            time.sleep(1)


    def read_qstat(self):
        """
        run 'qstat' on hawk and read output
        """
        args=['qstat']
        if self.remote: 
           args=self.to_ssh(args)
        job = subprocess.run(args,shell=self.remote,stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,universal_newlines=True)
        lines = job.stdout.split('\n')
        for i_line,line in enumerate(lines): 
            if line.startswith("Job id"):
                break
        lines = lines[i_line:-1]
        # find last line with status 
        for i_line, line in enumerate(lines[2:]): 
            if line.find(".") != 7: 
                lines = lines[:i_line+2]
                break
        if len(lines)<3:
            return {}
        else:
            def id(line): 
                return int(line.split(".")[0])
            def stat(line):
                return line.split()[-2]
            return {id(line):stat(line) for line in lines[2:]}


    def check_errorfile(self,batch):
        """
        open error file and parse errrors. 
        Well, parse is a strong word here.
        """
        batch.errfile_name = batch.full_name + ".e" + str(batch.job_id)
        # sometimes hawk needs a while to finish up jobs
        if not os.path.isfile(batch.errfile_name):
            time.sleep(5)
        with open(batch.errfile_name) as f:
            lines = f.read().splitlines()
        # empty error file: all good
        for line in lines: 
            if line.find("PBS: job killed: walltime") > -1 and line.find("exceeded limit") > -1: 
                p_print("Batch {} job exceeded walltime ({}). ".format(
                            batch.name,time_to_str(batch.batch_walltime))
                        +"Re-submit with double walltime.")
                batch.batch_walltime *= 2
                self.submit_job(batch,resub=True)
                return
        # other error (disabled, since output is piped and module list output goes to stderr)
        # raise Exception('Error in jobfile execution! '
                        # + 'See file {} for details.'.format(batch.errfile_name))

        # no return means all runs finished normally
        batch.finished=True


    def allocate_resources(self):
        """
        Takes the properties of the batch (number of current samples,
        walltime and cores of current sample) as well as the machine 
        properties or machine input (number of cores per node, max nodes
        etc.) and outputs number of cores and number of parallel runs 
        for this batch.
        """
        if not self.multi_sample:
            for batch in self.active_batches:
                batch.n_cores=batch.cores_per_sample
                batch.n_nodes=((batch.cores_per_sample - 1) // self.cores_per_node) + 1
                batch.batch_walltime=batch.avg_walltime
            return

        table = pt.PrettyTable()
        table.field_names = ["batch", "efficiency (%)","# parallel runs",
                             "# sequential runs", "# cores / sample","# nodes",
                             "batch walltime","# elems / core"]

        for batch in self.active_batches:
            if globels.sim.current_iter.n > 1:
                est_work = batch.sum_work[batch.samples.n_previous]/batch.samples.n_previous
            else: 
                est_work = batch.est_work
            batch.scaled_est_work=self.work_safety_fac*est_work
            batch.work=batch.scaled_est_work * batch.samples.n

            self.get_opt_props(batch)

            self.total_work += batch.n_cores * batch.batch_walltime

            table.add_row([batch.name,
                           batch.efficiency,
                           batch.n_parallel_runs,
                           batch.n_sequential_runs,
                           batch.cores_per_sample,
                           batch.n_nodes,
                           batch.batch_walltime,
                           batch.n_elems_core])

        print_table(table)

        if self.total_work > self.max_total_work:
            raise Exception("Max total core hours exceeded!")


    def get_opt_props(self,batch):
        # optimal queue: 
        wt_func =    np.array([1.E-6, 1.,  5.*60,   3600.,   3600.,     24.*3600,     24.*3600])
        nodes_func = np.array([1,     1,   1,           8,      64,          512,     1024    ])
        work_func = wt_func*nodes_func*self.cores_per_node

        assert (work_func[0] < batch.work) and (work_func[-1] > batch.work)
        iu = np.argmax(work_func>batch.work)
        il = iu-1 

        if nodes_func[il] == nodes_func[iu]: 
            ideal_nodes = nodes_func[il]
        else: 
            exp_nodes = np.log(nodes_func[iu]/nodes_func[il]) / np.log(work_func[iu]/work_func[il])
            ideal_nodes = nodes_func[il] * (batch.work / work_func[il])**exp_nodes

        batch.n_nodes = 2**int(round(np.log(ideal_nodes)/np.log(2)))
        batch.n_nodes = min(self.n_max_nodes,max(1,batch.n_nodes))

        while True: 
            self.get_props(batch)
            if batch.batch_walltime <= self.max_walltime: 
                break
            else: 
                self.safe_double_nodes(batch)

    def safe_double_nodes(self,batch): 
        if batch.n_nodes < self.n_max_nodes: 
            batch.n_nodes *=2 
        else: 
            raise Exception("batch "+batch.name+" scheduling does not fit in max nodes / max wt")

    def get_props(self,batch):
        batch.n_cores_avail = batch.n_nodes*self.cores_per_node
        max_n_parallel_runs = min(batch.n_cores_avail // batch.cores_per_sample_min,batch.samples.n)
        if max_n_parallel_runs == 0: 
            # hack, which leads to doubling of nodes
            batch.batch_walltime = 2.*self.max_walltime
            return
        if batch.n_elems: 
            batch.max_elems_per_core = math.ceil(batch.n_elems/ batch.cores_per_sample_min)
            batch.min_elems_per_core = math.ceil(batch.n_elems/ batch.cores_per_sample_max)
            options = [Option(nec,batch) for nec in range(batch.min_elems_per_core,batch.max_elems_per_core+1)]
            i_best = np.argmax(np.array([o.efficiency for o in options]))
            options[i_best].adopt(batch)
        else: 
            batch.n_elems_core = None
            batch.n_sequential_runs = ((batch.samples.n-1) // max_n_parallel_runs)+1
            # reduce parallel runs if it does not increase sequential runs
            batch.n_parallel_runs = (batch.samples.n - 1)//batch.n_sequential_runs + 1 
            batch.cores_per_sample = min(batch.n_cores_avail // batch.n_parallel_runs, batch.cores_per_sample_max)
            batch.n_cores = batch.cores_per_sample*batch.n_parallel_runs
            if batch.n_nodes < 64: 
                batch.n_nodes = math.ceil(batch.n_cores/ self.cores_per_node)
            batch.batch_walltime = batch.n_sequential_runs*batch.scaled_est_work/batch.cores_per_sample
            batch.efficiency = batch.work / (batch.batch_walltime*batch.n_nodes*self.cores_per_node)


class Option(): 
    def __init__(self,n_elems_core,batch): 
        self.n_elems_core = n_elems_core
        min_cores_per_sample = math.ceil(batch.n_elems/n_elems_core)
        max_n_parallel_runs = min(batch.n_cores_avail // min_cores_per_sample,batch.samples.n)
        if max_n_parallel_runs < 1: 
            self.efficiency = -1 
            return
        self.n_sequential_runs = math.ceil(batch.samples.n / max_n_parallel_runs)
        # reduce parallel runs if it does not increase sequential runs
        self.n_parallel_runs = math.ceil(batch.samples.n/self.n_sequential_runs)
        self.cores_per_sample = min(batch.n_cores_avail // self.n_parallel_runs, batch.cores_per_sample_max)
        self.elem_efficiency = batch.n_elems/(n_elems_core*self.cores_per_sample)
        self.n_cores = self.cores_per_sample*self.n_parallel_runs
        self.batch_walltime = self.n_sequential_runs*batch.scaled_est_work/(self.cores_per_sample*self.elem_efficiency)
        self.efficiency = batch.work / (self.batch_walltime*batch.n_cores_avail)

    def adopt(self,batch): 
        if self.efficiency < 0: 
            raise Exception("only invalid options!")
        batch.n_elems_core = self.n_elems_core
        batch.n_sequential_runs = self.n_sequential_runs
        batch.n_parallel_runs = self.n_parallel_runs
        batch.cores_per_sample = self.cores_per_sample
        batch.n_cores = self.n_cores
        batch.batch_walltime = self.batch_walltime
        batch.efficiency = self.efficiency


import shlex
import subprocess
import math
import prettytable as pt

from .machine import Machine
from helpers.printtools import *
from helpers.tools import *

class Local(Machine):
    """
    Class: Defines local machine.
    Since no queuing is required, this all reduces
    to very basic routines.
    """

    cname = "local"

    defaults_={
        "parallelization" : "none", # options: "none", "mpi", "gnu"
        "n_max_cores" : 1, 
        }

    defaults_add = { 
        "Batch": {
            'cores_per_sample' : 1
            }
        }

    def run_batches(self):
        """
        Runs a job by calling a subprocess.
        """
        # TODO: do not change run_commands but create new variable instead
        # & pipe in different logfiles
        # OR: adapt check_finished to find errors even for several runs
        for batch in self.active_batches:
            if self.multi_sample and self.parallelization == "mpi": 
                self.to_mpi(batch)
            elif self.multi_sample and self.parallelization == "gnu": 
                self.to_gnu(batch)
            
            for i,cmd in enumerate(batch.run_commands):
                p_print("run command "+yellow(cmd))
                p_print("    logfile "+yellow(batch.logfile_names[i]))
                with open(batch.logfile_names[i],'w+') as f:
                    subprocess.run(cmd,stdout=f,shell=True)
        self.check_all_finished()

    def allocate_resources(self):
        if not self.multi_sample:
            p_print("Nothing to be done.")
            return
        if self.parallelization == "none": 
            p_print("No parallelization; All commands are run sequentially.")
            for batch in self.active_batches:
                batch.n_parallel_runs=1
                batch.n_sequential_runs=batch.samples.n
        elif self.parallelization in ["gnu","mpi"]: 
            table = pt.PrettyTable()
            table.field_names = ["batch", "# parallel runs", "# sequential runs", "# total cores"]
            for batch in self.active_batches:
                n_para_max = self.n_max_cores // batch.cores_per_sample
                batch.n_parallel_runs=min(n_para_max,batch.samples.n)
                batch.n_sequential_runs=math.ceil(batch.samples.n/batch.n_parallel_runs)
                batch.n_cores = batch.n_parallel_runs*batch.cores_per_sample
                table.add_row([batch.name,
                               batch.n_parallel_runs,
                               batch.n_sequential_runs,
                               batch.n_cores])
            print_table(table)
        else: 
            raise Exception("invalid parallelization type") 

    def to_mpi(self,batch): 
        batch.run_commands = ["mpirun -np {} {}".format(batch.n_cores, cmd) for cmd in batch.run_commands]

    def to_gnu(self,batch): 
        cmd_lists = [cmd.split(" ") for cmd in batch.run_commands]
        cmds_new = []
        for i in range(batch.n_sequential_runs): 
            i_min = i*batch.n_parallel_runs
            i_max = min((i+1)*batch.n_parallel_runs,batch.samples.n)
            runs_loc = cmd_lists[i_min:i_max]
            cmds_new.append(self.to_gnu_cmd(runs_loc))
        batch.run_commands = cmds_new

    def to_gnu_cmd(self,cmds): 
        out_list = []
        for args in zip(*cmds):
            if all(arg == args[0] for arg in args): 
                out_list.append(args[0])
            else: 
                out_list.append(" ".join(args))
        return "parallel --link -k " + " ::: ".join(out_list)
            



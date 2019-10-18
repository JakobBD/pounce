import shlex
import subprocess

from .machine import Machine
from helpers.printtools import *
from helpers.tools import *

class Local(Machine):
    """
    Class: Defines local machine.
    Since no queuing is required, this all reduces
    to very basic routines.
    """

    defaults_={
        "mpi" : "NODEFAULT"
        }

    defaults_add = { 
        "Batch": {
            'cores_per_sample' : 1,
            'avg_walltime': "dummy_unused",
            }
        }

    def run_batches(self):
        """
        Runs a job by calling a subprocess.
        """
        # TODO: enable parallel runs of jobs
        for batch in self.active_batches:
            for i,run in enumerate(batch.run_commands):
                if self.mpi and self.multi_sample:
                    args="mpirun -np {} {}".format(
                        batch.cores_per_sample, run)
                else:
                    args=run
                p_print("run command "+yellow(args))
                with open(batch.logfile_names[i],'w+') as f:
                    subprocess.run(args,stdout=f,shell=True)
        self.check_all_finished()

    def allocate_resources(self):
        if not self.multi_sample:
            p_print("Nothing to be done.")
            return
        p_print("All runs are carried out sequentially.")
        for batch in self.active_batches:
            batch.n_parallel_runs=1
            batch.n_sequential_runs=batch.samples.n


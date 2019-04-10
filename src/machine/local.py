import shlex
import subprocess

from .machine import Machine
from helpers.printtools import *

class Local(Machine):
    """Class: Defines local machine. Machine executes Samples.
    """

    defaults_={
        "mpi" : "NODEFAULT"
        }

    defaults_add = { 
        "Level": {
            'cores_per_sample' : 2,
            'avg_walltime': "dummy_unused",
            'avg_walltime_postproc': "dummy_unused"
            }
        }

    def run_batches(self,batches):
        """Runs a job by calling a subprocess.
        """
        # TODO: enable parallel runs of jobs
        for batch in batches:
            batch.logfile_name="log_"+batch.name+".dat"
            if self.mpi and self.multi_sample:
                args="mpirun -np {} {}".format(
                    batch.cores_per_sample, batch.run_command)
            else:
                args=batch.run_command
            p_print("run command "+yellow(args))
            with open(batch.logfile_name,'w+') as f:
                subprocess.run(args,stdout=f,shell=True)
        self.check_all_finished()

    def allocate_resources(self,batches):
        if not self.multi_sample:
            p_print("Nothing to be done.")
            return
        p_print("All runs are carried out sequentially.")
        for batch in batches:
            batch.n_parallel_runs=1
            batch.n_sequential_runs=batch.samples.n


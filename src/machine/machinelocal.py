import shlex
import subprocess

from .machine import Machine
from helpers.printtools import *

@Machine.register_subclass('local')
class Local(Machine):
    """Class: Defines local machine. Machine executes Samples.
    Args:

    Returns:
    """
    subclass_defaults={
        "mpi" : "NODEFAULT"
        }

    def run_batches(self,batches,simulation,solver,postproc_type=False):
        """Runs a job by calling a subprocess.
        """
        # TODO: enable parallel runs of jobs
        for batch in batches:
            batch.logfile_name="log_"+batch.name+".dat"
            if self.mpi:
                args=["mpirun", "-n %d"%(batch.cores_per_sample), batch.run_command]
            else:
                args=shlex.split(batch.run_command)
            p_print("run command "+yellow(batch.run_command))
            with open(batch.logfile_name,'w+') as f:
                subprocess.run(args,stdout=f)
        if not postproc_type:
            solver.check_all_finished(batches)

    def allocate_resources(self,batches):
        for batch in batches:
            batch.n_parallel_runs=1
            batch.n_sequential_runs=batch.samples.n

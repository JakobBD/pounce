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
        "mpi" : "NODEFAULT",
        'cores_per_sample' : 2
        }

    level_defaults={
        'avg_walltime' : "dummy_unused",
        'avg_walltime_postproc' : "dummy_unused"
        }

    def run_batches(self,batches,simulation,solver,postproc_type=False):
        """Runs a job by calling a subprocess.
        """
        # TODO: enable parallel runs of jobs
        for batch in batches:
            batch.logfile_name="log_"+batch.name+".dat"
            if self.mpi and not postproc_type:
                args="mpirun -np {} {}".format(
                    batch.cores_per_sample, batch.run_command)
            else:
                args=batch.run_command
            p_print("run command "+yellow(args))
            with open(batch.logfile_name,'w+') as f:
                subprocess.run(args,stdout=f,shell=True)
        if not postproc_type:
            solver.check_all_finished(batches)

    def allocate_resources(self,batches):
        p_print("All runs are carried out sequentially.")
        for batch in batches:
            batch.n_parallel_runs=1
            batch.n_sequential_runs=batch.samples.n

    run_batches_external=staticmethod(run_batches)

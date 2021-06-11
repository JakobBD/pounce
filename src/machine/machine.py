from helpers.baseclass import BaseClass
from simulation.simulation import Stage

class Machine(Stage,BaseClass):
    """
    defines the machine that an external job is run on. 
    We call the processing of an external job (i.e. allocating 
    resouces, preparation, and running) as a stage. 
    Each stage can (theoretically) be run on a different machine.
    E.g., post-processing can be doen locally.
    Therefore, the different stages are instances of machine 
    subclasses.
    """

    defaults_ = {
        "parallelization" : "none", # options: "none", "mpi", "gnu"
        "name" : "default"
        }

    def prepare_run_commands(self,batch): 
        if self.multi_sample and self.parallelization == "mpi": 
            self.to_mpi(batch)
        elif self.multi_sample and self.parallelization == "gnu": 
            self.to_gnu(batch)

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
            



from . import *

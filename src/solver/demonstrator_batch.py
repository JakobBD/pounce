import h5py
import numpy as np

from .solver import Solver,QoI
from helpers.printtools import *
from helpers.tools import *
from helpers import globels

class DemonstratorBatch(Solver):
    # TODO: Docstrings
    """ 
    Dummy python solver for testing.
    python source files are located in the externals directory
    I/O via HDF5. 
    """

    cname = "demonstrator_batch"

    defaults_ = {
        "solver_prms" : {}#, # parameters to be changed in every parameter filei to distinguish between levels/fidelities. Can be ModelName and/or nPoints.
        # "ModelName" : 'NODEFAULT',
        # "nPoints" : 0
        }


    class QoI(QoI):
        """ 
        Parent class for the dummy solver's QoI(s)
        """

        stages = {"all"}

        defaults_ = {
            "exe_path" : "dummy_unused"
            }

        internal = True

        def get_response(self):
            u_out = []
            for p in self.participants:
                u_tmp = p.get_response_from_hdf5()
                u_tmp = np.array([float(s) for s in u_tmp])
                u_out.append(u_tmp)
            return u_out


    def prepare(self):
        """ 
        Prepares the simulation by generating the run_command 
        and writing the HDF5 file containing all samples of the current 
        iteration and the current level.
        """

        p_print("Write HDF5 parameter file for simulation "+self.name)
        self.prm_file_name   = self.full_name+'_Input.h5'
        self.output_filename = self.full_name+'_Results.h5'

        prms = {a:b for a,b in self.solver_prms.items()}
        prms.update({"ProjectName" : self.full_name,
                     "nSamples" : self.samples.n,
                     "Samples" : self.samples.nodes,
                     "nParallelRuns" : self.n_parallel_runs})
               
        # Write to HDF5 input file
        with h5py.File(self.prm_file_name, 'w') as h5f:
            for name,prm in prms.items():
                if isinstance(prm,np.ndarray):
                    h5f.create_dataset(name, data=prm)
                else:
                    h5f.attrs[name]=prm

        self.run_commands = ['python3 '+self.exe_path+' '+self.prm_file_name]


    def get_response_from_hdf5(self):
        """ 
        Prepares the simulation by generating the run_command 
        and writing the HDF5 file containing all samples of the current 
        iteration and the current level.
        """

        with h5py.File(self.output_filename, 'r') as h5f:
            self.current_avg_work=h5f.attrs['WorkMean']
            u = np.array(h5f['Result'])
        return u


    def check_finished(self):
        """ 
        Check last lines of logfiles (stdout) for confirmation that 
        the batch is finished. Also retrieve average work, which is 
        written to the log file as well (as part of flexibatch)
        """
        for logfile in self.logfile_names: 
            with open(logfile,'r') as lf:
                assert "Minimal batch solver finished" in lf.read()
        return True





class Standard(DemonstratorBatch.QoI):

    cname = "standard"

    pass



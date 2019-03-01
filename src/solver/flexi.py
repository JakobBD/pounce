import h5py
import numpy as np
import subprocess
import glob

from .solver import Solver
from helpers.printtools import *

@Solver.register_subclass('flexi')
class Flexi(Solver):
    subclass_defaults={
            "prmfiles" : {"main_solver": "","iteration_postproc": ""}
        }

    def prepare_simulations(self,batches,stoch_vars):
        """ Prepares the simulation by generating the run_command
        and writing the HDF5 file containing all samples of the current iteration
        and the current samples.
        """
        for batch in batches:
            p_print("Write HDF5 parameter file for simulation "+batch.name)
            batch.project_name = self.project_name+'_'+batch.name
            batch.prm_file_name = 'input_'+batch.project_name+'.h5'
            self.write_hdf5(batch,stoch_vars)
            batch.run_command = self.exe_paths["main_solver"] + ' ' + batch.prm_file_name + ' ' + self.prmfiles["main_solver"]


    def write_hdf5(self,batch,stoch_vars):
        """ Writes the HDF5 file containing all necessary data for flexi run
        to run.
        """
        h5f = h5py.File(batch.prm_file_name, 'w')
        h5f.create_dataset('Samples', data=batch.samples.nodes)
        h5f.create_dataset('Weights', data=batch.samples.weights)
        h5f.attrs.create('StochVarNames', [var.name.ljust(255) for var in stoch_vars], (len(stoch_vars),), dtype='S255' )
        h5f.attrs.create('iOccurrence', [var.i_occurrence for var in stoch_vars], (len(stoch_vars),) )
        h5f.attrs.create('iArray', [var.i_pos for var in stoch_vars], (len(stoch_vars),) )
        h5f.attrs.create('ProjectName', self.project_name.ljust(255), dtype='S255')
        h5f.attrs.create('Distributions', [var._type for var in stoch_vars], (len(stoch_vars),), dtype='S255' )
        h5f.create_dataset('DistributionProps', data= [var.parameters for var in stoch_vars])
        h5f.attrs["nStochVars"] = len(stoch_vars)
        h5f.attrs["nGlobalRuns"] = batch.samples.n
        h5f.attrs["nPreviousRuns"] = batch.samples.n_previous
        h5f.attrs["nParallelRuns"] = batch.n_parallel_runs

        batch.solver_prms.update({"ProjectName":self.project_name+"_"+batch.name})
        dtypes=[( "Int",     int,     None,     lambda x:x),
                  ( "Str",     str,     "S255",  lambda x:x.ljust(255)),
                  ( "Real",    float,  None,     lambda x:x)]

        for         dtype_name,dtype_in,dtype_out,func in dtypes:
            names=[ key.ljust(255) for key, value in batch.solver_prms.items() if isinstance(value,dtype_in)]
            values=[ func(value) for value in batch.solver_prms.values() if isinstance(value,dtype_in)]
            n_vars=len(names)
            h5f.attrs["nLevelVars"+dtype_name]=n_vars
            h5f.attrs.create('LevelVarNames'+dtype_name, names,  shape=(n_vars,), dtype='S255' )
            h5f.attrs.create('LevelVars'+dtype_name,      values, shape=(n_vars,), dtype=dtype_out )

        h5f.close()

    def prepare_postproc(self,postproc_batches):
        """ Prepares the postprocessing by generating the run_postproc_command.
        """
        for postproc in postproc_batches:
            names=[p.name for p in postproc.participants]
            p_print("Generate postproc command for simulation(s) "+", ".join(names))
            postproc.run_command = self.exe_paths["iteration_postproc"] + " " + self.prmfiles["iteration_postproc"]
            # this is a rather ugly current flexi implementation
            postproc.project_name = postproc.participants[0].project_name
            postproc.output_filename = 'postproc_'+postproc.project_name+'_state.h5'
            for p in postproc.participants:
                filename=sorted(glob.glob(p.project_name+"_State_*.h5"))[-1]
                postproc.run_command=postproc.run_command+' '+filename

    def prepare_simu_postproc(self,simu_postproc):
        simu_postproc.args=[p.postproc.output_filename for p in simu_postproc.participants]
        simu_postproc.run_command=self.exe_paths["simulation_postproc"] + " " + " ".join(simu_postproc.args)

    def get_postproc_quantity_from_file(self,postproc,quantity_name):
        """ Readin sigma_sq or avg_walltime for MLMC.
        """
        h5f = h5py.File(postproc.output_filename, 'r')
        quantity = h5f.attrs[quantity_name]
        h5f.close()
        return quantity

    def get_work_mean(self,postproc):
        return sum(p.current_avg_work for p in postproc.participants)

    def check_finished(self,batch):
        #TODO: some more checks, e.g. empty stderr
        try:
            args=['tail','-n','3',batch.logfile_name]
            output=subprocess.run(args,stdout=subprocess.PIPE)
            output=output.stdout.decode("utf-8").splitlines()
            batch.current_avg_work=float(output[2])
            return output[0]=="FLEXIBATCH FINISHED"
        except:
            return False


# class QoIState():
    # pass

# QoIs={"state":QoIState}

import h5py
import numpy as np
import subprocess
import glob

from .solver import Solver
from helpers.printtools import *

@Solver.register_subclass('flexi')
class Flexi(Solver):
    subclass_defaults={
            "prmfiles" : {"main_solver": "","iteration_postproc": ""}#,
            # "QoIs" : ["state"],
            # "QoI_optimize" : "state"
        }

    def prepare_simulations(self,batches,stoch_vars):
        """ Prepares the simulation by generating the run_command
        and writing the HDF5 file containing all samples of the current iteration
        and the current samples.
        """
        for batch in batches:
            p_print("Write HDF5 parameter file for simulation "+batch.name)
            batch.project_name = self.project_name+'_'+batch.name
            self.write_hdf5(batch,stoch_vars)

            batch.prm_file_name = 'input_'+batch.project_name+'.h5'
            batch.run_command = self.exe_paths["main_solver"] + ' ' + batch.prm_file_name + ' ' + self.prmfiles["main_solver"]


    def write_hdf5(self,batch,stoch_vars):
        """ Writes the HDF5 file containing all necessary data for flexi run
        to run.
        """
        prms= {'Samples'          : batch.samples.nodes,
               'Weights'          : batch.samples.weights,
               'StochVarNames'    : stoch_vars.name,
               'iOccurrence'      : stoch_vars.i_occurrence,
               'iArray'           : stoch_vars.i_pos,
               'Distributions'    : stoch_vars._type,
               'DistributionProps': stoch_vars.parameters,
               "nStochVars"       : len(stoch_vars),
               "nGlobalRuns"      : batch.samples.n,
               "nPreviousRuns"    : batch.samples.n_previous,
               "nParallelRuns"    : batch.n_parallel_runs
               }

        h5f = h5py.File(batch.prm_file_name, 'w')
        for name,prm in prms.items():
            self.h5write(h5f,name,prm)

        batch.solver_prms.update({"ProjectName":self.project_name+"_"+batch.name})
        dtypes=[("Int", int), ("Str", str), ("Real", float)]

        for suffix,type_in in dtypes:
            names=[ key for key, value in batch.solver_prms.items() if isinstance(value,type_in)]
            values=[ value for value in batch.solver_prms.values() if isinstance(value,type_in)]
            n_vars=len(names)
            self.h5write(h5f,'nLevelVars'   +suffix,n_vars)
            self.h5write(h5f,'LevelVarNames'+suffix,names)
            self.h5write(h5f,'LevelVars'    +suffix,values)

        h5f.close()


    def h5write(self,h5f,name,prm):
        if isinstance(prm,np.ndarray):
            h5f.create_dataset(name, data=prm)
        elif isinstance(prm,list):
            if len(prm) == 0:
                h5f.attrs.create(name, prm)
            elif isinstance(prm[0],list):
                h5f.create_dataset(name, data=np.array(prm))
            elif isinstance(prm[0],str):
                h5f.attrs.create(name, [e.ljust(255) for e in prm], (len(prm),), dtype='S255' )
            else:
                h5f.attrs.create(name, prm, (len(prm),))
        elif isinstance(prm,str):
            h5f.attrs.create(name, prm.ljust(255), dtype='S255')
        else:
            h5f.attrs[name] = prm


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

# class QoIRecordPoints():
    # pass

# QoIs={"state":QoIState,
      # "rp":QoIRecordPoints}

import h5py
import numpy as np

from .solver import Solver,QoI
from helpers.printtools import *

@Solver.register_subclass('internal')
class Internal(Solver):
    subclass_defaults={
        }

    def prepare_simulations(self,batches,stoch_vars):
        """ Prepares the simulation by generating the run_command 
        and writing the HDF5 file containing all samples of the current iteration
        and the current level.
        """
        for batch in batches:
            p_print("Write HDF5 parameter file for simulation "+batch.name)
            batch.project_name = self.project_name+'_'+batch.name
            batch.prm_file_name = 'input_'+batch.project_name+'.h5'
            self.write_hdf5(batch,stoch_vars)
            batch.run_command='python3 '+self.exe_path + ' '+batch.prm_file_name

    def write_hdf5(self,batch,stoch_vars):
        """ Writes the HDF5 file containing all necessary data for the internal 
        to run.
        """
        h5f = h5py.File(batch.prm_file_name, 'w')
        h5f.create_dataset('Samples', data=batch.samples.nodes)
        h5f.create_dataset('Weights', data=batch.samples.weights)
        h5f.attrs["nPrevious"] = batch.samples.n_previous
        h5f.attrs["ProjectName"] = batch.project_name
        for key, value in batch.solver_prms.items():
            h5f.attrs[key] = value
        h5f.close()

    def prepare_postproc(self,qois):
        """ Prepares the postprocessing by generating the run_postproc_command.
        """
        for qoi in qois: 
            p_print("Generate postproc command for "+qoi.name+" "+qoi._type)
            names=[p.name for p in qoi.participants]
            p_print("  Participants: "+", ".join(names))
            qoi.prepare()

    def prepare_simu_postproc(self,qois):
        for i,qoi in enumerate(qois):
            qoi.args=[p.qois[i].output_filename for p in qoi.participants]
            qoi.run_command="python3 " + qoi.exe_paths["simulation_postproc"] + " " + " ".join(qoi.args)

    def get_work_mean(self,qoi):
        return self.get_postproc_quantity_from_file(qoi,"WorkMean")

    def get_postproc_quantity_from_file(self,qoi,quantity_name):
        """ Readin sigma_sq for MLMC.
        """
        h5f = h5py.File(qoi.output_filename, 'r')
        quantity = h5f.attrs[quantity_name]
        h5f.close()
        return quantity

    def check_finished(self,batch):
        return True


@QoI.register_subclass('internal_integral')
class Integral(QoI):

    def prepare(self):
        self.run_command = "python3 "+self.exe_paths["iteration_postproc"]
        # this is a rather ugly current implementation
        self.project_name = self.participants[0].project_name
        self.output_filename = 'postproc_'+self.project_name+'_integral.h5'
        for p in self.participants:
            filename=p.project_name+"_State.h5"
            self.run_command=self.run_command+' '+filename


from .solver import Solver
import h5py
import numpy as np
from helpers.printtools import *

@Solver.register_subclass('internal')
class SolverInternal(Solver):
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
         batch.run_command='python3 '+self.exe_paths["main_solver"] + ' '+batch.prm_file_name

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

   def prepare_postproc(self,postproc_batches):
      """ Prepares the postprocessing by generating the run_postproc_command.
      """
      for postproc in postproc_batches: 
         names=[p.name for p in postproc.participants]
         p_print("Generate postproc command for simulation(s) "+", ".join(names))
         postproc.run_command = "python3 "+self.exe_paths["iteration_postproc"]
         # this is a rather ugly current implementation
         postproc.project_name = postproc.participants[0].project_name
         for p in postproc.participants:
            postproc.run_command=postproc.run_command+' '+p.project_name+"_State.h5"

   def get_work_mean(self,postproc):
      return self.get_postproc_quantity_from_file(postproc,"WorkMean")

   def get_postproc_quantity_from_file(self,postproc,quantity_name):
      """ Readin sigma_sq for MLMC.
      """
      h5_file_name = 'sums_'+postproc.participants[0].project_name+'.h5'
      h5f = h5py.File(h5_file_name, 'r')
      quantity = h5f.attrs[quantity_name]
      h5f.close()
      return quantity

   def check_finished(self,postproc):
      return True

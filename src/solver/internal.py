import h5py
import numpy as np

from .solver import Solver,QoI
from helpers.printtools import *
from helpers.tools import *

@Solver.register_subclass('internal')
class Internal(Solver):
    subclass_defaults={
        }

    def prepare_simulations(self,batches,uqmethod,simulation):
        """ Prepares the simulation by generating the run_command 
        and writing the HDF5 file containing all samples of the current 
        iteration and the current level.
        """
        for batch in batches:
            p_print("Write HDF5 parameter file for simulation "+batch.name)
            batch.project_name = simulation.project_name+'_'+batch.name
            batch.prm_file_name = 'input_'+batch.project_name+'.h5'
            prms={"Samples"    :batch.samples.nodes,
                  "ProjectName":batch.project_name}
            prms.update(uqmethod.prm_dict_add(batch))
            prms.update(batch.solver_prms)

            self.write_hdf5(batch.prm_file_name,prms)

            batch.run_command='python3 '+self.exe_path+' '+batch.prm_file_name

    def write_hdf5(self,file_name,prms):
        """ Writes the HDF5 file containing all necessary data for the 
        internal to run.
        """

        h5f = h5py.File(file_name, 'w')
        for name,prm in prms.items():
            self.h5write(h5f,name,prm)
        h5f.close()

    def h5write(self,h5f,name,prm):
        if isinstance(prm,np.ndarray):
            h5f.create_dataset(name, data=prm)
        else:
            h5f.attrs[name]=prm

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


@QoI.register_subclass('internal','integral')
class Integral(QoI):

    def prepare_iter_postproc(self,simulation):
        self.run_command = "python3 "+self.exe_paths["iteration_postproc"]
        # participants[0] is a rather dirty hack
        self.prm_file_name = self.participants[0].prm_file_name
        self.run_command += " " + self.prm_file_name 
        self.project_name  = self.participants[0].project_name
        self.output_filename = 'postproc_'+self.project_name+'_integral.h5'
        for p in self.participants:
            filename=p.project_name+"_State.h5"
            self.run_command += ' ' + filename

    def prepare_simu_postproc(self,simulation):
        self.args=[p.output_filename for p in self.participants]
        self.run_command="python3 " + self.exe_paths["simulation_postproc"] \
                        + " " + " ".join(self.args)

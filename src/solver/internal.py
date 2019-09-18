import h5py
import numpy as np

from .solver import Solver,QoI
from helpers.printtools import *
from helpers.tools import *
from helpers import globels

class Internal(Solver):

    defaults_ = {
        "solver_prms" : {
            "nPoints" : "NODEFAULT"
            }
        }

    class QoI(QoI):

        def get_work_mean(self):
            return self.get_derived_quantity("WorkMean")

        def get_derived_quantity(self,quantity_name):
            """ Readin sigma_sq for MLMC.
            """
            with h5py.File(self.output_filename, 'r') as h5f:
                quantity = h5f.attrs[quantity_name]
            return quantity


    def prepare(self,uq_method):
        """ Prepares the simulation by generating the run_command 
        and writing the HDF5 file containing all samples of the current 
        iteration and the current level.
        """
        p_print("Write HDF5 parameter file for simulation "+self.name)
        self.project_name = globels.project_name+'_'+self.name
        self.prm_file_name = 'input_'+self.project_name+'.h5'
        prms={"Samples"    :self.samples.nodes,
              "ProjectName":self.project_name}
        prms.update(uq_method.prm_dict_add(self))
        prms.update(self.solver_prms)

        self.write_hdf5(self.prm_file_name,prms)

        self.run_command='python3 '+self.exe_path+' '+self.prm_file_name

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




class Integral(Internal.QoI):

    def prepare_iteration_postproc(self,uq_method):
        self.run_command = "python3 "+self.exe_path
        # participants[0] is a rather dirty hack
        self.prm_file_name = self.participants[0].prm_file_name
        self.run_command += " " + self.prm_file_name 
        self.project_name  = self.participants[0].project_name
        self.output_filename = 'postproc_'+self.project_name+'_integral.h5'
        for p in self.participants:
            filename=p.project_name+"_State.h5"
            self.run_command += ' ' + filename

    def prepare_simulation_postproc(self,uq_method):
        self.args=[p.output_filename for p in self.participants]
        self.run_command="python3 " + self.exe_path \
                        + " " + " ".join(self.args)


            

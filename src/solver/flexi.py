import h5py
import numpy as np
import subprocess
import glob

from .solver import Solver,QoI
from helpers.printtools import *
from helpers.tools import *

@Solver.register_subclass('flexi')
class Flexi(Solver):
    subclass_defaults={
            "prmfile" : "parameter_flexi.ini"
        }

    def prepare_simulations(self,batches,uqmethod,simulation):
        """ Prepares the simulation by generating the run_command
        and writing the HDF5 file containing all samples of the current
        iteration and the current samples.
        """
        for batch in batches:
            p_print("Write HDF5 parameter file for simulation "+batch.name)
            batch.project_name = simulation.project_name+'_'+batch.name
            batch.prm_file_name = 'input_'+batch.project_name+'.h5'
            batch.solver_prms.update({"ProjectName":batch.project_name})

            # both:
            stv=uqmethod.stoch_vars
            prms= {'Samples'          : batch.samples.nodes,
                   'StochVarNames'    : [s.name         for s in stv],
                   'iOccurrence'      : [s.i_occurrence for s in stv],
                   'iArray'           : [s.i_pos        for s in stv],
                   "nStochVars"       : len(stv),
                   "nGlobalRuns"      : batch.samples.n,
                   "nParallelRuns"    : batch.n_parallel_runs
                   }
            prms.update(uqmethod.prm_dict_add(batch))

            self.write_hdf5(batch.prm_file_name,batch.solver_prms,prms)

            batch.run_command = self.exe_path + ' ' \
                                + batch.prm_file_name + ' ' + self.prmfile


    def write_hdf5(self,file_name,solver_prms,further_prms):
        """ Writes the HDF5 file containing all necessary data for
        flexi run to run.
        """

        h5f = h5py.File(file_name, 'w')
        for name,prm in further_prms.items():
            self.h5write(h5f,name,prm)

        dtypes=[("Int", int), ("Str", str), ("Real", float)]

        for suffix,dtype in dtypes:
            names=[key for key, value in solver_prms.items() \
                   if isinstance(value,dtype)]
            values=[value for value in solver_prms.values() \
                    if isinstance(value,dtype)]
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
                h5f.attrs.create(name, [e.ljust(255) for e in prm],
                                 (len(prm),), dtype='S255' )
            else:
                h5f.attrs.create(name, prm, (len(prm),))
        elif isinstance(prm,str):
            h5f.attrs.create(name, prm.ljust(255), dtype='S255')
        else:
            h5f.attrs[name] = prm


    def get_postproc_quantity_from_file(self,qoi,quantity_name):
        """ Readin sigma_sq or avg_walltime for MLMC.
        """
        h5f = h5py.File(qoi.output_filename, 'r')
        quantity = h5f.attrs[quantity_name]
        h5f.close()
        return quantity

    def get_work_mean(self,qoi):
        return sum(p.current_avg_work for p in qoi.participants)

    def check_finished(self,batch):
        #TODO: some more checks, e.g. empty stderr
        try:
            args=['tail','-n','4',batch.logfile_name]
            output=subprocess.run(args,stdout=subprocess.PIPE)
            output=output.stdout.decode("utf-8").splitlines()
            index=output.index("FLEXIBATCH FINISHED")
            batch.current_avg_work=float(output[index+2])
            return True
        except:
            return False


@QoI.register_subclass('flexi','fieldsolution')
class FieldSolution(QoI):

    subclass_defaults={"prmfiles": {"iteration_postproc": "",
                                    "simulation_postproc":""}
            }

    def prepare_iter_postproc(self,simulation):
        # participants[0] is a rather dirty hack
        self.prm_file_name = self.participants[0].prm_file_name
        self.run_command = self.exe_paths["iteration_postproc"] \
                           + " " + self.prmfiles["iteration_postproc"] \
                           + " " + self.prm_file_name
        self.project_name  = self.participants[0].project_name
        self.output_filename = 'postproc_'+self.project_name+'_state.h5'
        for p in self.participants:
            filename=sorted(glob.glob(p.project_name+"_State_*.h5"))[-1]
            self.run_command += " " + filename

    def prepare_simu_postproc(self,simulation):
        self.args=[p.output_filename for p in self.participants]
        self.run_command = self.exe_paths["simulation_postproc"] \
                          + " " + " ".join(self.args)
        self.project_name  = simulation.project_name+'_'+self.name
        self.output_filename = 'SOLUTION_'+self.project_name+'_state.h5'


@QoI.register_subclass('flexi','recordpoints')
class RecordPoints(QoI):

    subclass_defaults={"prmfiles": {"iteration_postproc": "",
                                    "simulation_postproc":""},
                       "time_span": [0.,1.E10]
            }

    def prepare_iter_postproc(self,simulation):
        # participants[0] is a rather dirty hack
        self.prm_file_name = self.participants[0].prm_file_name
        filenames=sorted(glob.glob(self.participants[0].project_name+"_RP_*.h5"))
        n_files = 0
        for fn in filenames:
            time=float(fn.split("_")[-1][:-3])
            if self.time_span[0] <= time <= self.time_span[1]:
                n_files += 1
        self.run_command = self.exe_paths["iteration_postproc"] \
                           + " " + self.prmfiles["iteration_postproc"] \
                           + " " + self.prm_file_name \
                           + " " + str(n_files)
        self.project_name = self.participants[0].project_name
        self.output_filename = 'postproc_'+self.project_name+'_recordpoints.h5'
        for p in self.participants:
            filenames=sorted(glob.glob(p.project_name+"_RP_*.h5"))
            fn_add=[]
            for fn in filenames:
                time=float(fn.split("_")[-1][:-3])
                if self.time_span[0] <= time <= self.time_span[1]:
                    self.run_command += " "+fn

    def prepare_simu_postproc(self,simulation):
        self.args=[p.output_filename for p in self.participants]
        self.run_command = self.exe_paths["simulation_postproc"] \
                          + " " + self.prmfiles["iteration_postproc"] \
                          + " " + " ".join(self.args)
        self.project_name  = simulation.project_name+'_'+self.name
        self.output_filename = 'SOLUTION_'+self.project_name+'_state.h5'

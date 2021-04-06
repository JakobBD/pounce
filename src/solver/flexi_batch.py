import h5py
import numpy as np
import subprocess
import glob

from .solver import Solver,QoI
from .cfdfv import Cfdfv
from .internal import Internal
from helpers.printtools import *
from helpers.tools import *
from helpers import globels

class FlexiBatch(Solver):
    """ 
    Runs with the POUNCE-adaptation of FLEXI, i.e. with the 
    executable flexibatch and the according post-processing tools.
    """

    cname = "flexi_batch"

    defaults_ = {
        "prmfile" : "parameter_flexi.ini",
        "solver_prms" : {
            "N" : "NODEFAULT",
            "MeshFile" : "NODEFAULT"
            }
        }

    defaults_add = { 
        "StochVar": {
            'i_occurrence': 1,
            'i_pos': 1,
            'name' : 'NODEFAULT'
            }
        }

    class QoI(QoI):
        """ 
        Parent class for all FLEXI QoI's 
        """

        defaults_ = {
            "prmfile" : ""
            }

        def get_derived_quantity(self,quantity_name):
            """ 
            Readin sigma_sq or avg_walltime for MLMC.
            """
            with h5py.File(self.output_filename, 'r') as h5f:
                quantity = h5f.attrs[quantity_name]
            return quantity

        def get_current_work_mean(self):
            """ 
            For FlexiBatch, avg work is already read from HDF5 file during 
            check_all_finished
            """
            return sum(p.current_avg_work for p in self.participants)


    def prepare(self):
        """ 
        Prepares the simulation by generating the run_command
        and writing the HDF5 file containing all samples of the current
        iteration and the current samples.
        """

        p_print("Write HDF5 parameter file for simulation "+self.name)
        self.project_name = globels.project_name+'_'+self.name
        self.prm_file_name = 'input_'+self.project_name+'.h5'
        self.solver_prms.update({"ProjectName":self.project_name})

        # both:
        stv=self.samples.stoch_vars
        prms= {'Samples'          : self.samples.nodes,
               'StochVarNames'    : [s.name         for s in stv],
               'iOccurrence'      : [s.i_occurrence for s in stv],
               'iArray'           : [s.i_pos        for s in stv],
               "nStochVars"       : len(stv),
               "nGlobalRuns"      : self.samples.n,
               "nParallelRuns"    : self.n_parallel_runs
               }

        self.write_hdf5(self.prm_file_name,self.solver_prms,prms)

        self.run_commands = [self.exe_path + ' ' \
                             + self.prm_file_name + ' ' + self.prmfile]


    def write_hdf5(self,file_name,solver_prms,further_prms):
        """ 
        Writes the HDF5 file containing all necessary data for
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
        """ 
        helper function for correct data formatting 
        in Fortran readable HDF5 files. 
        """
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

    def get_qty_from_stdout(self,name): 
        """
        dirty: gets info not from stdout, but from h5 file
        TODO: rename 
        """
        filename=sorted(glob.glob(self.project_name+"_BodyForces_*.h5"))[-1]
        with h5py.File(filename, 'r') as h5f:
                dset = h5f['BodyForces_BC_wall'][()]
        vals=np.array(dset)
        return vals[:,name]

    def check_finished(self):
        """ 
        Check last lines of logfiles (stdout) for confirmation that 
        the batch is finished. Also retrieve average work, which is 
        written to the log file as well (as part of flexibatch)
        """
        try:
            for logfile in self.logfile_names: 
                args=['tail','-n','4',logfile]
                output=subprocess.run(args,stdout=subprocess.PIPE)
                output=output.stdout.decode("utf-8").splitlines()
                index=output.index("FLEXIBATCH FINISHED")
                self.current_avg_work=float(output[index+2])
            return True
        except:
            return False


class FlexiBatchClBatch(Cfdfv.QoI,FlexiBatch.QoI):
    """ 
    first parent is dominant, second adds it to their subclasses dict
    """

    cname = "cl_batch"

    stages = {"all"}

    defaults_ = {
        "prmfile": "dummy_unused"
        }

    # this is dirty: index of BodyForce
    string_in_stdout = 1 


class FlexiBatchCp(Internal.QoI,FlexiBatch.QoI):
    """ 
    first parent is dominant, second adds it to their subclasses dict
    """

    cname = "cp"

    stages = {"all"}

    defaults_ = {
        "exe_path" : "NODEFAULT",
        "prmfile": "dummy_unused",
        "do_write" : True,
        "refstate" : "NODEFAULT"
        }

    def get_response(self,s=None): 
        u_out = []
        for p in self.participants:
            statefilename=sorted(glob.glob(p.project_name+"_State_*.h5"))[-1]
            run_command = self.exe_path + " " + statefilename
            # TODO: very dirty still...
            with open("dummy_log_file",'w+') as f:
                subprocess.run(run_command,stdout=f,shell=True)
            with h5py.File(statefilename, 'r') as h5f:
                    dset = h5f['SwimCP'][()]
            pres =np.array(dset)
            u_inf = np.array(self.refstate)
            cp = (pres-u_inf[4])/(0.5*u_inf[0]*np.sum(u_inf[1:4]**2))
            u_out.append(cp)
        return u_out

    def write_to_file(self): 
        if self.do_write: 
            self.outfilename = "output_" + self.cname + ".csv"
            with open(self.outfilename,"w") as f: 
                f.write("mean stddev")
                for x, y in zip(self.mean,self.stddev): 
                    f.write("\n"+str(x)+" "+str(y))

    def integrate(self,qty): 
        return np.mean(qty)


class FlexiBatchFieldSolution(FlexiBatch.QoI):
    """ 
    Takes the whole field solution as quantity of interest. 

    Caution: routines starting with prepare_... 
    will be renamed to "prepare" as part of the create_by_stage
    routine. 
    """

    cname = "field_solution"

    stages = set()


class FlexiBatchFieldSolutionIterPostProc(FlexiBatchFieldSolution):

    stages = {"iteration_postproc"}

    def prepare(self):
        # participants[0] is a rather dirty hack
        self.prm_file_name = self.participants[0].prm_file_name
        run_command = self.exe_path \
                      + " " + self.prmfile \
                      + " " + self.prm_file_name
        self.project_name  = self.participants[0].project_name
        self.output_filename = 'postproc_'+self.project_name+'_state.h5'
        for p in self.participants:
            filename=sorted(glob.glob(p.project_name+"_State_*.h5"))[-1]
            run_command += " " + filename
        self.run_commands = [run_command]

class FlexiBatchFieldSolutionSimuPostProc(FlexiBatchFieldSolution):

    stages = {"simulation_postproc"}

    def prepare(self):
        self.args=[p.output_filename for p in self.participants]
        self.run_commands = [self.exe_path \
                            + " " + " ".join(self.args)]
        self.project_name  = globels.project_name+'_'+self.name
        self.output_filename = 'SOLUTION_'+self.project_name+'_state.h5'


class FlexiBatchRecordPoints(FlexiBatch.QoI):
    """ 
    Takes a solution time sereis evaluated at record points as QoI.

    Caution: routines starting with prepare_... 
    will be renamed to "prepare" as part of the create_by_stage
    routine. 
    """

    cname = "record_points"

    stages = set()

    defaults_ = { # TODO: move to IterPostProc
        "time_span": [0.,1.E10]
        }

class FlexiBatchRecordPointsIterPostProc(FlexiBatchRecordPoints):

    stages = {"iteration_postproc"}

    def prepare(self):
        # participants[0] is a rather dirty hack
        self.prm_file_name = self.participants[0].prm_file_name
        n_files = len(glob.glob(participants[0].project_name+"_RP_*.h5"))
        run_command = self.exe_path \
                      + " " + self.prmfile \
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
                    run_command += " "+fn
        self.run_commands = [run_command]


class FlexiBatchRecordPointsSimuPostProc(FlexiBatchRecordPoints):

    stages = {"simulation_postproc"}

    def prepare(self):
        self.args=[p.output_filename for p in self.participants]
        self.run_commands = [self.exe_path \
                            + " " + " ".join(self.args)]
        self.project_name  = globels.project_name+'_'+self.name
        self.output_filename = 'SOLUTION_'+self.project_name+'_state.h5'

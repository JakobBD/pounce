import h5py
import numpy as np
import subprocess
import glob

from .solver import Solver,QoI
from helpers.printtools import *
from helpers.tools import *
from helpers import globels

class Cfdfv(Solver):
    """ 
    Runs with the POUNCE-adaptation of FLEXI, i.e. with the 
    executable flexibatch and the according post-processing tools.
    """

    defaults_ = {
        "prmfile" : "parameter_cfdfv.ini",
        "solver_prms" : {
            "MeshFile" : "NODEFAULT"
            }
        }

    defaults_add = { 
        "StochVar": {
            'i_occurrence': [],
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

        def __init__(self,*args,**kwargs): 
            super().__init__(*args,**kwargs)
            self.internal = True


        def get_response(self,s=None): 
            if not s: 
                s = self.string_in_stdout
            u_fine = self.participants[0].get_qty_from_stdout(s)
            if len(self.participants)>1: 
                u_coarse = self.participants[1].get_qty_from_stdout(s)
            else: 
                u_coarse = 0. * u_fine
            return u_fine, u_coarse

        def get_derived_quantity(self,quantity_name):
            """ 
            Readin sigma_sq or avg_walltime for MLMC.
            """
            qty = get_attr(self,quantity_name,None)
            if qty: 
                return qty
            else: 
                raise Exception("Quantity " + quantity_name + " not found!")

        def get_work_mean(self):
            """ 
            For Flexi, avg work is already read from HDF5 file during 
            check_all_finished
            """
            return sum(p.current_avg_work for p in self.participants)


    def replace_prm(self,prmfile):
        #TODO


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
        prms.update(self.samples.sampling_prms())

        self.write_hdf5(self.prm_file_name,self.solver_prms,prms)

        self.run_commands = [self.exe_path + ' ' \
                             + self.prm_file_name + ' ' + self.prmfile]

    def get_qty_from_stdout(self,name): 
        vals = []
        for logfile in self.logfile_names: 
            args=['tail','-n','20',logfile]
            output=subprocess.run(args,stdout=subprocess.PIPE)
            output=output.stdout.decode("utf-8").splitlines()
            found = False
            for line in reversed(output): 
                #TODO
                v = re.match(r"\s*"+name+"\s*:(.+)",line,)
                if v: 
                    vals.append(v.group(1))
                    print(vals[-1])
                    found = True
                    break
            if not found: 
                raise Exception("Value " + name + " not found in stdout!")

    def check_finished(self):
        """ 
        Check last lines of logfiles (stdout) for confirmation that 
        the batch is finished. Also retrieve average work, which is 
        written to the log file as well (as part of flexibatch)
        """
        try:
            arr = self.get_qty_from_stdout("Computation Time"): 
            # remove "s" in the end
            t_sum = sum(float(item[:-2]) for item in arr)
            self.current_avg_work=t_sum / self.samples.n
            return True
        except:
            return False




class CL(Cfdfv.QoI):

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.string_in_stdout = "cl"


class CD(Cfdfv.QoI):

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.string_in_stdout = "cd"

import h5py
import numpy as np
import subprocess
import glob
import re
import configparser

from .solver import Solver,QoI
from helpers.printtools import *
from helpers.tools import *
from helpers import globels

class DemonstratorSingle(Solver):
    """ 
    Runs with the POUNCE-adaptation of FLEXI, i.e. with the 
    executable flexibatch and the according post-processing tools.
    """

    cname = "demonstrator_single"

    stages = {"main"}

    defaults_ = {
        "prmfile" : "parameter.ini",
        "solver_prms" : {}#, # parameters to be changed in every parameter filei to distinguish between levels/fidelities. Can be ModelName and/or nPoints.
        # "ModelName" : 'NODEFAULT',
        # "nPoints" : 0
        }

    defaults_add = { 
        "StochVar": {
            'name' : 'StochPrm'
            }
        }

    class QoI(QoI):
        """ 
        Parent class for QoI's of this solver
        """

        stages = {"all"}

        defaults_ = {
            "exe_path" : "dummy_unused"
            }

        internal = True


        def get_response(self,s=None): 
            if not s: 
                s = self.string_in_stdout
            u_out = []
            for p in self.participants:
                u_tmp = p.get_qty_from_stdout(s)
                u_tmp = np.array([float(s) for s in u_tmp])
                u_out.append(u_tmp)
            return u_out

        def get_derived_quantity(self,quantity_name):
            """ 
            Readin sigma_sq or avg_walltime for MLMC.
            """
            qty = getattr(self,quantity_name,"not found")
            if qty == "not found": 
                raise Exception("Quantity " + quantity_name + " not found!")
            else: 
                return qty


    def prepare(self):
        """ 
        Prepares the simulation by generating the run_command
        and writing the HDF5 file containing all samples of the current
        iteration and the current samples.
        """

        # read input file
        prms = configparser.ConfigParser()
        with open(self.prmfile,'r') as stream:
            prms.read_string("[DEFAULT]\n" + stream.read())

        for key,value in self.solver_prms.items():
            prms["DEFAULT"][key] = str(value)

        self.run_commands = []
        self.prmfiles = []
        for i_sample in range(self.samples.n): 
            try: 
                i_sample_glob = i_sample + self.samples.n_previous + 1
            except AttributeError:
                i_sample_glob = i_sample + 1
            sample_str = '_'+self.name+'_s'+str(i_sample_glob)
            for i_var,s in enumerate(self.samples.stoch_vars): 
                assert s.name in prms["DEFAULT"]
                prms["DEFAULT"][s.name] = str(self.samples.nodes[i_sample,i_var])
            prms["DEFAULT"]['ProjectName'] = globels.project_name + sample_str
            
            prmfile = 'parameter'+sample_str+'.ini'
            with open(prmfile,'w') as pf: 
                prms.write(pf)
            self.prmfiles.append(prmfile)

            self.run_commands.append('python3 ' + self.exe_path + ' ' + prmfile)


    def get_qty_from_stdout(self,name): 
        vals = []
        for logfile in self.logfile_names: 
            with open(logfile,'r') as lf:
                output = lf.read().split("===OUTPUT===")[1:]
            for run in output:
                found = False
                for line in reversed(run.splitlines()): 
                    v = re.match(r"\s*"+name+r"\s*:(.+)",line)
                    if v: 
                        vals.append(v.group(1))
                        found = True
                        break
                if not found: 
                    raise Exception("Value " + name + " not found in stdout!")
        return vals

    def check_finished(self):
        """ 
        Check last lines of logfiles (stdout) for confirmation that 
        the batch is finished. Also retrieve average work, which is 
        written to the log file as well (as part of flexibatch)
        """
        arr = self.get_qty_from_stdout("Computation Time")
        self.current_avg_work = sum(float(i) for i in arr) / self.samples.n
        return True



class Standard(DemonstratorSingle.QoI):

    cname = "standard"

    string_in_stdout = "Result"



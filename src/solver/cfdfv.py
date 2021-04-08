import h5py
import numpy as np
import subprocess
import glob
import copy
import re

from .solver import Solver,QoI
from helpers.printtools import *
from helpers.tools import *
from helpers import globels

class Cfdfv(Solver):
    """ 
    Runs with the POUNCE-adaptation of FLEXI, i.e. with the 
    executable flexibatch and the according post-processing tools.
    """

    cname = "cfdfv"

    defaults_ = {
        "prmfile" : "parameter_cfdfv.ini",
        "solver_prms" : {
            "MeshFile" : "NODEFAULT"
            }
        }

    defaults_add = { 
        "StochVar": {
            'i_occurrence': [1],
            'name' : 'NODEFAULT'
            }
        }

    class QoI(QoI):
        """ 
        Parent class for all FLEXI QoI's 
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

        def get_current_work_mean(self):
            """ 
            For Flexi, avg work is already read from HDF5 file during 
            check_all_finished
            """
            return sum(p.current_avg_work for p in self.participants)

    def find_ind(self,lines,name,i_occurrence=[1]):
            i_found = 0
            ii = 0
            int_out=[]
            for i,l in enumerate(lines): 
                if l.split("=")[0].strip() == name: 
                    i_found += 1
                    if i_found == i_occurrence[ii]: 
                        int_out.append(i)
                        ii+=1
                        if ii == len(i_occurrence):
                            break
            if ii < len(i_occurrence):
                raise Exception("parameter "+name+" not found enough times in prm file")
            return int_out

    def prepare(self):
        """ 
        Prepares the simulation by generating the run_command
        and writing the HDF5 file containing all samples of the current
        iteration and the current samples.
        """

        self.project_name = globels.project_name+'_'+self.name
        with open(self.prmfile,'r') as pf: 
            orig = pf.readlines()
        new = copy.deepcopy(orig)

        for key,value in self.solver_prms.items():
            ind=self.find_ind(orig,key)[0]
            new[ind] = key + " = " + value + "\n"

        for s in self.samples.stoch_vars: 
            s.line_ind = self.find_ind(orig,s.name,s.i_occurrence)
        fn_ind = self.find_ind(orig,"FileName")[0]

        self.run_commands = []
        self.prmfiles = []
        for i_sample in range(self.samples.n): 
            i_sample_glob = i_sample + self.samples.n_previous + 1
            sample_str = '_'+self.name+'_s'+str(i_sample_glob)
            for i_var,s in enumerate(self.samples.stoch_vars): 
                for ind in s.line_ind: 
                    new[ind] = s.name + " = " + str(self.samples.nodes[i_sample,i_var]) + "\n"
            new[fn_ind] = "FileName = " + globels.project_name + sample_str + "\n"
            
            prmfile = 'parameter'+sample_str+'.ini'
            with open(prmfile,'w') as pf: 
                pf.writelines(new)
            self.prmfiles.append(prmfile)

            self.run_commands.append(self.exe_path + ' ' + prmfile)

    def get_qty_from_stdout(self,name): 
        vals = []
        for logfile in self.logfile_names: 
            args=['tail','-n','20',logfile]
            output=subprocess.run(args,stdout=subprocess.PIPE)
            output=output.stdout.decode("utf-8").splitlines()
            found = False
            for line in reversed(output): 
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
        # try:

        arr = self.get_qty_from_stdout("Computation Time")
        # remove "s" in the end
        t_sum = sum(float(item[:-2]) for item in arr)
        self.current_avg_work=t_sum / self.samples.n
        return True
        # except:
            # return False



class Cfdfv2(Cfdfv): 

    cname = "cfdfv2"
    stage = "2"

    def prepare(self):
        print("hello")
        super().__init(self)



class CfdfvCl(Cfdfv.QoI):

    cname = "cl"

    string_in_stdout = "cl"


class CfdfvCd(Cfdfv.QoI):

    cname = "cd"

    string_in_stdout = "cd"

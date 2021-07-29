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

class Ice(Solver):
    """ 
    Runs with the POUNCE-adaptation of FLEXI, i.e. with the 
    executable flexibatch and the according post-processing tools.
    """

    cname = "ice"
    stages = {"main"}

    defaults_ = {
        "prmfile" : "parameter_flexi.ini",
        "mesh_dir" : "mesh",
        "A_q_ref" : "NODEFAULT",
        "solver_prms" : {
            "N" : "NODEFAULT"
            }
        }

    class QoI(QoI):
        """ 
        Parent class for all FLEXI QoI's 
        """

        defaults_ = {
            "exe_path": "dummy_unused"
            }

        def get_derived_quantity(self,quantity_name):
            """ 
            Readin sigma_sq or avg_walltime for MLMC.
            """
            with h5py.File(self.output_filename, 'r') as h5f:
                quantity = h5f.attrs[quantity_name]
            return quantity

    def prepare(self):
        """ 
        Prepares the simulation by generating the run_command
        and writing the HDF5 file containing all samples of the current
        iteration and the current samples.
        """

        p_print("Write HDF5 parameter file for simulation "+self.name)
        self.sample_prm_file = self.full_name+'_StochInput.h5'
        self.solver_prms.update({"ProjectName":self.full_name})

        # both:
        stv=self.samples.stoch_vars
        prms= {"nStochVars"       : 0,
               "nGlobalRuns"      : self.samples.n,
               "nParallelRuns"    : self.n_parallel_runs
               }


        self.write_hdf5(self.sample_prm_file,self.solver_prms,prms)

        self.run_commands = [self.exe_path + ' ' \
                             + self.sample_prm_file + ' ' + self.prmfile]


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

        meshfiles = [self.to_meshfile(i).encode("latin-1").ljust(255) for i in range(self.samples.n)]
        h5f.create_dataset("MeshFiles", data=meshfiles, shape = (self.samples.n,), dtype='S255')

        h5f.close()


    def to_meshfile(self,i):
        return self.mesh_dir+"/"+self.full_name+"_Smesh_R"+str(i+1)+"_mesh.h5"


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
        filename=sorted(glob.glob(self.full_name+"_Restart_BodyForces_*.h5"))[-1]
        with h5py.File(filename, 'r') as h5f:
                dset = h5f['BodyForces_Wall_BC'][()]
        vals=np.array(dset)
        vals /= self.A_q_ref
        # Hack for error in c_l/c_d computation: rotate by 2*AlphaRefState
        # vals_tmp = vals[:,:2]
        # a = 6.*np.pi/180.
        # vals[:,0] = np.cos(a)*vals_tmp[:,0] + np.sin(a)*vals_tmp[:,1]
        # vals[:,1] = np.cos(a)*vals_tmp[:,1] - np.sin(a)*vals_tmp[:,0]
        # second hack: get lift coefficients from forces
        # vals *= 2.
        # if self.name.find("HF") > -1 or self.name.find("3D") > -1: 
           # vals /= 0.05004
        # end hacks
        return vals[:,name]

    def check_finished(self):
        """ 
        Check last lines of logfiles (stdout) for confirmation that 
        the batch is finished. Also retrieve average work, which is 
        written to the log file as well (as part of flexibatch)
        """
        try:
            for logfile in self.logfile_names: 
                # TODO: use check_stdout function
                args=['tail','-n','4',logfile]
                output=subprocess.run(args,stdout=subprocess.PIPE)
                output=output.stdout.decode("utf-8").splitlines()
                index=output.index("FLEXIBATCH FINISHED")
                self.current_avg_work=float(output[index+2])
            return True
        except:
            return False

    def check_stdout(self,fn,nlines,stringcmp):
        args=['tail','-n',str(nlines),fn]
        output=subprocess.run(args,stdout=subprocess.PIPE)
        output=output.stdout.decode("utf-8")
        return output.startswith(stringcmp)

        

class IceMeshRef(Ice):

    cname = "ice_meshref"
    stages = {"meshref"}

    defaults_ = {
        "prmfile" : "dummy_unused",
        }

    def prepare(self):
        if globels.sim.current_iter.n >1: 
            self.run_commands = []
            return
        self.run_commands = ["python3 "+self.exe_path+" NONE NONE "
                             +self.mesh_dir+"/"+self.run_name(0)
                             +" 0 5"]

    def check_finished(self):
        if globels.sim.current_iter.n >1: 
            return True
        try: 
            return self.check_stdout(self.logfile_names[0],3,"msh file:")
        except:
            return False


class IceMesh(Ice):

    cname = "ice_mesh"
    stages = {"mesh"}

    defaults_ = {
        "hopr_path" : "NODEFAULT"
        }

    def prepare(self):
        self.run_commands = []
        command_base = "python3 {} {} {}".format(self.exe_path,self.hopr_path,self.prmfile)
        for i_run, node in enumerate(self.samples.nodes): 
            namestr = self.mesh_dir+"/"+self.run_name(i_run)
            arg_vec = "_".join([str(n) for n in node])
            self.run_commands.append(" ".join([command_base,namestr,arg_vec]))

    def check_finished(self):
        try: 
            all_ok = True
            for logfile in self.logfile_names: 
                args=['grep','-nri','-a4',"ERROR",logfile]
                output=subprocess.run(args,stdout=subprocess.PIPE)
                output=output.stdout.decode("utf-8")
                if len(output)>0: 
                    all_ok = False
                self.current_avg_work = 180. # TODO: actually measure time!
            return all_ok
        except:
            return False


class IceSortSides(Ice):

    cname = "ice_sortsides"
    stages = {"sortsides"}

    defaults_ = {
        "prmfile" : "dummy_unused"
        }

    def prepare(self):
        self.run_commands = [self.exe_path + " " + self.to_meshfile(i) for i in range(self.samples.n)]

    def check_finished(self):
        try: 
            return all([self.check_stdout(lfn,2," SORT ICING SIDES TOOL FINISHED!") for lfn in self.logfile_names])
        except:
            return False


class IceMerge(Ice):

    cname = "ice_merge"
    stages = {"merge"}
    defaults_ = {
        "prmfile"   : "dummy_unused",
        "start_time" : "NODEFAULT",
        "end_time"   : "NODEFAULT"
            }

    def prepare(self):
        # self.statefilename=sorted(glob.glob(self.full_name+"_State_*.h5"))[-1]
        self.avgfilenames=sorted(glob.glob(self.full_name+"_TimeAvg_0*.h5"))
        start_end_str = " --start={} --end={} ".format(self.start_time,self.end_time)
        self.run_commands = [self.exe_path + start_end_str + " ".join(self.avgfilenames)]

    def check_finished(self):
        return self.check_stdout(self.logfile_names[0],2,"Merging DONE:") 


class IceRestart(Ice):

    cname = "ice_restart"
    stages = {"restart"}
    # defaults_ = {
        # "prmfile": "dummy_unused"
        # }

    def prepare(self):
        # main_stage = [s for s self.other_stages if s.cname == "ice"][0]
        # self.sample_prm_file = main_stage.sample_prm_file
        # self.prmfile = main_stage.prmfile
        self.sample_prm_file = self.full_name+'_StochInput.h5'
        with h5py.File(self.sample_prm_file,"r+") as h5f:
            del h5f.attrs["nParallelRuns"]
            h5f.attrs["nParallelRuns"] = self.n_parallel_runs
        self.restartfile=sorted(glob.glob(self.full_name+"_TimeAvg_0*.h5"))[-1]
        self.run_commands = [" ".join([self.exe_path, self.sample_prm_file, 
                                      self.prmfile, self.restartfile])]


    def check_finished(self):
        return True # TODO


class IceSwim(Ice):

    cname = "ice_swim"
    stages = {"swim"}
    defaults_ = {
        "prmfile" : "dummy_unused",
        "refstate" : "NODEFAULT",
        "common_x" : True,
        "x_min" : -0.1,
        "x_max" : 1.0,
        "n_pts" : 100
            }

    def prepare(self):
        # self.statefilename=sorted(glob.glob(self.full_name+"_State_*.h5"))[-1]
        # avgfilename is _Merged_ is that exists and last TimeAvg file else
        self.avgfilename=sorted(glob.glob(self.full_name+"_TimeAvg_*.h5"))[-1]
        self.sample_prm_file = self.full_name+'_StochInput.h5'
        if self.common_x: 
            arg_str = " --InterpolateX {} {} {} ".format(self.x_min,self.x_max,self.n_pts)
        else: 
            arg_str = " "
        self.run_commands = [self.exe_path + arg_str + 
                             self.sample_prm_file + " " + self.avgfilename]

    def check_finished(self):
        # try: 
            with h5py.File(self.avgfilename, 'r') as h5f:
                    dset = h5f['SwimData'][()]
            pres =np.array(dset[:,:,7]) # assumes avg of cons and pres
            u_inf = np.array(self.refstate)
            cp_temp = (pres-u_inf[4])/(0.5*u_inf[0]*np.sum(u_inf[1:4]**2))
            x_tmp = np.linspace(self.x_min,self.x_max,self.n_pts)
            self.x = np.concatenate((x_tmp[::-1],x_tmp))
            # self.valid = pres > 0.
            # self.n_valid = np.sum(self.valid)
            self.cp = np.where(pres >= 0.,cp_temp,0.)
            return True
        # except:
            # return False


class FlexiBatchClBatch(Cfdfv.QoI,Ice.QoI):
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


class FlexiBatchCdBatch(Cfdfv.QoI,Ice.QoI):
    """ 
    first parent is dominant, second adds it to their subclasses dict
    """

    cname = "cd_batch"

    stages = {"all"}

    defaults_ = {
        "prmfile": "dummy_unused"
        }

    # this is dirty: index of BodyForce
    string_in_stdout = 0 


class FlexiBatchCp(Internal.QoI,Ice.QoI):
    """ 
    first parent is dominant, second adds it to their subclasses dict
    """

    cname = "cp"

    stages = {"all"}

    defaults_ = {
        "prmfile": "dummy_unused",
        "do_write" : True
        }

    def get_response(self,s=None): 
        return [p.other_stages[5].cp for p in self.participants]

    def write_to_file(self): 
        if self.do_write: 
            self.outfilename = "output_" + self.cname + ".csv"
            xv = self.participants[0].other_stages[5].x
            with open(self.outfilename,"w") as f: 
                f.write("mean stddev")
                for x, m, s in zip(xv,self.mean,self.stddev): 
                    f.write("\n"+str(x)+" "+str(m)+" "+str(s))

    def integrate(self,qty): 
        return np.mean(qty)



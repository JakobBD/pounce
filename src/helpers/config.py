# ---------- external imports ----------
import yaml
import pickle
import sys
import re
# ---------- local imports -------------
from uqmethod.uqmethod import UqMethod
from machine.machine import Machine
from helpers.baseclass import BaseClass
from helpers.printtools import *
from helpers.tools import *
from helpers import globels


def config(prmfile):
    """
    Reads all user input and sets up (sub-)classes according to this
    input.
    Partially, setup is called from uq-method-specific routines.
    The sim object is copied to globels to be available for pickle.
    """
    # read user input to dict
    with open(prmfile, 'r') as f:
        prms = yaml.safe_load(f)

    # sets up global tools like logger
    print_step("Read parameters")

    # initialize classes according to chosen subclass
    sim = UqMethod.create(prms["uq_method"])
    sim.cfg = GeneralConfig(prms["general"])

    if sim.cfg.stdout_log_file: 
        sys.stdout = Logger(sim.cfg.stdout_log_file)

    # backwards compatibility
    if "machine" in prms: 
        prms["machine"]["name"] = "default"
        prms["machines"] = [prms["machine"]]
        del prms["machine"]

    machines_loc = [Machine.create(subdict) for subdict in prms["machines"]]
    if sum((m.name=="default") for m in machines_loc) != 1: 
        raise Exception("please make exactly one machine the default")
    sim.machines = {m.name:m for m in machines_loc}

    sim.stages = []
    for stage in sim.cfg.main_stages: 
        m_str = stage["machine"] if "machine" in stage else "default"
        m = copy.deepcopy(sim.machines[m_str])
        m.fill(stage["name"],True)
        sim.stages.append(m)

    # in the multilevel case, some further setup is needed for the
    # levels (mainly sorting prms into sublevels f and c)
    sim.setup(prms)

    globels.sim = sim
    return sim

def restart(prmfile=None):
    """
    restart simulation from a pickle file. 
    """
    with open('pounce.pickle', 'rb') as f:
        sim = pickle.load(f)
    if prmfile:
        raise Exception("Modifying parameters at restart is not yet "
                        "implemented")

    n_finished_iter = len(sim.iterations) \
                    - (0 if sim.current_iter.finished else 1)
    if n_finished_iter > 0:
        p_print(cyan("Skipping %i finished Iteration(s)."%(n_finished_iter)))

    globels.sim = sim
    sim.cfg.copy_to_globels()
    apply_changes()
    # extract_mfmc_mlopt()
    # extract_mlmc_mlopt()

    if sim.cfg.stdout_log_file: 
        sys.stdout = Logger(sim.cfg.stdout_log_file)

    return sim

def apply_changes(): 
   """
   This is a custom function which can be used to apply changes to the restart file 
   """
   # print("_".join([str(i) for i in globels.sim.levels[0].samples.nodes[28,:]]))
   # sys.exit()
   pass
   # example: 
   # print(globels.sim.samples.nodes)
   # for qoi in globels.sim.internal_qois:
      # u_out = qoi.get_response()[0]
      # qoi.mean = np.dot(np.transpose(u_out),globels.sim.samples.weights)
      # qoi.stddev = np.sqrt(np.dot(np.transpose(u_out**2),globels.sim.samples.weights) - qoi.mean**2.)
      # print(qoi.cname,qoi.mean,qoi.stddev)
      # # np.savetxt("csv/"+qoi.cname[0:2]+"_all_nisp.csv", qoi.get_response()[0])
   # sys.exit()
   # globels.sim.stages[-2].batches[1].cores_per_sample = 16
   # globels.sim.stages[-2].batches[2].cores_per_sample = 4
   # globels.sim.stages[-2].batches[3].cores_per_sample = 128
   # globels.sim.stages[-2].batches[4].cores_per_sample = 16
   # globels.sim.stages[4].batches[1].start_time=8.5
   # globels.sim.stages[4].batches[2].start_time=8.5
   # globels.sim.n_max_iter = 3
   # return

def extract_mlmc_mlopt():
    sigmasq = []
    mlopt = []
    work = []
    mse = []
    for i, _ in enumerate(globels.sim.levels[0].internal_qois): 
        qv = [m.internal_qois[i] for m in globels.sim.levels[::-1]]
        sigmasq.append([q.sigma_sq for q in qv])
        mlopt.append([q.mlopt for q in qv])
        work.append([q.work_mean_static*q.mlopt for q in qv])
        v_opt = sum([q.sigma_sq/q.mlopt for q in qv])
        mse.append([v_opt,0.]) # get v_ref from MFMC!
    work = np.array(work)
    work = work/np.sum(work,axis=1,keepdims=True)
    sigmasq = np.array(sigmasq)
    # DIRTY: multiplied by 100 to get bar base on bottom axis in tikz
    sigmasq *= 100./sigmasq[:,2:3]
    np.savetxt("csv_mlopt/sigmasq.csv", sigmasq) 
    np.savetxt("csv_mlopt/mlopt.csv",   np.array(mlopt)) 
    np.savetxt("csv_mlopt/work.csv",    np.array(work))#/3.6e9) 
    np.savetxt("csv_mlopt/mse.csv",     np.array(mse))  
    sys.exit()

def extract_mfmc_mlopt():
    omrho = []
    alpha = []
    mlopt = []
    work = []
    mse = []
    for i, _ in enumerate(globels.sim.hfm.internal_qois): 
        qv = [m.internal_qois[i] for m in globels.sim.all_models]
        omrho.append([q.om_rho_sq for q in qv])
        alpha.append([getattr(q,"alpha",0.) for q in qv])
        mlopt.append([getattr(q,"mlopt",1) for q in qv])
        work.append([q.work_mean_static*getattr(q,"mlopt",0) for q in qv])
        _, v_opt = globels.sim.select_models(i) 
        # v_opt = globels.sim.get_v(globels.sim.models_opt+[globels.sim.dummy_model],i)
        v_ref = globels.sim.get_v([globels.sim.hfm,globels.sim.dummy_model],i)
        mse.append([np.sqrt(v_opt),v_opt/v_ref])
    # np.savetxt("csv_mlopt/omrho.csv",   np.transpose(np.array(omrho)))
    # np.savetxt("csv_mlopt/rho.csv",  1.-np.transpose(np.array(omrho)))
    # np.savetxt("csv_mlopt/alpha.csv",   np.transpose(np.array(alpha))) 
    # np.savetxt("csv_mlopt/mlopt.csv",   np.transpose(np.array(mlopt))) 
    # np.savetxt("csv_mlopt/work.csv",    np.transpose(np.array(work)) )
    # np.savetxt("csv_mlopt/mse.csv",     np.transpose(np.array(mse))  )
    work = np.array(work)
    work = work/np.sum(work,axis=1,keepdims=True)
    np.savetxt("csv_mlopt/omrho.csv",   np.array(omrho))
    np.savetxt("csv_mlopt/rho.csv",  1.-np.array(omrho))
    np.savetxt("csv_mlopt/alpha.csv",   np.array(alpha)) 
    np.savetxt("csv_mlopt/mlopt.csv",   np.array(mlopt)) 
    np.savetxt("csv_mlopt/work.csv",    np.array(work))#/3.6e9) 
    # np.savetxt("csv_mlopt/work_cl.csv", work[0,:]/np.sum(work[0,:])) 
    # np.savetxt("csv_mlopt/work_cd.csv", work[1,:]/np.sum(work[1,:])) 
    # np.savetxt("csv_mlopt/work_cp.csv", work[2,:]/np.sum(work[2,:])) 
    np.savetxt("csv_mlopt/mse.csv",     np.array(mse))  
    sys.exit()


def config_list(name,prms,class_init,*args,sub_list_name=None):
    """
    Checks for correct input format for list type input and
    initializes (sub-) class for given input
    """
    if name not in prms:
        raise Exception("Required parameter '"
                        +name+"' is not set in parameter file!")
    prms_loc = expand_prms_by_sublist(prms[name],sub_list_name)
    p_print("Setup "+yellow(name)+" - Number of " + name + " is "
            + yellow(str(len(prms_loc))) + ".")
    indent_in()
    classes = [class_init(sub_dict,*args) for sub_dict in prms_loc]
    indent_out()
    return classes


def expand_prms_by_sublist(prms,sub_list_name): 
    if isinstance(prms,list):
        return prms
    counter, length = count_recursive(prms,sub_list_name,0)
    if counter == 0: 
        print("WARNING: Key "+sub_list_name+" missing in prm file!!!")
    list_out = [copy.deepcopy(prms) for i in range(length)]
    for i_sublist, sub_list in enumerate(list_out): 
        delete_recursive(sub_list,sub_list_name,i_sublist)
    return list_out


def delete_recursive(prms,sub_list_name,i_sublist): 
    names = [k for k in prms.keys()]
    for name in names: 
        entry = prms[name]
        if name == sub_list_name: 
            prms.update(entry[i_sublist])
            del prms[name]
        elif isinstance(entry,dict): 
            delete_recursive(entry,sub_list_name,i_sublist)
        elif isinstance(entry,list): 
            if isinstance(entry[0],dict): 
                for lentry in entry: 
                    delete_recursive(lentry,sub_list_name,i_sublist)


def count_recursive(prms,sub_list_name,counter,length=None):
    for name, entry in prms.items(): 
        if name == sub_list_name: 
            if not isinstance(entry,list): 
                raise Exception(sub_list_name + " always has to be a list!")
            counter +=1 
            if length: 
                if length != len(entry): 
                    raise Exception(sub_list_name + " always has to have same length!")
            length = len(entry)
        elif isinstance(entry,dict): 
            counter, length = count_recursive(entry,sub_list_name,counter,length)
        elif isinstance(entry,list): 
            if isinstance(entry[0],dict): 
                for lentry in entry: 
                    counter, length = count_recursive(lentry,sub_list_name,counter,length)
    return counter, length
        

def config_pp_mach(prms,sim,stage_name):
    if "machine_postproc" in prms: 
        MachineLoc = Machine.subclass("local")
        sub_dict = prms["machine_postproc"]
        pp_mach = MachineLoc(sub_dict)
    else: 
        pp_mach = sim.machines["default"]
    pp_out = copy.deepcopy(pp_mach)
    pp_out.fill(stage_name, False)
    return pp_out


class GeneralConfig(BaseClass):
    """
    Provides a container for some general config options and their
    default values. 
    """

    defaults_ = {
        "archive_level" : 0,
        "do_pickle" : True,
        "project_name" : "NODEFAULT",
        "stdout_log_file": None,
        "main_stages": [{"name":"main"}] # TODO: own class with default
        }

    def __init__(self,*args): 
        super().__init__(*args)
        self.copy_to_globels()

    def copy_to_globels(self):
        globels.archive_level=self.archive_level
        globels.project_name=self.project_name
        globels.do_pickle=self.do_pickle


class Logger(object):
   def __init__(self,filename):
      self.terminal = sys.stdout
      self.log = open(filename, "a")
      self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

   def write(self, message):
      self.terminal.write(message)
      logmsg = self.ansi_escape.sub('', message)
      self.log.write(logmsg)

   def flush(self):
      #this flush method is needed for python 3 compatibility.
      #this handles the flush command by doing nothing.
      #you might want to specify some extra behavior here.
      pass


# ---------- external imports ----------
import yaml
import pickle
import sys
import re
# ---------- local imports -------------
from uqmethod.uqmethod import UqMethod
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

    if sim.cfg.stdout_log_file: 
        sys.stdout = Logger(sim.cfg.stdout_log_file)

    return sim


def config_list(name,prms,class_init,*args,sub_list_name=None):
    """
    Checks for correct input format for list type input and
    initializes (sub-) class for given input
    """
    if name not in prms:
        raise Exception("Required parameter '"
                        +name+"' is not set in parameter file!")
    if sub_list_name: 
        try:
            prms_loc=prms[name][sub_list_name]
            for_all = copy.deepcopy(prms[name])
            del for_all[sub_list_name]
            for entry in prms_loc: 
                entry.update(for_all)
        except KeyError: 
            print(prms)
            raise Exception("Revise input prm structure of "+name+"!")
    else: 
        prms_loc=prms[name]
    if not isinstance(prms_loc,list):
        raise Exception("Parameter'"+name+"' needs to be defined as a list!")
    p_print("Setup "+yellow(name)+" - Number of " + name + " is "
            + yellow(str(len(prms_loc))) + ".")
    indent_in()
    classes = [class_init(sub_dict,*args) for sub_dict in prms_loc]
    indent_out()
    return classes


class GeneralConfig(BaseClass):
    """
    Provides a container for some general config options and their
    default values. 
    """

    defaults_ = {
        "archive_level" : 0,
        "do_pickle" : True,
        "project_name" : "NODEFAULT",
        "stdout_log_file": None
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


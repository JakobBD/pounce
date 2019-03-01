# ---------- external imports ----------
import sys
import yaml
import logging
import copy
import pickle
# ---------- local imports -------------
from simulation import Simulation
from uqmethod.uqmethod import UqMethod
from machine.machine import Machine
from solver.solver import Solver
from stochvar.stochvar import StochVar
from level.level import Level
from helpers.baseclass import BaseClass
from helpers.printtools import *


def config(prmfile):
   """
   Reads all user input and sets up (sub-)classes according to this input
   """
   # read user input to dict
   with open(prmfile, 'r') as f:
      prms = yaml.safe_load(f)

   # sets up global tools like logger
   print_step("Read parameters")
   GeneralConfig(prms["general"])

   # initialize classes according to chosen subclass
   simulation = Simulation()
   simulation.uq_method = UqMethod.create(prms["uq_method"])
   simulation.machine = Machine.create(prms["machine"])
   simulation.solver = Solver.create(prms["solver"])

   # initialize lists of classes for all levels and all stoch_vars
   simulation.uq_method.stoch_vars = config_list("stoch_vars",prms,StochVar.create,simulation.uq_method.stoch_var_defaults)
   defaults = {}
   [defaults.update(x.level_defaults) for x in [simulation.uq_method, simulation.machine] ]
   simulation.uq_method.levels = config_list("levels",prms,Level,defaults)

   # in the multilevel case, some firther setup is needed for the levels (mainly sorting prms into sublevels f and c)
   simulation.uq_method.setup_batches()

   return simulation

def restart(prmfile=None):

   f = open('pickle', 'rb')
   simulation = pickle.load(f)
   f.close()          

   if prmfile:
      raise Exception("Modifying parameters at restart is not yet implemented")

   n_finished_iter = len(simulation.iterations) - (1 if simulation.do_continue else 0)
   if n_finished_iter > 0:
      p_print(cyan("Skipping %i finished Iteration(s)."%(n_finished_iter)))

   return simulation


def config_list(string,prms,class_init,defaults):
   """
   Checks for correct input format for list type input and initializes (sub-) class for given input
   """
   if string not in prms:
      raise Exception("Required parameter '"+string+"' is not set in parameter file!")
   if not isinstance(prms[string],list):
      raise Exception(" Parameter'"+string+"' needs to be defined as a list!")
   p_print("Setup "+yellow(string)+" - Number of " + string + " is " + yellow(str(len(prms[string]))) + ".")
   indent_in()
   classes = [ class_init(sub_dict,defaults) for sub_dict in prms[string] ]
   indent_out()
   return classes


class GeneralConfig(BaseClass):
   """
   This class consists mainly of attributes.
   Its purpose is to ease general parameter readin and default value handling.
   """
   class_defaults={"output_level" : "standard"}

   def __init__(self,input_prm_dict):
      super().__init__(input_prm_dict)
      self.setup_logger()

   def setup_logger(self):
      """
      Setups a global logger with the name 'logger'.
      This logger can accessed in any function by "log = logging.getLogger('logger')".
      
      Three different logging levels:

          - none     : print no logging messages
          - standard : print information messages (i.e. print all messages invoked with "log.info(message)")
          - debug    : print debug + information messages (i.e. print all messages invoked with "log.info(message)"
                       or "log.debug(message)")
      """

      if self.output_level == "none" :       # no logging
         formatter = logging.Formatter()
      elif self.output_level == "standard" : # info
         formatter = logging.Formatter(fmt='%(message)s')
      elif self.output_level == "debug" :    # debug
         formatter = logging.Formatter(fmt='%(levelname)s - %(module)s: %(message)s')

      handler = logging.StreamHandler()
      handler.setFormatter(formatter)

      logger = logging.getLogger('logger')
      if self.output_level == "none" : # no logging
         logger.setLevel(0)
      elif self.output_level == "standard" : # info
         logger.setLevel(logging.INFO)
      elif self.output_level == "debug" : # debug
         logger.setLevel(logging.DEBUG)

      logger.addHandler(handler)
      return logger


def print_default_yml_file():
   """
   Asks for user input to choose one of the available subclasses,
   builds up dictionary of defaults for all variables for this sub class combinatiion,
   then prints default YML file using yaml.dump.
   """
   print("\n_print default YML File\n"+"-"*132+"\n_config:\n")
   all_defaults={}

   parent_classes={"uq_method": UqMethod,
                  "machine": Machine,
                  "solver": Solver }
   subclasses={}

   # First, get defaults for parent classes uq_method, machine and solver.
   for parent_class_name,parent_class in parent_classes.items():

      # Inquire user input to choose subclass for which defaults are to be printed
      subclass_name, class_defaults, subclass = inquire_subclass(parent_class_name,parent_class)

      # build up dictionary with defaults for this parent class.
      class_dict={"_type" : subclass_name}
      class_dict.update(class_defaults)
      class_dict.update(subclass.subclass_defaults)

      # add defaults for this class to dict with all defaults
      all_defaults.update({parent_class_name : class_dict})

      # we need a dict of all chosen subclasses below,
      # as some defaults set per level or per stoch_var depend on the chosen subclasses.
      subclasses.update({parent_class_name:subclass})


   # build defaults per level
   level_defaults_tmp = Level.class_defaults

   # some defaults set per level depend on the chosen uq_method
   level_defaults_tmp.update(subclasses["uq_method"].level_defaults)

   # we update the large defaults dict with a list containing our level dict.
   # This outputs the defaults for n_levels = 1 in the correct format
   all_defaults.update({"levels" : [level_defaults_tmp]})


   # for stoch_vars, we output a list of all implemented types
   var_defaults_tmp=[]
   # loop over all implemented stoch_var types (normal, uniform, ...)
   for stoch_var_name,stoch_var in StochVar.subclasses.items():
      stoch_var_dict={"_type" : stoch_var_name} # name of stoch_var (e.g. normal)
      stoch_var_dict.update(stoch_var.class_defaults.copy())
      stoch_var_dict.update(stoch_var.subclass_defaults)

      # some defaults set per stoch_var depend on the chosen uq_method and are defined in the uq_method subclass
      stoch_var_dict.update(subclasses["uq_method"].stoch_var_defaults)

      # add dict for thi soch_var to list of all stoch_vars
      var_defaults_tmp.append(stoch_var_dict)
   all_defaults.update({"stoch_vars" : var_defaults_tmp})

   # add general config parameters
   all_defaults.update({"general" : GeneralConfig.class_defaults})

   print("\n_default YML File:\n"+"-"*132+"\n")
   print(yaml.dump(all_defaults, default_flow_style=False))
   sys.exit()


def inquire_subclass(parent_class_name,parent_class):
   """
   Asks for user input to choose one of the available subclasses
   """
   msg = "Available types for "+parent_class_name+" (please choose): "
   for subclass_name in parent_class.subclasses:
      msg += subclass_name + ", "
   while True:
      subclass_name=input(msg[:-2]+"\n")
      # check if user input is a valid option
      if subclass_name in parent_class.subclasses:
         return subclass_name, parent_class.class_defaults, parent_class.subclasses[subclass_name]
      else:
         print("Wrong input. Repeat.")

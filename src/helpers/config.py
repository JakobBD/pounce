# ---------- external imports ----------
import sys
import yaml
import logging
import copy
import pickle
# ---------- local imports -------------
from uqmethod.uqmethod import UqMethod
from machine.machine import Machine
from solver.solver import Solver
from stochvar.stochvar import StochVar
from level.level import Level
from helpers.baseclass import BaseClass
from helpers.printtools import *


def Config(prmfile):
   """
   Reads all user input and sets up (sub-)classes according to this input
   """
   # read user input to dict
   with open(prmfile, 'r') as f:
      prms = yaml.safe_load(f)

   # sets up global tools like logger
   PrintStep("Read parameters")
   GeneralConfig(prms["general"])

   # initialize classes according to chosen subclass
   uqMethod = UqMethod.Create(prms["uqMethod"])
   uqMethod.machine = Machine.Create(prms["machine"])
   uqMethod.solver = Solver.Create(prms["solver"])

   # initialize lists of classes for all levels and all stochVars
   uqMethod.stochVars = ConfigList("stochVars",prms,StochVar.Create,uqMethod.stochVarDefaults)
   defaults = {}
   [defaults.update(x.levelDefaults) for x in [uqMethod, uqMethod.machine] ]
   uqMethod.levels = ConfigList("levels",prms,Level,defaults)

   # in the multilevel case, some firther setup is needed for the levels (mainly sorting prms into sublevels f and c)
   uqMethod.SetupLevels()

   return uqMethod

def Restart(prmfile=None):

   f = open('pickle', 'rb')
   uqMethod = pickle.load(f)
   f.close()          

   if prmfile:
      raise Exception("Modifying parameters at restart is not yet implemented")

   nFinishedIter = len(uqMethod.iterations) - (1 if uqMethod.doContinue else 0)
   if nFinishedIter > 0:
      Print(cyan("Skipping %i finished Iteration(s)."%(nFinishedIter)))

   return uqMethod


def ConfigList(string,prms,classInit,defaults):
   """
   Checks for correct input format for list type input and initializes (sub-) class for given input
   """
   if string not in prms:
      raise Exception("Required parameter '"+string+"' is not set in parameter file!")
   if not isinstance(prms[string],list):
      raise Exception(" Parameter'"+string+"' needs to be defined as a list!")
   Print("Setup "+yellow(string)+" - Number of " + string + " is " + yellow(str(len(prms[string]))) + ".")
   IndentIn()
   classes = [ classInit(subDict,defaults) for subDict in prms[string] ]
   IndentOut()
   return classes


class GeneralConfig(BaseClass):
   """
   This class consists mainly of attributes.
   Its purpose is to ease general parameter readin and default value handling.
   """
   classDefaults={"outputLevel" : "standard"}

   def __init__(self,inputPrmDict):
      super().__init__(inputPrmDict)
      self.SetupLogger()

   def SetupLogger(self):
      """
      Setups a global logger with the name 'logger'.
      This logger can accessed in any function by "log = logging.getLogger('logger')".
      
      Three different logging levels:

          - none     : print no logging messages
          - standard : print information messages (i.e. print all messages invoked with "log.info(message)")
          - debug    : print debug + information messages (i.e. print all messages invoked with "log.info(message)"
                       or "log.debug(message)")
      """

      if self.outputLevel == "none" :       # no logging
         formatter = logging.Formatter()
      elif self.outputLevel == "standard" : # info
         formatter = logging.Formatter(fmt='%(message)s')
      elif self.outputLevel == "debug" :    # debug
         formatter = logging.Formatter(fmt='%(levelname)s - %(module)s: %(message)s')

      handler = logging.StreamHandler()
      handler.setFormatter(formatter)

      logger = logging.getLogger('logger')
      if self.outputLevel == "none" : # no logging
         logger.setLevel(0)
      elif self.outputLevel == "standard" : # info
         logger.setLevel(logging.INFO)
      elif self.outputLevel == "debug" : # debug
         logger.setLevel(logging.DEBUG)

      logger.addHandler(handler)
      return logger


def PrintDefaultYMLFile():
   """
   Asks for user input to choose one of the available subclasses,
   builds up dictionary of defaults for all variables for this sub class combinatiion,
   then prints default YML file using yaml.dump.
   """
   print("\nPrint default YML File\n"+"-"*132+"\nConfig:\n")
   allDefaults={}

   parentClasses={"uqMethod": UqMethod,
                  "machine": Machine,
                  "solver": Solver }
   subclasses={}

   # First, get defaults for parent classes uqMethod, machine and solver.
   for parentClassName,parentClass in parentClasses.items():

      # Inquire user input to choose subclass for which defaults are to be printed
      subclassName, classDefaults, subclass = InquireSubclass(parentClassName,parentClass)

      # build up dictionary with defaults for this parent class.
      classDict={"_type" : subclassName}
      classDict.update(classDefaults)
      classDict.update(subclass.subclassDefaults)

      # add defaults for this class to dict with all defaults
      allDefaults.update({parentClassName : classDict})

      # we need a dict of all chosen subclasses below,
      # as some defaults set per level or per stochVar depend on the chosen subclasses.
      subclasses.update({parentClassName:subclass})


   # build defaults per level
   levelDefaultsTmp = Level.classDefaults

   # some defaults set per level depend on the chosen uqMethod
   levelDefaultsTmp.update(subclasses["uqMethod"].levelDefaults)

   # we update the large defaults dict with a list containing our level dict.
   # This outputs the defaults for nLevels = 1 in the correct format
   allDefaults.update({"levels" : [levelDefaultsTmp]})


   # for stochVars, we output a list of all implemented types
   stochVarDefaultsTmp=[]
   # loop over all implemented stochVar types (normal, uniform, ...)
   for stochVarName,stochVar in StochVar.subclasses.items():
      stochVarDict={"_type" : stochVarName} # name of stochVar (e.g. normal)
      stochVarDict.update(stochVar.classDefaults.copy())
      stochVarDict.update(stochVar.subclassDefaults)

      # some defaults set per stochVar depend on the chosen uqMethod and are defined in the uqMethod subclass
      stochVarDict.update(subclasses["uqMethod"].stochVarDefaults)

      # add dict for thi sochVar to list of all stochVars
      stochVarDefaultsTmp.append(stochVarDict)
   allDefaults.update({"stochVars" : stochVarDefaultsTmp})

   # add general config parameters
   allDefaults.update({"general" : GeneralConfig.classDefaults})

   print("\nDefault YML File:\n"+"-"*132+"\n")
   print(yaml.dump(allDefaults, default_flow_style=False))
   sys.exit()


def InquireSubclass(parentClassName,parentClass):
   """
   Asks for user input to choose one of the available subclasses
   """
   msg = "Available types for "+parentClassName+" (please choose): "
   for subclassName in parentClass.subclasses:
      msg += subclassName + ", "
   while True:
      subclassName=input(msg[:-2]+"\n")
      # check if user input is a valid option
      if subclassName in parentClass.subclasses:
         return subclassName, parentClass.classDefaults, parentClass.subclasses[subclassName]
      else:
         print("Wrong input. Repeat.")

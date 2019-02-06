# ---------- external imports ----------
import sys
import yaml
import logging
import copy
# ---------- local imports -------------
from uqmethod.uqmethod import UqMethod
from machine.machine import Machine
from solver.solver import Solver
from stochvar.stochvar import StochVar
from level.level import Level
from .baseclass import BaseClass
from .helpers import Log,Debug


def Config(prmfile): 
   with open(prmfile, 'r') as f:
      prms = yaml.safe_load(f)

   GeneralConfig(prms["general"])  

   uqMethod = UqMethod.Create(prms["uqMethod"])
   uqMethod.machine = Machine.Create(prms["machine"])
   uqMethod.solver = Solver.Create(prms["solver"])
   
   if "stochVars" not in prms:
      sys.exit("'stochVars' is not set in parameter file!")
   if type(prms["stochVars"]) is not list:
      sys.exit("'stochVars' need to be defined as a list!")
   uqMethod.stochVars=[ StochVar.Create(subDict,uqMethod.stochVarDefaults) for subDict in prms["stochVars"] ]

   if "levels" not in prms:
      sys.exit("'levels' is not set in parameter file!")
   if type(prms["levels"]) is not list:
      sys.exit("'levels' need to be defined as a list!")
   uqMethod.levels=[ Level(subDict,uqMethod.levelDefaults) for subDict in prms["levels"] ]

   uqMethod.OwnConfig()

   return uqMethod
      


class GeneralConfig(BaseClass): 
   """This class consists mainly of attributes. 
   Its purpose is to ease general parameter readin and default value handling.
   """
   classDefaults={"outputLevel" : "standard"}

   def InitLoc(self):
      self.SetupLogger()

   def SetupLogger(self):
      """Setups a global logger with the name 'logger'. 
      This logger can accessed in any function by "log = logging.getLogger('logger')".
      Three different logging levels:
          none     : print no logging messages
          standard : print information messages (i.e. print all messages invoked with "log.info(message)")
          debug    : print debug + information messages (i.e. print all messages invoked with "log.info(message)" 
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
   print("\nPrint default YML File\n"+"-"*132+"\nConfig:\n")
   allDefaults={}

   parentClasses={"uqMethod": UqMethod,
                  "machine": Machine,
                  "solver": Solver }
   subclasses={}

   for parentClassName,parentClass in parentClasses.items(): 
      subclassName, classDefaults, subclass = InquireSubclass(parentClassName,parentClass)
      allDefaults.update({parentClassName : {"_type" : subclassName}})
      allDefaults[parentClassName].update(classDefaults)
      allDefaults[parentClassName].update(subclass.subclassDefaults)
      subclasses.update({parentClassName:subclass})

   levelDefaultsTmp = Level.classDefaults
   levelDefaultsTmp.update(subclasses["uqMethod"].levelDefaults)
   allDefaults.update({"levels" : [levelDefaultsTmp]})

   stochVarDefaultsTmp=[]
   for stochVarName,stochVar in StochVar.subclasses.items():
      stochVarDict=copy.deepcopy(StochVar.classDefaults)
      stochVarDict.update(stochVar.subclassDefaults)
      stochVarDict.update(subclasses["uqMethod"].stochVarDefaults)
      stochVarDict.update({"_type" : stochVarName})
      stochVarDefaultsTmp.append(stochVarDict)
   allDefaults.update({"stochVars" : stochVarDefaultsTmp})

   allDefaults.update({"general" : GeneralConfig.classDefaults})

   print("\nDefault YML File:\n"+"-"*132+"\n")
   print(yaml.dump(allDefaults, default_flow_style=False))
   sys.exit()


def InquireSubclass(parentClassName,parentClass): 
   msg = "Available types for "+parentClassName+" (please choose): " 
   for subclassName in parentClass.subclasses:
      msg += subclassName + ", "
   while True:
      subclassName=input(msg[:-2]+"\n")
      if subclassName in parentClass.subclasses:
         return subclassName, parentClass.classDefaults, parentClass.subclasses[subclassName]
      else: 
         print("Wrong input. Repeat.")

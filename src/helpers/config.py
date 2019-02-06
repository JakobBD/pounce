# ---------- external imports ----------
import sys
import yaml
import logging
# ---------- local imports -------------
from uqmethod.uqmethod import UqMethod
from machine.machine import Machine
from solver.solver import Solver
from .baseclass import BaseClass
from .helpers import Log,Debug


def Config(prmfile): 
   with open(prmfile, 'r') as f:
      prms = yaml.safe_load(f)

   GeneralConfig(prms["general"])  

   return UqMethod.Create(prms["uqMethod"]), Machine.Create(prms["machine"]), Solver.Create(prms["solver"])


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

   for key,parentClass in parentClasses.items(): 
      subclassName, classDefaults, subclassDefaults = InquireSubclass(key,parentClass)
      allDefaults.update({key : {"_type" : subclassName}})
      allDefaults[key].update(classDefaults)
      allDefaults[key].update(subclassDefaults)

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
         return subclassName, parentClass.classDefaults, parentClass.subclasses[subclassName].subclassDefaults
      else: 
         print("Wrong input. Repeat.")

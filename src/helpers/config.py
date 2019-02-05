# ---------- external imports ----------
import yaml
import logging
# ---------- local imports -------------
import uqmethod.uqmethod as uqm
import machine.machine as mac
import solver.solver as sol
from .baseclass import BaseClass
from .helpers import Log,Debug

def Config(prmfile): 
   with open(prmfile, 'r') as f:
      prmdict = yaml.safe_load(f)

   GeneralConfig(prmdict["general"])  
   log = logging.getLogger('logger')
   Log("testLog")
   Debug("testDebug")

   uqMethod = uqm.UqMethod.Create(prmdict["uqMethod"])
   machine  = mac.Machine.Create(prmdict["machine"])
   solver   = sol.Solver.Create(prmdict["solver"])

   return uqMethod,machine,solver

class GeneralConfig(BaseClass): 
   """This class consists mainly of attributes. 
   Its purpose is to ease general parameter readin and default value handling.
   """

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

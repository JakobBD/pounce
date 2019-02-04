import yaml
import uqmethod.uqmethod as uqm
import machine.machine as mac
import solver.solver as sol

def Init(prmfile): 
   with open(prmfile, 'r') as f:
      prmdict = yaml.safe_load(f)

   uqMethod = uqm.UqMethod.Create(prmdict["uqMethod"])
   machine  = mac.Machine.Create(prmdict["machine"])
   solver   = sol.Solver.Create(prmdict["solver"])

   return uqMethod,machine,solver

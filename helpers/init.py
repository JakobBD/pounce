import yaml
import uqmethod as uqm
import machine as mac
import solver as sol


def Init(prmfile): 
   with open(prmfile, 'r') as f:
      prmdict = yaml.safe_load(f)

   uqMethod = uqm.UqMethod.Create(prmdict["uqMethod"])
   machine  = mac.Machine.Create(prmdict["machine"])
   solver   = sol.Solver.Create(prmdict["solver"])

   return uqMethod,machine,solver

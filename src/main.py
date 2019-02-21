# global imports
import sys,os
if sys.version_info[0] < 3:
   print('\nPOUNCE only works with Python 3!\n')
   sys.exit()

# local imports
from helpers import config,printtools
from helpers.printtools import *


# parse commmand line arguments

usage="""

Allowed usage:
python3 main.py parameter.yml
python3 main.py -r
python3 main.py -r parameter.yml
python3 main.py --help>
"""
nArgs=len(sys.argv)

if nArgs < 2:
   raise Exception(usage)

if nArgs == 2 and sys.argv[1] in ['-h','--help']:
   config.PrintDefaultYMLFile()

PrintHeader()

lastArgIsPrmFile = sys.argv[-1].endswith(('yml','yaml'))
restartMode = sys.argv[1] in ['-r','--restart']

if nArgs == 2 and lastArgIsPrmFile:
   PrintMajorSection("Start parameter readin and configuration")
   uqMethod = config.Config(sys.argv[-1])
elif restartMode and nArgs == 2:
   PrintMajorSection("Restart simulation")
   uqMethod = config.Restart()
elif restartMode and nArgs == 3 and lastArgIsPrmFile:
   PrintMajorSection("Restart simulation")
   uqMethod = config.Restart(prmfile=sys.argv[-1])
else:
   raise Exception(usage)


# run simulation
uqMethod.RunSimulation()

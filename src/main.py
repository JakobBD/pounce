# global imports
import sys,os

# local imports
from helpers import config,printtools
from helpers.printtools import *

# parse commmand line arguments
if len(sys.argv) == 2 and sys.argv[1] in ['-h','--help']:
   config.PrintDefaultYMLFile()
if not (len(sys.argv) == 2 and sys.argv[1].endswith(('yml','yaml'))):
   sys.exit("\nUsage: <python3 main.py parameter.yml> OR <python3 main.py --help>\n")

PrintHeader()

# read input

PrintMajorSection("Start parameter readin and configuration")
uqMethod = config.Config(sys.argv[1])

# run simulation
uqMethod.RunSimulation()

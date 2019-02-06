# global imports
import sys,os

# local imports
from helpers import config

# parse commmand line arguments
if len(sys.argv) is 2 and sys.argv[1] in ['-h','--help']:
   config.PrintDefaultYMLFile()
if not (len(sys.argv) is 2 and sys.argv[1].endswith('ml')):
   sys.exit("\nUsage: <python3 main.py parameter.yml> OR <python3 main.py --help>\n")

# read input 
uqMethod = config.Config(sys.argv[1])

# run simulation
uqMethod.RunSimulation()

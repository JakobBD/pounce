# global imports
import sys,os
if sys.version_info[0] < 3:
   print('\n_c_e only works with Python 3!\n')
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
n_args=len(sys.argv)

if n_args < 2:
   raise Exception(usage)

if n_args == 2 and sys.argv[1] in ['-h','--help']:
   config.PrintDefaultYMLFile()

print_header()

is_prm_file = sys.argv[-1].endswith(('yml','yaml'))
restart_mode = sys.argv[1] in ['-r','--restart']

if n_args == 2 and is_prm_file:
   print_major_section("Start parameter readin and configuration")
   simulation = config.config(sys.argv[-1])
elif restart_mode and n_args == 2:
   print_major_section("Restart simulation")
   simulation = config.restart()
elif restart_mode and n_args == 3 and is_prm_file:
   print_major_section("Restart simulation")
   simulation = config.restart(prmfile=sys.argv[-1])
else:
   raise Exception(usage)


# run simulation
simulation.run()




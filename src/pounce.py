#!/usr/bin/env python3

"""POUNCE main program.
   Parses arguments, calls config to set up class structure,
   runs UQ simulation. 
"""

import sys
if sys.version_info[0] < 3:
    print('\nPounce only works with Python 3!\n')
    sys.exit()

from helpers import config
from helpers.printtools import *



# parse commmand line arguments

# sdtout string for exceptions (explains correct arguments)
usage="""

Allowed usage:
python3 pounce.py parameter.yml
python3 pounce.py -r
python3 pounce.py -r parameter.yml
"""
n_args=len(sys.argv)

if n_args < 2:
    raise Exception(usage)

print_header()

is_prm_file = sys.argv[-1].endswith(('yml','yaml'))
restart_mode = sys.argv[1] in ['-r','--restart']

# configure simulation, set up class structure
if n_args == 2 and is_prm_file:
    # standard use, fresh start
    print_major_section("Start parameter readin and configuration")
    simulation = config.config(sys.argv[-1])
elif restart_mode and n_args == 2:
    # restart
    print_major_section("Restart simulation")
    simulation = config.restart()
elif restart_mode and n_args == 3 and is_prm_file:
    # restart with changed parameters (not yet implemented)
    print_major_section("Restart simulation")
    simulation = config.restart(prmfile=sys.argv[-1])
else:
    raise Exception(usage)

# run simulation
simulation.run()




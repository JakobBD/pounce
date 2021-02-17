# global imports
import sys
if sys.version_info[0] < 3:
    print('\nPounce only works with Python 3!\n')
    sys.exit()

# local imports
from helpers import config,default_yml
from helpers.printtools import *

import copy
from helpers import globels
import numpy as np
import matplotlib.pyplot as plt

# parse commmand line arguments

# sdtout string for exceptions (explains correct arguments)
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
    default_yml.print_default_yml_file()

print_header()

is_prm_file = sys.argv[-1].endswith(('yml','yaml'))
restart_mode = sys.argv[1] in ['-r','--restart']

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

n_runs = 10
work_vec = [10.,50.,250.]
mse_vec=[]
est_mse_vec=[]
for w in work_vec: 
    mse = 0.
    est_mse = 0.
    for i in range(n_runs): 
        sim_current = copy.deepcopy(simulation)
        sim_current.total_work=w
        globels.sim = sim_current
        # run simulation
        sim_current.run()
        mse += (sim_current.mean+np.pi/64.)**2.
        est_mse += np.sqrt(sim_current.v_opt)
    mse_vec.append(np.sqrt(mse/n_runs))
    est_mse_vec.append(est_mse/n_runs)

plt.figure()
plt.plot(work_vec,mse_vec)
plt.plot(work_vec,est_mse_vec)
plt.xscale("log")
plt.yscale("log")
plt.show()


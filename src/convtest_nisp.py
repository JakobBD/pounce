import sys
import copy
import numpy as np
import matplotlib.pyplot as plt
import time

from helpers import config
from helpers.printtools import *
from helpers import globels




basedir = "/home/jakob/diss/plots/conv/csv_nisp"

prmfile = "parameter_sc.yml"

def write(name,x_data,y_data): 
    with open(basedir + "/" + name + ".csv","w") as f: 
        f.write("x y")
        for x, y in zip(x_data,y_data): 
            f.write("\n"+str(float(x))+" "+str(y))


polydeg_vec = list(range(1,11))
n_pts_vec = [32,128,512,2048,8192]

simulation = config.config(prmfile)
for do_sparse in [True,False]: 
    sparse_str = "sp" if do_sparse else "tp"
    for n_pts in n_pts_vec:
        err_mean_vec=[]
        err_std_vec=[]
        nsamples_vec=[]
        for polydeg in polydeg_vec:
            mse = 0.
            sim_current = copy.deepcopy(simulation)
            sim_current.solver.samples.poly_deg = polydeg
            sim_current.solver.samples.sparse_grid = do_sparse
            sim_current.solver.n_pts = n_pts
            globels.sim = sim_current

            # run simulation
            sim_current.run()

            # err_mean_vec.append(np.abs(sim_current.mean))
            # err_std_vec.append(np.abs(sim_current.stddev-np.sqrt(2.)))

            mean_exact = 2./(3.*np.pi)
            stddev_exact = np.sqrt(0.5 - mean_exact**2)

            err_mean_vec.append(np.abs(sim_current.mean-mean_exact))
            err_std_vec.append(np.abs(sim_current.stddev-stddev_exact))
            nsamples_vec.append(sim_current.solver.samples.n)

            suffix = "_n"+str(n_pts)+"_"+sparse_str

            write("mean"+suffix,polydeg_vec,err_mean_vec)
            write("std"+suffix,polydeg_vec,err_std_vec)
            write("nsamples"+suffix,polydeg_vec,nsamples_vec)





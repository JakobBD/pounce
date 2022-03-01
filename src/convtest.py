import sys
import copy
import numpy as np
import matplotlib.pyplot as plt
import time

from helpers import config
from helpers.printtools import *
from helpers import globels



n_runs = 1000
work_vec = [10.,20., 40., 80., 160., 320., 640.]
basedir = "/home/jakob/diss/plots/conv/csv_mc"


folders =   ["mfmc",               "mlmc",               "mc"              ]
prmfiles =  ["parameter_mfmc.yml", "parameter_mlmc.yml", "parameter_mc.yml"]
n_var_all = [3,                    3,                    1                 ]


def adjust_prms(simulation,i_variant): 
    if folder == "mfmc": 
        if i_variant == 0: 
            simulation.reuse_warmup_samples = False
            simulation.update_alpha = False
            suffix = "noreuse"
        elif i_variant == 1: 
            simulation.reuse_warmup_samples = True
            simulation.update_alpha = False
            suffix = "reuse"
        elif i_variant == 2: 
            simulation.reuse_warmup_samples = True
            simulation.update_alpha = True
            suffix = "updatealpha"
    elif folder == "mlmc": 
        if i_variant == 0:
            simulation.n_max_iter = 2 
            simulation.use_ci = False
            suffix = "n2"
        elif i_variant == 1: 
            simulation.n_max_iter = 4 
            simulation.use_ci = False
            suffix = "n4h"
        elif i_variant == 2:
            simulation.n_max_iter = 4 
            simulation.use_ci = True
            suffix = "n4ci"
    elif folder == "mc": 
            suffix = "ref"
    return suffix

def write(prefix,x_data,y_data): 
    with open(dirloc + "/" + prefix + "_" + suffix + ".csv","w") as f: 
        f.write("x y")
        for x, y in zip(x_data,y_data): 
            f.write("\n"+str(x)+" "+str(y))

start_time = time.time()

for folder,prmfile,n_variants in zip(folders,prmfiles,n_var_all):
    dirloc = basedir + "/" + folder
    print_major_section("Start parameter readin and configuration")
    simulation = config.config(prmfile)
    for i_variant in range(n_variants): 
        suffix = adjust_prms(simulation,i_variant)
        mse_vec=[]
        est_mse_vec=[]
        meanmean_vec=[]
        nsamples_mean_vec=[]
        nsamples_std_vec=[]
        for w in work_vec:
            mse = 0.
            meanmean=0.
            est_mse = 0.
            if simulation.cname() == "mlmc": 
                nsamples = [0 for l in simulation.levels]
                nsamples_sq = [0 for l in simulation.levels]
            elif simulation.cname() == "mfmc": 
                nsamples = [0 for l in simulation.models]
                nsamples_sq = [0 for l in simulation.models]
            for i in range(n_runs): 
                sim_current = copy.deepcopy(simulation)
                sim_current.total_work=w
                globels.sim = sim_current
                # run simulation
                sim_current.run()
                if sim_current.cname() == "mfmc": 
                    mean_sim    = sim_current.mean
                    est_mse_sim = np.sqrt(sim_current.v_opt)
                elif sim_current.cname() == "mlmc": 
                    mean_sim    = sim_current.mean
                    est_mse_sim = sim_current.est_eps
                else: 
                    sys.exit("wrong sim type")
                # mse += (mean_sim)**2.
                mse += (mean_sim+np.pi/64.)**2.
                # mse += (mean_sim-0.25)**2.
                meanmean += (mean_sim-0.25)
                est_mse += est_mse_sim
                if sim_current.cname() == "mlmc": 
                    for il, l in enumerate(sim_current.levels): 
                        nsamples[il] += l.samples.n_previous
                        nsamples_sq[il] += l.samples.n_previous**2
                elif sim_current.cname() == "mfmc": 
                    for il, l in enumerate(sim_current.models): 
                        nsamples[il] += l.samples.n_previous + l.samples.n
                        nsamples_sq[il] += (l.samples.n_previous + l.samples.n)**2

            mean_str = ""
            std_str = ""
            for s, ssq in zip(nsamples,nsamples_sq): 
                mean_str += str(float(s)/n_runs) + " "
                std_str += str(np.sqrt((float(ssq)-float(s)**2/n_runs)/(n_runs-1.))) + " "
            nsamples_mean_vec.append(mean_str)
            nsamples_std_vec.append(std_str)

            mse_vec.append(np.sqrt(mse/n_runs))
            est_mse_vec.append(est_mse/n_runs)
            meanmean_vec.append(meanmean)

        if sim_current.cname() == "mfmc": 
            work_vec = [w+sim_current.work_warmup for w in work_vec]

        write("mse",work_vec,mse_vec)
        write("est_mse",work_vec,est_mse_vec)
        write("nsamples_mean",work_vec,nsamples_mean_vec)
        write("nsamples_std",work_vec,nsamples_std_vec)
        #TODO: nSamples EXTRA!

print()
print(time.time()-start_time)


# plt.figure()
# plt.plot(work_vec,mse_vec)
# plt.plot(work_vec,est_mse_vec)
# plt.xscale("log")
# plt.yscale("log")
# plt.show()


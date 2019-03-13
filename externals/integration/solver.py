import sys
import numpy as np
import h5py
import time

# function to integrate: 
# f = prod over i of sin(x/i-xi_i), i = 1, ..., nVar
def f(x,xi_vec):
    #add some computation time
    for k in range(1000):
        s="hello"
    return np.prod([np.sin(x/(i+1)-xi) for i,xi in enumerate(xi_vec)])

# integrates f over x from 0 to pi with 1st or 2nd order accuracy
def integ(n_points,xi_vec):
    dx=np.pi/n_points
    half_space=0.5*dx # second order
    # half_space=0.     # first order
    x_vec=np.linspace(0.,np.pi-dx,n_points)+half_space
    return np.sum([f(x,xi_vec)*dx for x in x_vec])

# ----------------------------------------------------------------------

# read input
with h5py.File(sys.argv[1], 'r') as h5f: 
    projectname = h5f.attrs['ProjectName']
    n_points    = h5f.attrs['nPoints']
    samples     = np.array(h5f['Samples'])

# ACTUAL SIMULATION
start_time = time.clock()
# performs integration for all samples
all_integs = list(map(lambda xi : integ(n_points,xi) , samples ))
end_time = time.clock()
work_mean =  (end_time - start_time)/len(samples)

# write output
with h5py.File(projectname+'_State.h5', 'w') as h5f:
    h5f.create_dataset('Integral', data=all_integs)
    h5f.attrs['ProjectName'] = projectname
    h5f.attrs['WorkMean'] = work_mean
    h5f.attrs['nSamples'] = len(samples)

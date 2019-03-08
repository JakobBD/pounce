import sys
import numpy as np
import h5py

# read in solution of fine sublevel
with h5py.File(sys.argv[1],'r') as h5f:
    u = np.array(h5f['Integral'])
    weights = np.array(h5f['Weights'])
    projectname = h5f.attrs['ProjectName']

mean = np.dot(u,weights)
variance = np.dot(np.square(u),weights) - mean**2

filename_out='SC_SOLUTION_'+projectname+'_integral.h5'

# write output
with h5py.File(filename_out, 'w') as h5f:
    h5f.attrs['Mean']     = mean
    h5f.attrs['Variance'] = variance
    h5f.attrs['StdDev']   = np.sqrt(variance)



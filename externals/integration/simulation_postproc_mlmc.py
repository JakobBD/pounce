import sys
import numpy as np
import h5py

# read in solution of fine sublevel
Mean=0.
Variance=0.
for fn in sys.argv[1:]:
    with h5py.File(fn,'r') as h5f:
        UFineSum     = h5f.attrs['UFineSum']
        UFineSqSum   = h5f.attrs['UFineSqSum']
        UCoarseSum   = h5f.attrs['UCoarseSum']
        UCoarseSqSum = h5f.attrs['UCoarseSqSum']
        n_samples    = h5f.attrs['nSamples']
    Mean += (UFineSum-UCoarseSum)/n_samples
    VarianceFine = (UFineSqSum - 1./n_samples * UFineSum**2) / (n_samples-1)
    VarianceCoarse = (UCoarseSqSum - 1./n_samples * UCoarseSum**2) / (n_samples-1)
    Variance += VarianceFine - VarianceCoarse


output_filename='SOLUTION_integral.h5'

# write output
with h5py.File(output_filename, 'w') as h5f:
    h5f.attrs['Mean']    = Mean
    h5f.attrs['Variance'] = Variance
    h5f.attrs['StdDev'] = np.sqrt(Variance)

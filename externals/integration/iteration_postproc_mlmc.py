import sys
import numpy as np
import h5py

with h5py.File(sys.argv[1],'r') as h5f:
    n_previous  = h5f.attrs['nPreviousRuns']

# read in solution of fine sublevel
with h5py.File(sys.argv[2],'r') as h5f:
    UFine       = np.array(h5f['Integral'])
    projectname = h5f.attrs['ProjectName']
    work_mean   = h5f.attrs['WorkMean']
    n_samples   = h5f.attrs['nSamples']

sums_filename='postproc_'+projectname+'_integral.h5'

# read in solution of coarse sublevel, if applicable
if len(sys.argv)==4: # i_level > 1
    with h5py.File(sys.argv[3],'r') as h5f:
        UCoarse = np.array(h5f['Integral'])
        work_mean += h5f.attrs['WorkMean']
else: # Level 1 
    UCoarse = [0. for i in UFine]

# get current sums
UFineSum     = sum(UFine)
UFineSqSum   = sum([a**2 for a in UFine])
UCoarseSum   = sum(UCoarse)
UCoarseSqSum = sum([a**2 for a in UCoarse])
DUSqSum      = sum([(f-c)**2 for f,c in zip(UFine,UCoarse)])

# update sums with sums from previous iteration, if applicable
if n_previous > 0: 
    with h5py.File(sums_filename, 'r') as h5f:
        UFineSum     += h5f.attrs["UFineSum"]
        UFineSqSum   += h5f.attrs["UFineSqSum"]
        UCoarseSum   += h5f.attrs["UCoarseSum"]
        UCoarseSqSum += h5f.attrs["UCoarseSqSum"]
        DUSqSum      += h5f.attrs["DUSqSum"]
        work_mean     = (n_samples*work_mean+n_previous*h5f.attrs['WorkMean'])\
                        / (n_samples+n_previous)
        n_samples    += n_previous

# Get SigmaSq
SigmaSq = ( DUSqSum - (UFineSum-UCoarseSum)**2 / n_samples  ) / (n_samples-1)

# write output
with h5py.File(sums_filename, 'w') as h5f:
    h5f.attrs['UFineSum']     = UFineSum
    h5f.attrs['UFineSqSum']   = UFineSqSum
    h5f.attrs['UCoarseSum']   = UCoarseSum
    h5f.attrs['UCoarseSqSum'] = UCoarseSqSum
    h5f.attrs['DUSqSum']      = DUSqSum
    h5f.attrs['SigmaSq']      = SigmaSq
    h5f.attrs['WorkMean']     = work_mean
    h5f.attrs['nSamples']     = n_samples



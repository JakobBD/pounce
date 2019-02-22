import sys
import numpy as np
import h5py

# read in solution of fine sublevel
with h5py.File(sys.argv[1],'r') as h5f:
   UFine       = np.array(h5f['Integral'])
   projectname = h5f.attrs['ProjectName']
   workMean    = h5f.attrs['WorkMean']
   nSamples    = h5f.attrs['nSamples']
   nPrevious   = h5f.attrs['nPrevious']

sumsFilename='sums_'+projectname+'.h5'

# read in solution of coarse sublevel, if applicable
if len(sys.argv)==3: # iLevel > 1
   with h5py.File(sys.argv[2],'r') as h5f:
      UCoarse = np.array(h5f['Integral'])
      workMean += h5f.attrs['WorkMean']
else: # Level 1 
   UCoarse = [0. for i in UFine]

# get current sums
UFineSum   = sum(UFine)
UCoarseSum = sum(UCoarse)
DUSqSum    = sum([(f-c)**2 for f,c in zip(UFine,UCoarse)])

# update sums with sums from previous iteration, if applicable
if nPrevious > 0: 
   with h5py.File(sumsFilename, 'r') as h5f:
      UFineSum   += h5f.attrs["UFineSum"]
      UCoarseSum += h5f.attrs["UCoarseSum"]
      DUSqSum    += h5f.attrs["DUSqSum"]
      workMean = (nSamples*workMean + nPrevious*h5f.attrs['WorkMean']) / (nSamples+nPrevious)
      nSamples += nPrevious

# Get SigmaSq
SigmaSq = ( DUSqSum - (UFineSum-UCoarseSum)**2 / nSamples  ) / (nSamples-1)

# write output
with h5py.File(sumsFilename, 'w') as h5f:
   h5f.attrs['UFineSum']   = UFineSum
   h5f.attrs['UCoarseSum'] = UCoarseSum
   h5f.attrs['DUSqSum']    = DUSqSum
   h5f.attrs['SigmaSq']    = SigmaSq
   h5f.attrs['WorkMean']   = workMean



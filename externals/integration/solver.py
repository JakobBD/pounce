import sys
import numpy as np
import h5py
import time

#integrates sin(x-xi) from 0 to pi/iVar using the midpoint rule
def Int1D(nPoints,iVar,xi):
   # halfSpace=0.5*np.pi/(iVar*nPoints)
   halfSpace=0.
   x=np.linspace(xi/iVar+halfSpace,(xi+np.pi)/iVar-halfSpace,nPoints)
   #add some computation time
   for i in range(nPoints):
      for j in range(nPoints): 
         for k in range(100):
            s="hello"
   return sum(np.sin(xx) for xx in x)*(np.pi/iVar)/nPoints

# multiplies 1D integrals in all dimensions
def IntnD(nPoints,xiVec):
   return np.product([Int1D(nPoints,iVar+1,xi) for iVar,xi in enumerate(xiVec)])

#read input
with h5py.File(sys.argv[1], 'r') as h5f: 
   projectname = h5f.attrs['ProjectName']
   nPoints     = h5f.attrs['nPoints']
   nPrevious   = h5f.attrs['nPrevious']
   samples     = np.array(h5f['Samples'])

# ACTUAL SIMULATION STARTS HERE
startTime = time.clock()
# performs integration for all samples
allIntegs = list(map(lambda xi : IntnD(nPoints,xi) , samples ))
endTime = time.clock()
workMean =  (endTime - startTime)/len(samples)

#write output
with h5py.File(projectname+'_State.h5', 'w') as h5f:
   h5f.create_dataset('Integral', data=allIntegs)
   h5f.attrs['ProjectName'] = projectname
   h5f.attrs['WorkMean'] = workMean
   h5f.attrs['nSamples'] = len(samples)
   h5f.attrs['nPrevious'] = nPrevious

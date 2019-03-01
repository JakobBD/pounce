import sys
import numpy as np
import h5py
import time

#integrates sin(x-xi) from 0 to pi/i_var using the midpoint rule
def int1_d(n_points,i_var,xi):
   # half_space=0.5*np.pi/(i_var*n_points)
   half_space=0.
   x=np.linspace(xi/i_var+half_space,(xi+np.pi)/i_var-half_space,n_points)
   #add some computation time
   for i in range(n_points):
      for j in range(n_points): 
         for k in range(100):
            s="hello"
   return sum(np.sin(xx) for xx in x)*(np.pi/i_var)/n_points

# multiplies 1_d integrals in all dimensions
def intn_d(n_points,xi_vec):
   return np.product([int1_d(n_points,i_var+1,xi) for i_var,xi in enumerate(xi_vec)])

#read input
with h5py.File(sys.argv[1], 'r') as h5f: 
   projectname = h5f.attrs['ProjectName']
   n_points     = h5f.attrs['nPoints']
   n_previous   = h5f.attrs['nPrevious']
   samples     = np.array(h5f['Samples'])

# ACTUAL SIMULATION STARTS HERE
start_time = time.clock()
# performs integration for all samples
all_integs = list(map(lambda xi : intn_d(n_points,xi) , samples ))
end_time = time.clock()
work_mean =  (end_time - start_time)/len(samples)

#write output
with h5py.File(projectname+'_State.h5', 'w') as h5f:
   h5f.create_dataset('Integral', data=all_integs)
   h5f.attrs['ProjectName'] = projectname
   h5f.attrs['WorkMean'] = work_mean
   h5f.attrs['nSamples'] = len(samples)
   h5f.attrs['nPrevious'] = n_previous

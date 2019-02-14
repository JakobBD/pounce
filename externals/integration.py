import argparse
import numpy as np
import h5py
import time

def Function(func,spacing,sample,n):
   for ind,sp in enumerate(sample):
      func[ind]=func[ind]+sp*spacing**(n+1)
   return func

def WriteHdf5(integral,weights,projectname,level,sublevel,workMean):
   h5f = h5py.File(projectname+'_'+str(level)+sublevel+'_State.h5', 'w')
   h5f.create_dataset('Integral', data=integral)
   h5f.create_dataset('Weights', data=weights)
   h5f.create_dataset('WorkMean', data=workMean)
   h5f.attrs['ProjectName'] = projectname
   h5f.attrs['Level']       = level
   h5f.attrs['SubLevel']    = sublevel
   h5f.close()

parser = argparse.ArgumentParser(description='Integration of function with two input parameters')
parser.add_argument('-f','--file'   ,help='Stochastic Input h5 File')

args = parser.parse_args()

h5f = h5py.File(args.file, 'r')
projectname = h5f.attrs['Projectname']
level    = h5f.attrs['Level']
nPoints  = h5f.attrs['nPoints']
try:
   sublevel = h5f.attrs['Sublevel']
except:
   sublevel = ''
varnames = h5f.attrs['StochVars']
sample   = np.transpose(np.array(h5f['Samples']))
weights  = np.transpose(np.array(h5f['Weights']))
spacing  = np.linspace(0.,10.,nPoints)
cells    = len(spacing)-1
function = np.zeros((len(sample[0]),len(spacing)))
for i in range(len(varnames)):
   function=Function(function,spacing,sample[i],i)


integral = np.zeros(len(sample[0]))
startTime = time.clock()
for i in range(cells):
   integral = integral + (np.transpose(function)[i+1]+np.transpose(function)[i])/2.*(spacing[1]-spacing[0])
workMean =  (time.clock() - startTime)/len(sample[0])
WriteHdf5(integral,weights,projectname,level,sublevel,workMean)

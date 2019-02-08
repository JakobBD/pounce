import argparse
import numpy as np
import h5py

def Function(func,spacing,sample,n):
   for ind,sp in enumerate(sample):
      func[ind]=func[ind]+sp*spacing**n
   return func

def WriteHdf5(projectname,level,nSamples,sums):
   h5f = h5py.File(projectname+'_'+str(level)+'_Postproc.h5', 'w')
   h5f.attrs['ProjectName'] = projectname
   h5f.attrs['Level']       = level
   h5f.attrs['nSamples']    = nSamples
   for key,value in sums.items():
      h5f.create_dataset(key, data=value)
   h5f.close()

parser = argparse.ArgumentParser(description='Integration of function with two input parameters')
parser.add_argument('-f','--file'   ,help='Stochastic Input h5 File',nargs='+')

args = parser.parse_args()

h5f = h5py.File(args.file[0], 'r')
projectname = h5f.attrs['ProjectName']
level = h5f.attrs['Level']
integralF = np.array(h5f['Integral'])
weights   = np.array(h5f['Weights'])
nNewSamples=len(integralF)
h5f.close()

if level > 1:
   h5f = h5py.File(args.file[1], 'r')
   integralC = np.array(h5f['Integral'])
   h5f.close()

sums = {}
try :
   h5f = h5py.File(projectname+'_'+str(level)+'_Postproc.h5', 'r')
   nSamples = h5f.attrs['nSamples']
   sums.update({"uFineSum":np.array(h5f['uFineSum'])})
   sums.update({"uFineSqSum":np.array(h5f['uFineSqSum'])})
   if level > 1:
      sums.update({"uCoarseSum":np.array(h5f['uCoarseSum'])})
      sums.update({"uCoarseSqSum":np.array(h5f['uCoarseSqSum'])})
      sums.update({"dUSqSum":np.array(h5f['dUSqSum'])})
   h5f.close()
except:
   nSamples=0
   sums.update({"uFineSum": 0.})
   sums.update({"uFineSqSum": 0.})
   if level > 1:
      sums.update({"uCoarseSum": 0.})
      sums.update({"uCoarseSqSum": 0.})
      sums.update({"dUSqSum": 0.})

nSamples+=nNewSamples
for i in range(nNewSamples):
   sums["uFineSum"]   += integralF[i]
   sums["uFineSqSum"] += (integralF[i])**2
   if level > 1:
      sums["uCoarseSum"]   += integralC[i]
      sums["uCoarseSqSum"] += (integralC[i])**2
      sums["dUSqSum"]      += (integralF[i]-integralC[i])**2
if level > 1:
   sums["mean"] = (sums["uFineSum"]-sums["uCoarseSum"])/nSamples
   sums["sigmaSq"] = (sums["dUSqSum"])/(nSamples-1)-(sums["uFineSum"]-sums["uCoarseSum"])**2/(nSamples*(nSamples-1))
else:
   sums["mean"] = np.sum(integralF*weights) if len(weights)>0 else np.sum(integralF*(1./nSamples))
   sums["sigmaSq"] = np.sum((integralF)**2*weights) -np.sum(integralF*weights)**2 if len(weights)>0 \
                    else  (sums["uFineSqSum"])/(nSamples-1)-(sums["uFineSum"])**2/(nSamples*(nSamples-1))

WriteHdf5(projectname,level,nSamples,sums)

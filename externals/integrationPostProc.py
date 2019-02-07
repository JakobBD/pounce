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
   for key,value in sums.items():
      h5f.create_dataset(key, data=value)
   h5f.close()

parser = argparse.ArgumentParser(description='Integration of function with two input parameters')
parser.add_argument('-f','--file'   ,help='Stochastic Input h5 File',nargs='+')
parser.add_argument('-s','--sums'   ,help='h5 file containing the all sum from previous simulations.')

args = parser.parse_args()

h5f = h5py.File(args.file[0], 'r')
projectname = h5f.attrs['ProjectName'] 
level = h5f.attrs['Level'] 
integralF = np.array(h5f['Integral'])
nNewSamples=len(integralF)
h5f.close()

if level > 1:
   h5f = h5py.File(args.file[1], 'r')
   integralC = np.array(h5f['Integral'])
   h5f.close()

sums = {}
if args.sums:
   h5f = h5py.File(args.sums, 'r')
   nSamples = h5f['nSamples']
   sums.update({"uFineSum":h5f['uFineSum']})
   sums.update({"uFineSqSum":h5f['uFineSqSum']})
   if level > 1:
      sums.update({"uCoarseSum":h5f['uCoarseSum']})
      sums.update({"uCoarseSqSum":h5f['uCoarseSqSum']})
      sums.update({"dUSqSum":h5f['dUSqSum']})
   h5f.close()
else:
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
   sums["mean"] = sums["uFineSum"]/nSamples
   sums["sigmaSq"] = (sums["uFineSqSum"])/(nSamples-1)-(sums["uFineSum"])**2/(nSamples*(nSamples-1))

WriteHdf5(projectname,level,nSamples,sums)



import numpy as np
import os

from .uqmethod import UqMethod

@UqMethod.RegisterSubclass('mlmc')
class Mlmc(UqMethod):
   def GetNodesAndWeights(self,nSamples):
       """Draws random samples for uncertain input

       Args:
          nSamples [1:nLevels]: array of number of samples to draw .

       Returns:
          samples[0:nLevels-1,0:nStochDim].
       """
       samples=[]
       weights=[]
       for idx,level in self.levels.items():
          localSamples=[]
          for key in self.stochvar.items():
             dist = self.stochvar[key[0]]
             if(dist['distribution']=="uniform"):
                localSamples.append(np.random.uniform(dist[dist['distribution']][0],dist[dist['distribution']][1],nSamples[idx-1]))
             elif(dist['distribution']=="normal"):
                localSamples.append(np.random.normal(dist[dist['distribution']][0],dist[dist['distribution']][1],nSamples[idx-1]))
             else:
                sys.exit('Distribution {} not implemented'.format(key))

          samples.append(localSamples)
          weights.append(np.ones(nSamples[idx-1])/nSamples[idx-1])
       return samples,weights

   def PrepareSimulation(self,samples,weights,solver):
       varnames = []
       for key in self.stochvar.items():
          dist = self.stochvar[key[0]]
          varnames.append(dist['name'])
       for idx,level in self.levels.items():
          for sublevel in ['c','f']:
             prepSimuDict={'level'    : level,
                           'sublevel': sublevel,
                           'varnames': varnames,
                           'samples' : samples,
                           'weights' : weights  }
             # solver.PrepareSimulation(prepSimuDict)
       return(prepSimuDict)

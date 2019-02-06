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
       levels=self.levels
       for idx,level in levels.items():
          localSamples=[]
          for dist in self.distribution:
             for key in dist:
                if(key=="uniform"):
                   localSamples.append(np.random.uniform(dist[key][0],dist[key][1],nSamples[idx-1]))
                elif(key=="normal"):
                   localSamples.append(np.random.normal(dist[key][0],dist[key][1],nSamples[idx-1]))
                else:
                   sys.exit('Distribution {} not implemented'.format(key))

          samples.append(localSamples)
          weights.append(np.ones(nSamples[idx-1])/nSamples[idx-1])
       return samples,weights

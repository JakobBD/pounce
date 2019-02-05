import numpy as np
from .uqmethod import UqMethod
from .stochparameters import StochParameters


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
       for idx,level in enumerate(self.levels):
          localSamples=[]
          localweights=[]
          for dist in self.distribution:
             for key in dist:
                if(key=="uniform"):
                   localSamples.append(np.random.uniform(dist[key][0],dist[key][1],nSamples[idx]))
                if(key=="normal"):
                   localSamples.append(np.random.normal(dist[key][0],dist[key][1],nSamples[idx]))
          samples.append(localSamples)
          weights.append(localweights)
       return samples,weights

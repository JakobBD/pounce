import numpy as np
import time
import pyKriging
# from numba import jit 

from helpers import globels 
from .surrogate import SurrogateModel

class Kriging(SurrogateModel): 

    cname = "kriging"

class KrigingStandard(Kriging.QoI):

    stages = {"all"}

    cname = "standard"

    def get_response(self,s=None): 
        own_model, model_in, qoi_in = self.participants
        # if not hasattr(self,"k"): 
        if len(globels.sim.iterations) == 1: 
            x_in = model_in.samples.nodes
            y_in = qoi_in.u
            self.k = pyKriging.krige.kriging(x_in, y_in, name='simple')
            self.k.train()
        start_time = time.time()
        # u = predict(own_model.samples.nodes,self.k)
        u = np.array([self.k.predict(x) for x in own_model.samples.nodes])
        self.current_work_mean = (time.time() - start_time)/own_model.samples.n
        return [u]

# @jit()
# def predict(xv,k):
    # u = []
    # for x in xv: 
        # u.append(k.predict(x))
    # return np.array(u)

import numpy as np
import time
import pyKriging

from .surrogate import SurrogateModel

class Kriging(SurrogateModel): 
    pass

class Standard(Kriging.QoI):

    def get_response(self,s=None): 
        own_model, model_in, qoi_in = self.participants
        if not hasattr(self,"k"): 
            x_in = model_in.samples.nodes
            y_in = qoi_in.u
            self.k = pyKriging.krige.kriging(x_in, y_in, name='simple')
            self.k.train()
        start_time = time.time()
        u = np.array([self.k.predict(x) for x in own_model.samples.nodes])
        self.current_work_mean = (time.time() - start_time)/own_model.samples.n
        return [u]

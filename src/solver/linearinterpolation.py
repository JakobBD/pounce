import numpy as np
import time

from .surrogate import SurrogateModel

class LinearInterpolation(SurrogateModel): 
    """
    Only works for one stochastic variable!
    """

    cname = "linear_interpolation"

class LinearInterpolationStandard(LinearInterpolation.QoI):

    cname = "standard"
    stages = {"all"}

    def get_response(self,s=None): 
        own_model, model_in, qoi_in = self.participants
        if not hasattr(self,"x_in"): 
            if model_in.samples.nodes.shape[1] != 1: 
                raise Exception("Linear interpolation only works for one stochastic variable!")
            self.x_in, self.y_in = zip(*sorted(zip(model_in.samples.nodes[:,0], qoi_in.u)))
        start_time = time.time()
        x_eval = own_model.samples.nodes[:,0]
        u = np.interp(x_eval, self.x_in, self.y_in)
        self.participants[0].current_avg_work = (time.time() - start_time)/own_model.samples.n
        return [u]


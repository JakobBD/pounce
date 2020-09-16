import h5py
import numpy as np
import time

from .solver import Solver,QoI
from .cfdfv import Cfdfv
from helpers.printtools import *
from helpers.tools import *
from helpers import globels
import pyKriging


class SurrogateModel(Solver):

    defaults_ = {
        "solver_prms" : "dummy_unused",
        "exe_path" : "dummy_unused",
        "n_samples_input": "NODEFAULT",
        "i_model_input": "NODEFAULT"
            }

    def __init__(self,*args,**kwargs): 
        super().__init__(*args,**kwargs)
        # has to be done since mfmc overwrites defaults 
        self.is_surrogate = True

    class QoI(QoI):

        defaults_ = {
            "exe_path" : "dummy_unused"
                }

        def __init__(self,*args,**kwargs): 
            super().__init__(*args,**kwargs)
            self.internal = True

        def get_current_work_mean(self):
            return self.current_work_mean

class LinearInterpolation(SurrogateModel): 
    """
    Only works for one stochastic variable!
    """
    pass

class Standard(LinearInterpolation.QoI):

    def get_response(self,s=None): 
        own_model, model_in, qoi_in = self.participants
        if not hasattr(self,"x_in"): 
            if model_in.samples.nodes.shape[1] != 1: 
                raise Exception("Linear interpolation only works for one stochastic variable!")
            self.x_in, self.y_in = zip(*sorted(zip(model_in.samples.nodes[:,0], qoi_in.u)))
        start_time = time.time()
        x_eval = own_model.samples.nodes[:,0]
        u = np.interp(x_eval, self.x_in, self.y_in)
        self.current_work_mean = (time.time() - start_time)/own_model.samples.n
        return [u]




# class Kriging(SurrogateModel): 
    # pass

# class Standard(Kriging.QoI):

    # def get_response(self,s=None): 
        # own_model, model_in, qoi_in = self.participants
        # if not hasattr(self,"x_in"): 
            # self.x_in = model_in.samples.nodes
            # self.y_in = qoi_in.u
        # start_time = time.time()
        # x_eval = own_model.samples.nodes
        
        # self.current_work_mean = (time.time() - start_time)/own_model.samples.n
        # return [u]

import h5py
import numpy as np

from .solver import Solver,QoI
from .cfdfv import Cfdfv
from helpers.printtools import *
from helpers.tools import *
from helpers import globels

class Internal(Solver):
    """
    dummy solver. all compuations are carried out during the check_finished routine
    """

    defaults_ = {
        "solver_prms" : "dummy_unused",
        "exe_path" : "dummy_unused",
        "n_pts" : None                    # use f_mf is None, else f_ml
            }

    class QoI(QoI):

        defaults_ = {
            "exe_path" : "dummy_unused"
                }

        def __init__(self,*args,**kwargs): 
            super().__init__(*args,**kwargs)
            self.internal = True


        def get_response(self,s=None): 
            return [np.array(p.u) for p in self.participants]

        def get_derived_quantity(self,quantity_name):
            """ 
            Readin sigma_sq or avg_walltime for MLMC.
            """
            qty = getattr(self,quantity_name,"not found")
            if qty == "not found": 
                raise Exception("Quantity " + quantity_name + " not found!")
            else: 
                return qty

        def get_current_work_mean(self):
            """ 
            For Flexi, avg work is already read from HDF5 file during 
            check_all_finished
            """
            return sum(p.current_avg_work for p in self.participants)

    def __init__(self,*args,**kwargs): 
        super().__init__(*args,**kwargs)
        self.f = self.f_ml if self.n_pts else self.f_mf

    def prepare(self):
        self.project_name = globels.project_name+'_'+self.name
        self.run_commands = []

    def check_finished(self):
        self.u, self.w = [], []
        for xi in self.samples.nodes:
            f,w = self.f(xi[0])
            self.u.append(f)
            self.w.append(w)
        self.current_avg_work = np.mean(np.array(self.w))
        return True

    def f_mf(self,xi):
        t0 = 1.0  * np.sin(np.pi * xi)
        t1 = 0.2  * np.sign(xi)
        t2 = 0.1  * np.sin(5. * np.pi * xi)
        t3 = 0.01 * xi**3

        if self.name == "hf": 
            f = t0 #+ t1 + t2 + t3
            w = 2000.
        elif self.name == "lf1": 
            f = t0 + t1 + t2
            w = 0.2
        elif self.name == "lf2": 
            f = t0 + t1
            w = 0.03
        elif self.name == "lf3": 
            f = t0 + t2
            w = 0.01
        else: 
            sys.exit("invalid model name")
        return f, w/10000.


    def f_ml(self,xi):
        x = np.linspace(-1.,xi,self.n_pts+1)
        y = np.pi*np.cos(np.pi*x)
        return np.trapz(y, dx = (1. + xi) / self.n_pts), float(self.n_pts**2)/10000.



class InternalStandard(Internal.QoI):
    pass



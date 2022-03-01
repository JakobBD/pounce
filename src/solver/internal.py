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

    cname = "internal"

    defaults_ = {
        "solver_prms" : "dummy_unused",
        "exe_path" : "dummy_unused",
        "n_pts" : None                    # use f_mf is None, else f_ml
            }

    class QoI(QoI):

        stages = {"all"}

        defaults_ = {
            "exe_path" : "dummy_unused"
                }

        internal = True

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


    def __init__(self,*args,**kwargs): 
        super().__init__(*args,**kwargs)
        self.f = self.f_ml if self.n_pts else self.f_mf

    def prepare(self):
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
        t0 = 1.0  * np.sin(np.pi * xi)      + 100.*np.maximum(0.,xi-0.9)
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


    # def f_ml(self,xi):
        # x = np.linspace(-1.,xi,self.n_pts+1)
        # y = np.pi*np.cos(np.pi*x)
        # return np.trapz(y, dx = (1. + xi) / self.n_pts), float(self.n_pts**2)/10000.

    def f_ml(self,xi):
        # first order integration of pi*cos(pi*x) from -1 to xi 
        # exact solution is sin(pi*xi)
        dx = (1. + xi) / self.n_pts
        x = np.linspace(-1.,xi-dx,self.n_pts)
        y = np.pi*np.cos(np.pi*x)
        # integrand += 50 for x > 0.9
        # mean exact solution += 50*max(0.,x-0.9)
        # y += (1.+np.sign(x-0.9))*50.
        return np.sum(y)*dx, float(self.n_pts**2)/10000.


class InternalStandard(Internal.QoI):

    cname = "standard"


class InternalDouble(Internal.QoI):

    cname = "double"

    defaults_ = {
        "do_write" : False
         }

    def get_response(self,s=None): 
        def double(a): 
            a_ext = np.array(a)[:,np.newaxis]
            return np.concatenate((a_ext,a_ext),axis=1)
        return [double(p.u) for p in self.participants]

    def write_to_file(self): 
        if self.do_write: 
            self.outfilename = "output_" + self.cname + ".csv"
            with open(self.outfilename,"w") as f: 
                f.write("mean stddev")
                for x, y in zip(self.mean,self.stddev): 
                    f.write("\n"+str(x)+" "+str(y))

    def integrate(self,qty): 
        return np.mean(qty)







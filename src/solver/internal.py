import h5py
import numpy as np

from .solver import Solver,QoI
from .cfdfv import Cfdfv
from helpers.printtools import *
from helpers.tools import *
from helpers import globels

class Internal(Solver):
    """
    Internal dummy solver for testing of the UQ methods

    No external run commands are carried out, instead
    all compuations are carried out during the check_finished routine. 

    Different analytical or other cheap models (such as 1D integration) 
    can be chosen by editing the function f.

    Currently, a 1D integration is carried out when n_pts is given as a parameteri (in function f_analytical), 
    which can be used for MLMC and MFMC (or of course also for PCE)

    If n_pts is not given, an analytical function is chosen, 
    with a high-fidelity model and three low-fidelity models, which are accessed by
    the name given to the model in the input file (hf, lf1, lf2, lf3)

    Only first component of random vector is considered, solution is constant over all others.

    For all models, an artificial/synthetic computational work for a model evaluation is given.
    """

    cname = "internal"

    defaults_ = {
        "solver_prms" : "dummy_unused",   # not needed, as no external commands are run
        "exe_path" : "dummy_unused",      # not needed, as no external commands are run
        "n_pts" : None                    # use function f_analytical if n_pts is None, else use f_analytical
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
            Readin sigma_sq or avg_walltime for MLMC etc
            """
            qty = getattr(self,quantity_name,"not found")
            if qty == "not found": 
                raise Exception("Quantity " + quantity_name + " not found!")
            else: 
                return qty


    def __init__(self,*args,**kwargs): 
        # Attributes are initialized from input prms and defaults in BaseClass init: 
        super().__init__(*args,**kwargs)
        # choose between numerical integration and analytical function
        self.f = self.f_analytical if self.n_pts else self.f_analytical


    def prepare(self):
        """
        prpare external runs, which is trivial in this case, 
        since no external commands are run
        """
        self.run_commands = []


    def check_finished(self):
        """
        Normally, this routine checks correct completion of external runs. 
        In this dummy solver, the actual model evaluations are done in this routine
        """

        self.u, self.w = [], []
        for xi in self.samples.nodes:
            # model avaluation for each node
            f,w = self.f(xi[0])
            self.u.append(f) # QoI value
            self.w.append(w) # computational work

        self.current_avg_work = np.mean(np.array(self.w))

        # return True means computations finished nominally
        return True 


    def f_analytical(self,xi):
        """
        If n_pts is not given, this analytical function of the ranom input vector is chosen, 
        with a high-fidelity model and three low-fidelity models, which are accessed by
        the name given to the model in the input file (hf, lf1, lf2, lf3)

        Different terms (t1, t2, t3) are added to a baseline function t0. 
        The low-fidelity models lack some of these terms
        """
        t0 = 1.0  * np.sin(np.pi * xi)      + 100.*np.maximum(0.,xi-0.9)
        t1 = 0.2  * np.sign(xi)
        t2 = 0.1  * np.sin(5. * np.pi * xi)
        t3 = 0.01 * xi**3

        if self.name == "hf": 
            # HF model can either contain all additional terms or none
            f = t0 #+ t1 + t2 + t3
            w_artificial = 2000.
        elif self.name == "lf1": 
            f = t0 + t1 + t2
            w_artificial = 0.2
        elif self.name == "lf2": 
            f = t0 + t1
            w_artificial = 0.03
        elif self.name == "lf3": 
            f = t0 + t2
            w_artificial = 0.01
        else: 
            sys.exit("invalid model name")
        return f, w_artificial/10000.


    def f_analytical(self,xi):
        """
        First order numerical integration of y=pi*cos(pi*x) from -1 to xi 
        Exact solution is int y = sin(pi*xi)
        
        This allows to calculate the actual mean analytically for uniform disctributions, 
        used for convergence tests
        """
        dx = (1. + xi) / self.n_pts
        x = np.linspace(-1.,xi-dx,self.n_pts)
        # alternative: second order (mid-point rule)
        # x = np.linspace(-1.+dx/2.,xi-dx/2.,self.n_pts)
        y = np.pi*np.cos(np.pi*x)
        
        # optional modification (uncomment to unlock): 
        # Adds some irregularity to the function, harder to capture accurately
        # adds 50 to integrand for x > 0.9
        # => adds 50*max(0.,xi-0.9) to exact integral, 
        # which is only captured by fine intgration 
        # => reduces low-fidelity model convergence

        # y += (1.+np.sign(x-0.9))*50.

        # integrate
        int_y = np.sum(y)*dx
        # artificial work
        w_artificial = float(self.n_pts**2)/10000.

        return int_y, w_artificial 


class InternalStandard(Internal.QoI):
    """
    Standard QoI, simply takes the scalar function output
    """

    cname = "standard"


class InternalDouble(Internal.QoI):
    """
    Vector-valued QoI used for testing of non-scalar QoI treatment: 
    Returns a vector with two identical components, 
    each of which is equal to the function output.
    """

    cname = "double"

    defaults_ = {
        "do_write" : False
         }

    def get_response(self,s=None): 
        """
        Takes solution u of QoI participants (i.e. solvers), 
        returns 2-component vector of them (see class description)
        """
        def double(a): 
            a_ext = np.array(a)[:,np.newaxis]
            return np.concatenate((a_ext,a_ext),axis=1)
        return [double(p.u) for p in self.participants]

    def write_to_file(self): 
        """
        writes mean and std deviation to file
        (mean and stddev are calculated by UqMethod,
        but stored as attribute of the QoI)
        """
        if self.do_write: 
            self.outfilename = "output_" + self.cname + ".csv"
            with open(self.outfilename,"w") as f: 
                f.write("mean stddev")
                for x, y in zip(self.mean,self.stddev): 
                    f.write("\n"+str(x)+" "+str(y))

    def integrate(self,qty): 
        return np.mean(qty)







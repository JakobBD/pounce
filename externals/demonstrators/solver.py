"""
Helper with core functions imported by batch and single example solvers.
The solver is mostly the same as the internal python solver. The code is simply copied.
"""
import sys 
import numpy as np 


def solver(model_name, n_points, xi): 
    if model_name == "Integration": 
        return f_integrate(model_name, n_points, xi)
    else: 
        return f_analytical(model_name, xi)


def f_analytical(model_name, xi):
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

    if model_name == "hf":
        # HF model can either contain all additional terms or none
        f = t0 #+ t1 + t2 + t3
        w_artificial = 500.
    elif model_name == "lf1": 
        f = t0 + t1 + t2
        w_artificial = 200.
    elif model_name == "lf2": 
        f = t0 + t1
        w_artificial = 30.
    elif model_name == "lf3": 
        f = t0 + t2
        w_artificial = 15.
    else: 
        Exception("invalid model name")
    return f, w_artificial/10000.


def f_integrate(model_name, n_points, xi):
    """
    First order numerical integration of y=pi*cos(pi*x) from -1 to xi 
    Exact solution is int y = sin(pi*xi)
    
    This allows to calculate the actual mean analytically for uniform disctributions, 
    used for convergence tests
    """
    dx = (1. + xi) / n_points
    x = np.linspace(-1.,xi-dx,n_points)
    # alternative: second order (mid-point rule)
    # x = np.linspace(-1.+dx/2.,xi-dx/2.,n_points)
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
    w_artificial = float(n_points**2)/10000.

    return int_y, w_artificial 

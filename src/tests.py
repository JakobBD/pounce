from helpers import config
from helpers.printtools import *
import numpy as np


def run_pounce_simple(prmfile):
    print_header()
    print_major_section("Start parameter readin and configuration")
    simulation = config.config(prmfile)
    simulation.run()
    return simulation

def general_tst(prmfile,mean_ref,stddev_ref,tol):
    sim = run_pounce_simple(prmfile)
    print("MEAN:  ", sim.mean)
    print("STDDEV:", sim.stddev)
    assert np.abs(sim.mean - mean_ref) < tol
    assert np.abs(sim.stddev - stddev_ref) < tol

def test_mlmc():
    prmfile    = "../ini/internal_local/parameter_mlmc.yml"
    mean_ref   = -0.03819458024853564
    stddev_ref = 0.6905427902794208
    tol = 1.E-10
    general_tst(prmfile,mean_ref,stddev_ref,tol)

def test_mfmc():
    prmfile    = "../ini/internal_local/parameter_mfmc.yml"
    mean_ref   = 0.022528934807061824
    stddev_ref = 0.691569022875092
    tol = 1.E-10
    general_tst(prmfile,mean_ref,stddev_ref,tol)

def test_sc():
    prmfile    = "../ini/internal_local/parameter_sc.yml"
    mean_ref   = 0.2101817993546256
    stddev_ref = 0.6743135688310626
    tol = 1.E-10
    general_tst(prmfile,mean_ref,stddev_ref,tol)

# global imports
import sys,os
import argparse

# local imports
from helpers import init

# parse commmand line arguments
parser = argparse.ArgumentParser(description='Python Propagation of Uncertainties')
parser.add_argument('prmfile',help='YAML input file')
args = parser.parse_args()

# read input 
uqMethod,machine,solver = init.Init(args.prmfile)

# run simulation
uqMethod.RunSimulation(machine,solver)

solver.Report()

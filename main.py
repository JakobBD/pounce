# global imports
import sys,os
import argparse
for subdir in os.walk(os.path.dirname(__file__)):
   sys.path.append ( os.path.join (os.path.dirname(__file__), subdir[0] ) )

# local imports
import init 

# parse commmand line arguments
parser = argparse.ArgumentParser(description='Python Propagation of Uncertainties')
parser.add_argument('prmfile',help='YAML input file')
args = parser.parse_args()

# read input 
uqMethod,machine,solver = init.Init(args.prmfile)

# run simulation
uqMethod.RunSimulation(machine,solver)

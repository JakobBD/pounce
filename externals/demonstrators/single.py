#!python3
"""
This is a wrapper for the minimal solver to demonstrate I/O via individual input files and Stdout. 
This is a fallback option for the batch version, if the latter cannot be generated or requires too much implementational effort
Usage: 

python3 single.py parameters.ini
"""

import sys
import numpy as np
import configparser

from solver import solver

# read input file
input_file_name = sys.argv[1]
parser = configparser.ConfigParser()
with open(input_file_name) as stream:
   parser.read_string("[DEFAULT]\n" + stream.read())
   config = parser["DEFAULT"]

# get parameters
project_name = config['ProjectName']
model_name = config['ModelName']
if model_name == "Integration": 
    n_points = int(config['nPoints'])
    assert n_points > 0
else: 
    n_points = None
xi = float(config["StochPrm"])

# Most parameters remain the same across different runs, 
# which is why we modify a default parameter file instead of 
# creating a new one from scratch for every sample.
dummy1 = config['DeterministicDummyPrm1']
dummy2 = config['DeterministicDummyPrm2']

# evaluate model
result, work_mean = solver(model_name, n_points, xi)

# print ouput
print("===OUTPUT===".format(result))
print("Result: {}".format(result))
print("Computation Time: {}".format(work_mean))




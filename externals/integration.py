import argparse
import numpy as np

def Function1(slope,offset,spacing):
   return slope*spacing+offset

def Function2(slope,offset,spacing):
   return slope*spacing**2+offset

parser = argparse.ArgumentParser(description='Integration of function with two input parameters')
parser.add_argument('-s','--slope'   ,help='Enter slope of function.')
parser.add_argument('-o','--offset'  ,help='Enter y-axis offset.')
parser.add_argument('-l','--level'   ,help='Enter discretization level.')
parser.add_argument('-cf','--coarsefine'  ,help='Enter discretization level.')
parser.add_argument('-p','--projectname',help='Enter projectname.')

args = parser.parse_args()
slope = float(args.slope)
offset= float(args.offset)
level = int(args.level)
spacing  = np.linspace(0.,10.,level*10)
cells    = len(spacing)-1
function = Function2(slope,offset,spacing)

integral =0.
for i in range(cells):
   integral = integral + (function[i+1]+function[i])/2.*(spacing[1]-spacing[0])

output = 'Integral: '+str(float(integral))
with open(args.projectname+'_l%d'%(level)+args.coarsefine+'.yml', 'w') as yamlFile:
   yamlFile.write(output)

import sys
import numpy as np

# syntax: python solver.py model xi

# function: 
# f(xi) = sin(pi*xi) + c1*sign(xi) + c2*sin(5*pi*xi) + c3*xi^3
# f(xi) = term 0     + term 1      + term 2          + term 3


model = sys.argv[1]
xi = float(sys.argv[2])

t0 = 1.0   * np.sin(np.pi * xi)
t1 = 0.1   * np.sign(xi)
t2 = 0.01  * np.sin(5. * np.pi * xi)
t3 = 0.001 * xi**3

if model == "hf": 
    f = t0 + t1 + t2 + t3
    w = 1.
elif model == "lf1": 
    f = t0 + t1 + t2
    w = 0.1
elif model == "lf2": 
    f = t0 + t1
    w = 0.02
elif model == "lf3": 
    f = t0 + t2
    w = 0.001
else: 
    sys.exit("invalid model name")

print("Result: {}".format(f))
print("Computation Time: {}".format(w))




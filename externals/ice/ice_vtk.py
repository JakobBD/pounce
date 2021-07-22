import h5py 
import numpy as np
import copy
import sys
# from matplotlib import pyplot as plt
from matplotlib import cm
import matplotlib._cntr as cntr
import csv 
import commons
from scipy.interpolate import CubicSpline,interp1d,interp2d,UnivariateSpline
import glob 
from matplotlib.collections import LineCollection
import meshio 
import pygmsh
import warnings
import subprocess




name_str    = sys.argv[1]
random_vars = sys.argv[2].split("_") # random distribution; normal(0.,1.,1) is correct, others improve stability
filename_ice = name_str+"_ICE.vtk"
filename_afl = name_str+"_AFL.vtk"


interp_spacing = 5E-4       # determines interpoaltion accuracy, not final spacing

min_ = np.minimum
max_ = np.maximum

def constrain_0to1(arr): 
    return min_(1.,max_(0.,arr))

def length(arr): 
    return np.linalg.norm(arr,axis = -1)

def add_dim(arr): 
    return arr.reshape(arr.shape + (1,))


# FILENAMES

# --------------------------------------------------------------------------------
# READ CLEAN AIRFOIL COORDS

path_afl = "report/airfoil.csv"
x_afl = commons.read_coords(path_afl)

# SHARP LEADING EDGE
# extrapolate
y_last = x_afl[-1,1]+(x_afl[-1,1]-x_afl[-2,1])/(x_afl[-1,0]-x_afl[-2,0])*(1.-x_afl[-1,0])
x_afl = np.concatenate((x_afl,np.array([[1.,y_last]])))
# adjust suction side
dy = x_afl[0,1]-y_last
h = x_afl.shape[0]//2 # leading edge int (roughly)
# sine ramping between x=0.3 and x=1.0
fac = 0.5-0.5*np.cos(np.pi*constrain_0to1((x_afl[h:,0]-0.3)/0.7))
x_afl[h:,1]+=fac*dy

# --------------------------------------------------------------------------------
# GET ICE SHAPE FROM MODES 

# read in modes
filename='modes.h5'
with h5py.File(filename, 'r') as h5f:
        avg = np.array(h5f['average'])
        modes = np.array(h5f['modes'])
        x = np.array(h5f['x'])
        y = np.array(h5f['y'])
X,Y = np.meshgrid(x,y)

assert len(random_vars) <= len(modes)

# linear combination
tmp = copy.deepcopy(avg)
for phii,modei in zip(random_vars,modes): 
    tmp += float(phii)*modei

# isoline / contour is ice outline
c = cntr.Cntr(X, Y, tmp)
nlist = c.trace(0., 0., 0)
segs = nlist[:len(nlist)//2][0]

# --------------------------------------------------------------------------------
# JOIN ICE SHAPE AND CLEAN AIRFOIL

# only use left (front) part of closed outline 
x_cut = 0.21
if segs[0,0] > x_cut: 
    i_use = np.argwhere(segs[:,0]<x_cut)
    il = i_use[0][0]
    iu = i_use[-1][0] 
    # add first and last points inside airfoil
    xl = [0.25, segs[il,1]]
    xu = [0.25, segs[iu,1]]
    segs = np.concatenate(([xl], segs[il:iu+1,:], [xu]))
else: 
    i_discard = np.argwhere(segs[:,0]>x_cut)
    il = i_discard[0][0]-1
    iu = i_discard[-1][0]+1
    # add first and last points inside airfoil
    xl = [0.25, segs[il,1]]
    xu = [0.25, segs[iu,1]]
    segs = np.concatenate(([xu], segs[iu:,:], segs[:il+1,:], [xl]))
if segs[0,1] > segs[-1,1]: 
    segs = np.flip(segs,axis=0)

# inperpolate both clean airfoil and ice outline  
x_ice = commons.interpolate(segs,spac=interp_spacing)
# alpha=0.5
# for i in range(10):
    # x_ice[1:-1,:] = (1.-alpha)*x_ice[1:-1,:] + alpha*0.5*(x_ice[2:,:]+x_ice[:-2,:])
x_afl = commons.interpolate(x_afl,spac=interp_spacing)

# use outermost of the two (ice thickness can't be negative)
# x_ice = commons.path_union(x_afl,x_ice)


# --------------------------------------------------------------------------------

n_ice = x_ice.shape[0]

# search nearest n(i) for each point i 
j_mindist = np.arange(n_ice)
for i in range(n_ice): 
    j_mindist[i] = commons.mindist(x_ice[i,:],x_afl)

j_min = np.minimum(j_mindist[1:],j_mindist[:-1])-1
j_max = np.maximum(j_mindist[1:],j_mindist[:-1])+1

# check intersection for i:i+1 and min(n(i),n(i+1))-1 : max(n(i),n(i+1)+1
# change sign for each intersection
inside = True
j_start = 0
segs = []
for i in range(n_ice-1): 
    for j in range(j_min[i],j_max[i]):
        if commons.do_intersect(x_ice[i,:],x_ice[i+1,:],x_afl[j,:],x_afl[j+1,:]): 
            if inside: 
                c1 = commons.x_intersect(x_ice[i:i+2,:],x_afl[j:j+2,:])
                i_start = i+1
                j_start = j+1
                inside = False
            else: 
                c2 = commons.x_intersect(x_ice[i:i+2,:],x_afl[j:j+2,:])
                inner = x_afl[j_start:j+1,:]
                outer = x_ice[i:i_start-1:-1,:]
                x_out=np.concatenate((c1,inner,c2,outer))
                segs.append(x_out)
                inside = True


# --------------------------------------------------------------------------------


# write mesh 

geom = pygmsh.built_in.Geometry()


# x_write = x_afl
# x_write = segs
for x_write in segs: 

    x_write = np.concatenate((x_write, 0.*x_write[:,0:1]),axis=-1)

    poly = geom.add_polygon(x_write)


    geom.set_transfinite_lines(poly.lines, 1)

    zunit = [0., 0., 1.]
    top,vol,lat = geom.extrude(poly.surface,translation_axis=zunit,num_layers=1,recombine=True)

    geom.add_physical(vol)

mesh = pygmsh.generate_mesh(geom)

meshio.write(filename_ice,mesh,file_format='vtk')

# --------------------------------------------------------------------------------


# write mesh 

geom = pygmsh.built_in.Geometry()


x_write = x_afl[::5,:]

x_write = np.concatenate((x_write, 0.*x_write[:,0:1]),axis=-1)

poly = geom.add_polygon(x_write)


geom.set_transfinite_lines(poly.lines, 1)

zunit = [0., 0., 1.]
top,vol,lat = geom.extrude(poly.surface,translation_axis=zunit,num_layers=1,recombine=True)

geom.add_physical(vol)

mesh = pygmsh.generate_mesh(geom)

meshio.write(filename_afl,mesh,file_format='vtk')

"""
This is a minimal solver to demonstrate the batch strategy of pounce, where several sample evaluations are grouped into a common program execution with a common I/O, which evaluates the samples both sequentially and in parallel.
I/O is done completely with h5py.
Usage: 

python3 batch.py Input.h5
"""

from mpi4py import MPI
import h5py
import sys
import numpy as np

from solver import solver

#---------------------------------------------------------------------------------------------------

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
global_root = rank == 0
size = comm.Get_size()

if global_root: 
    print("Start minimal batch solver...")

input_file_name = sys.argv[1]


#---------------------------------------------------------------------------------------------------

def read_xi():
    """ 
    """
    if global_root:
        with h5py.File(input_file_name, 'r') as h5f: 
            dset = h5f['Samples']
            start = i_sequential*n_parallel
            xi_vec = list(dset[start:start+n_parallel])
    else:
        xi_vec = None
    xi = root_comm.scatter(xi_vec, root=0)
    return xi

#---------------------------------------------------------------------------------------------------

def write_output():
    """ 
    Write output to HDF5 file. For simplicity, parallel HDF5 is not used here. 
    Instead, data is sent to and written by MPI root.
    """
    all_results = root_comm.gather(result, root=0)
    if global_root:
        if i_sequential == 0: 
            with h5py.File(output_file_name, 'w') as h5f: 
                h5f.create_dataset('Result', (n_samples,))
                h5f.attrs['ProjectName'] = project_name
                h5f.attrs['WorkMean'] = work
                h5f.attrs['nSamples'] = len(samples)
        with h5py.File(output_file_name, 'r+') as h5f:
            dset = h5f['Result']
            start = i_sequential*n_parallel
            dset[start:start+n_parallel] = all_results


#---------------------------------------------------------------------------------------------------
# Read input from HDF5 file. For simplicity, parallel HDF5 is not used here. 
# Instead, data is read by MPI root and communicated to other procs. 

if global_root:
    with h5py.File(input_file_name, 'r') as h5f: 
        project_name = h5f.attrs['ProjectName']
        model_name   = h5f.attrs['ModelName']
        n_samples    = h5f.attrs['nSamples']
        n_parallel   = h5f.attrs['nParallelSamples']
        if model_name == "Integration":
            n_points = h5f.attrs['nPoints']
            assert n_points > 0
        else: 
            n_points = 0
else:
    project_name = None
    model_name   = None
    n_points     = None
    n_samples    = None
    n_parallel   = None
project_name = comm.bcast(project_name, root=0)
model_name   = comm.bcast(model_name,  root=0)
n_points     = comm.bcast(n_points,     root=0)
n_samples    = comm.bcast(n_samples,    root=0)
n_parallel   = comm.bcast(n_parallel,   root=0)

# One sample evaluation can run in parallel, although in this dummy solver, 
# this means in practice that only the first process of this simulation does anything.
# If the number of ranks is not a multiple of the number of parallel sample evaluations, 
# The first few sample evaluations get one rank more than the last.
simu_size = size // n_parallel
n_remain = size - n_parallel*simu_size
simu_size = simu_size + 1 
offset = 0
for i_parallel in range(n_parallel): 
    if i_parallel == n_remain: 
        simu_size = simu_size - 1 
    offset_next = offset + simu_size
    if rank < offset_next: 
        break 
    offset = offset_next
internal_rank = rank - offset
is_simu_root = internal_rank == 0
i_parallel = i_parallel

if simu_root: 
    root_comm = comm.Split(0, rank)
else: 
    comm.Split(MPI.UNDEFINED, rank)
    sys.exit()

#---------------------------------------------------------------------------------------------------

# round up
n_sequential = (n_samples-1) // n_parallel + 1 
output_file_name = project_name + "_results.h5"

# Loop over sequential sample evaluations.
for i_sequential in range(n_sequential): 

    # If the number of sample evaluations is not a multiple of n_parallel, 
    # A few processes will idle during the last sequential run.
    if i_sequential == n_sequential-1: 
        n_remain = n_samples - n_parallel*(n_sequential-1)
        has_remain = i_parallel < n_remain
        if has_remain: 
            root_comm = root_comm.Split(0, rank)
            n_parallel = n_remain
        else: 
            root_comm.Split(MPI.UNDEFINED, rank)
            sys.exit()

    # MAIN WORK IS DONE HERE 
    xi = read_xi()
    result, work_mean = solver(model_name, xi)
    write_output()

#---------------------------------------------------------------------------------------------------

if global_root: 
    print("...Minimal batch solver finished.")


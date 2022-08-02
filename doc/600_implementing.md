# Implementing your own solver and machine API 

## Solver 

Each solver specification is located in an own file. To add a new one, just copy one of the existing ones (preferably one of the 'demonstrator' solvers), adapt class name and the 'cname' parameter in the class, and you are done. The new solver can now be used by giving its 'cname' as the '_type' parameter in the yaml file. 

In a next step, adapt how the solver interacts with PoUnce, i.e. how stochastic input is passed to the solver (in the 'prepare' routine) and how to check whether sample computation was successful (in the 'check_finished' routine).

Finally, adapt which quantities of interest are included, and how their output should be passed to PoUnce ('get_response' routine).

### Demonstrator solvers

Two solvers are implemented to demonstrate how such an interaction can be implemented both in PoUnce and the solver. The corresponding external solvers are located in the 'externals/demonstrators' folder. 

- **demontrator_single**: This is an example of communication with a standard solver, which may be very close to existing solvers and does not require changes to the solver, but also does not exploit the possible performance benefits of the PoUnce strategy. All samples are run as separate program executions. PoUnce creates an ini file for each individual solver. The solver output is written to stdout, from where it is read by a PoUnce QoI. This implementation produces large numbers of files if many samples are involved. 
- **demontrator_batch**: This is an example of how to avoid large file numbers and process placement times by combining all samples of one model and iteration into one program execution with a common file I/O. This requires some changes to the solver: Several runs must be placed in parallel in an umbrella MPI communicator, and a loop is added around program execution for several sequential runs. In this example, stochastic input is passed to the batch via HDF5 (in an array with one entry per sample), and output is also written to an HDF5 file, which is a very good option for structured parallel I/O.

## Machine

Each machine specification is also located in an own file. To add a new one, just copy one of the existing ones (using 'Hawk' as a starting point is recommended'), adapt class name and the 'cname' parameter in the class, and you are done. The new solver can now be used by giving its 'cname' as the '_type' parameter in the yaml file. 

In a next step, adapt the functions in the class to the new machine. Specifically: 

- Adapt the **allocate_resources** routine to specify how many nodes and how much walltime should be reserved for a job, and how many parallel and sequential samples should be used for a batch of samples. This routine should consider details about the new cluster such as cores per node, maximum number of nodes, a reasonable trade-off between walltime and number of nodes, and other constraints of the machine.
- Adapt the **run_batches** routine to the resource management system (for Hawk, PBS Pro is implemented). In particular, the subroutines **submit_job** and **read_qstat** should be adapted.  


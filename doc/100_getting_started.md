# Getting started

Required Python packages are given in `src/requirements.txt`.

Runs are configured using a YAML input file. Example input files are located in the `ini` folder.

For a test run, go to `ini/internal_local` and run 

```
python3 ../../src/pounce.py parameter_mlmc.yml
```

## Parameters

The basic syntax for a PoUnce run is
```
python3 <path/to>/src/pounce.py <path/to/parameter_file>.yml
```
Output files will be located in the current working directory, so it is best to copy a parameter file to an empty directory and start pounce from there.

Example YAML parameter files are located in the `ini` directory, where the structure is demonstrated. 

Files in the `demonstrator_XY` directories can be run out of the box and are included in the GitHub action regression tests (see also below).
The ice directory contains a complex application case, which needs additional parameter files and adapted codes.

Files in the directory `demonstrator_batch_local` are commented. 
In addition, the file `parameter_mfmc.yml` in the ice subdirectory has comments on additional parameters, which are not used in the simple test examples.

All parameters with their defaults are also listed in each class in the code.

Each parameter file contains the sections given in the following table. Most sections contain the "type" parameter which chooses the subclass to be used, and further parameters specifying its setup. 

| section           | description                                           |
|------------------:|-------------------------------------------------------|
| `general`         | General settings like the project name and whether    |
|                   | or not to save intermediate states of PoUnce.         |
| `uq_method`       | UQ method to be used and general parameters about     |
|                   | its configuration (such as the computational budget). | 
| `sampling`        | Configuration of the sampling method, such as         |
|                   | polynomial degree for polynomial chaos expansion or   |
|                   | fixed seed of the random number generator for Monte   |
|                   | Carlo.                                                |
| `solver`/`models` | Setup of the baseline solver(s); In some methods with | 
|                   | different levels/fidelities. The section is called    |
|                   | `models` in Multifidelity Monte Carlo to rreflect     |
|                   | that several different baseline solvers can be        |
|                   | combined here.                                        |
| `stoch_vars`      | A list of the used uncertain parameters including     |
|                   | their distribution type and defining parameters       |
| `machine`         | Choice and setup of the machine that the run is       |
|                   | performed on, such as a cluster or a local machine.   |
|                   | Several machines can be listed and assigned to        |
|                   | several parts of the simulation.                      |
| `qois`            | A list of the quantities of interest (QoIs) which are |
|                   | evaluated. Several QoIs can be evaluated in one run.  | 


## Tests

The current pipeline contains 9 regression tests covering different functionalities of the code.
All tests can be invoked from the `ini` folder with the command 
```
pytest ../src/tests.py
```
The tests are all designed to run on a `local` machine, i.e. without a scheduler. The nine tests cover all combinations of three deterministic baseline solvers (`demonstrator_batch`, `demonstrator_single` and `internal`) and three UQ methods they use (`pce`, `mlmc` and `mfmc`). For details on machines, deterministic solvers and UQ methods, see the 'Features' section of this documentation. 

The requirement for sucessful termination of each test is that the resulting mean and standard deviation equal reference values given in `src/tests.py` (To achieve reproducible results in the Monte Carlo simulations, the parameter `fixed_seed` in the parameter files is used to manually set the seed of the random number generator).

Each test can also be run as an individual PoUnce run (with the syntax shown above). The according nine parameter files are located in the ini folder in the subdirectories `demonstrator_batch_local`, `demonstrator_single_local` and `internal_local`.

## Restart

PoUnce runs can be aborted at (almost) any time. Since its state is written regularly at checkpoints, it can then be restarted from the last state with the command

```
python3 ../../src/pounce.py -r 
```
The restart capability is especially important due to the intermittent queuing times in the present scheduling strategy, which is outlined below.

There is a routine in the file helpers/config.py, which can be used to modify parameters in a restart. To do this, the user needs to be familiar with the data structure within PoUnce, and therefore the source code. Restarting from a modified parameter file is a possible future extension, but not yet implemented.

## Command line tool 

PoUnce can be made a command line tool. This makes working with it more convenient, but is optional.
This feature can be enables with the command 
```
make cmdline 
```
run from the main PoUnce directory. PoUnce can then be run from every folder without specifying the path to the python file and without the leading `python3`. An example command thus becomes
```
pounce parameter_mlmc.yml
```


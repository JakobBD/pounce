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

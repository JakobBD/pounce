# Getting started

Required Python packages are given in `src/requirements.txt`.

Runs are configured using a YAML input file. Example input files are located in the `ini` folder.

For a test run, go to `ini/internal_local` and run 

```
python3 ../../src/pounce.py parameter_mlmc.py
```

## Parameters

Example YAML parameter files are located in the ini directory, where the structure is demonstrated. 

Files in the demonstrator_XY directories can be run out of the box and are included in the github action regression tests.
The ice directory conatains a complex application case, which needs additional parameter files and adapted codes.

Files in the demonstrator_batch_local directory are commented. 
In addition, the file parameter_mfmc.yml in the ice subdirectory has comments on additional parameters, which are not used in the simple test examples.

All parameters with their defaults are also listed in each class in the code.

## Restart

PoUnce runs can be aborted at (almost) any time. Since its state is written regularly at checkpoints, it can then be restarted from the last state with the command

```
python3 ../../src/pounce.py -r 
```
The restart capability is especially important due to the intermittent queuing times in the present scheduling strategy, which is outlined below.

There is a routine in the file helpers/config.py, which can be used to modify parameters in a restart. To do this, the user needs to be familiar with the data structure within PoUnce, and therefore the source code. Restarting from a modified parameter file is a possible future extension, but not yet implemented.

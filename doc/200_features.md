# Features and detailed parameter description

In this chapter, features of PoUnce are given and their configuration and use in the parameter files is explained. Please also refer to the explanations in the example parameter files in the `ini/demonstrator_batch_local` directory as well as `ini/ice/parameter_mfmc.yml`.

## UQ methods

PoUnce currently features three UQ methods. They are configured via the `uq_method` and `sampling` sections of the parameter file: 

- **The non-intrusive polynomial chaos method (`_type: pce)`:** This method is implemented based on the ChaosPy [@ChaosPyFeinberg2015] package. The polynomial degree can be changed via `poly_deg` in the `sampleing` section of the parameter file. It includes the possibility of using sparse grids (`sparse_grid: true` in the `sampling` section). Since this method in its basic form only requires one iteration of sample simulations of similar computational cost, the implementation is simple and can be easily extended to more advanced methods, such as adaptive sparse grids. 
- **The multilevel Monte Carlo method (`_type: mlmc)`:** If this method is run with two iterations (computing pilot samples in a first iteration and the rest of an approximately optimal number of samples in the second; achieved by setting `n_max_iter: 2` in the `uq_method` section), it corresponds to the standard MLMC method as described in [@Giles2008] with a fixed set of resolution levels. However, in the implemented version, more iterations (usually three or four) can be used to carefully approach the optimal number of samples on every level while updating the estimates of these optimal numbers. This avoids overshooting the optimal sample numbers based on inaccurate estimates. To calculate the number of samples in the intermediate iterations, a heuristic approach based on the current and the optimal number of samples can be used (`use_ci: False`), or a method based on confidence intervals described in Detail in [@Beck2020], (`use_ci: True`). Either the `total_work` or the estimated stochastic error (`eps`) can be prescribed the other is then optimized. If the MLMC method is used, further sections of the parameter file are affected: In `sampling`, `fixed_seed: True` can be used to achieve the same results with the random number generator in every run which makes results reproducible. The `solver` section contains the additional parameter `n_warmup_samples` which determines the number of samples on every level in the first iteration. It is given in this section so that different values can be specified for each level. One of the `qois` gets and additional parameter `optimized`, which determines which QoI is used to optimize the sample number on every level. 
- **The multifidelity Monte Carlo method (`_type: mfmc)`:** The method is implemented following [@Peherstorfer2016], with the additional option to re-use pilot samples for the eventual estimators (`reuse_warmup_samples: True`) and to base estimation of optimal control variate coefficients on samples of both iterations (`update_alpha: True`). In MFMC, only the `total_work` can be described as in the original publication. In MFMC, `n_warmup_samples` are equal for every model and are therefore a parameter in the `uq_method` section. Again, `fixed_seed: True` can be set in the `sampling` section and one QoI in `qois` must get the `optimize: True` addition to optimize sample numbers and control variate coefficients on this QoI.

## Baseline solvers

PoUnce currently features adapters to the following solvers, which are configured in the `solver` or `models` section, depending on the UQ method: 

- Two external dummy Python solvers to demonstrate different strategies for interaction with baseline solvers (`_type: demonstrator_single` and `_type: demonstrator_batch`). Either the baseline codes can be adapted to this way of interaction, or the according adapters in PoUnce. The external dummy solvers are included in the repository in the `externals/demonstrators` folder. Further documentation is given in the source files of the solvers. 
- In internal Python dummy solver for testing of the UQ methods (`_type: internal`). It avoids spawning subprocesses for sample calculations, which makes execution faster.
- A version of the open-source flow solver FLEXI\footnote{\url{http://flexi-project.org}} [@Krais2019] adapted for UQ simulations (`_type: flexibatch`). The solver can be found in [https://github.com/flexi-framework/flexi-extensions/tree/pounce](https://github.com/flexi-framework/flexi-extensions/tree/pounce); Furthermore, an extended version of this code adapted for a study on airfoil icing detailed below, which is located in the same GitHub repository (`_type: ice`). 
- The educational flow solver CFDFV, which is located in [https://github.com/flexi-framework/cfdfv](https://github.com/flexi-framework/cfdfv); (`_type: cfdfv`).
- Surrogate models. In particular, linear interpolation and Kriging [@Krige1951] are implemented (`_type: kriging`).

Baseline solvers are configured in the `solver` section of the parameter file. In MLMC, A `levels` list can specify parameters separately for individual resolution levels. Every parameter which is given outside this list is valid for all levels. In MFMC, the `solver` section is renamed to `models` to reflect that different baseline solvers can be chosen. Instead of `levels`, a list of `fidelities` is included following the wording of the literature. For all external solvers, and `exe_path` is specified. Moreover, several parameters (`solver_prms`) can be passed to the solver, for example to distinguish between levels. This does not include the uncertain parameters, which are handled separately. In MFMC, each of the `fidelities` gets a `name` to distinguish between low fidelity models. 

## QoIs

Several QoIs can be specified which are then all evaluated within one run. They are implemented separately along each baseline solver in the same source file. They are defined by a `_type` given in the source file implementation and possibly further parameters, depending on the implementation. 

## HPC clusters 

PoUnce includes the interaction with cluster software. In particular, this means determining the required resources (number of nodes and wall time), generating a job script, submitting it to a scheduler, and monitoring its status. The following clusters are implemented (specified in the `machines` section of the parameter file): 

- A non-scheduling-based computer (`_type: local`). Assumes that compute resources can be accessed directly without submitting a job request. 
- The 'Hawk' cluster at HLRS Stuttgart (`_type: hawk`). It is based on the PBSPro batch system. The ideal parameters for resource use are tailored to this specific system, but can be easily adapted. An extension to other schedulers such as Slurm is also easily possible.

Different parts of a simulation can be run on different machines. Details are given below Under 'Stages'.

## Parallelization

As a parameter for each machine, the parallelization type can be given. Three options are available: `none` (run all samples in sequential), `mpi` (run all samples in one batch, which assumes a modified solver adapted to this task) and `gnu` for parallel sample executions with separate executable runs and I/O based on GNU parallel. Further details are given in the Scheduling chapter.

## Random distributions

PoUnce allows an infinite number of independent random input parameters, whose distributions can be chosen individually as a list in the `stoch_vars` section. Currently, normal (`_type: normal`) and uniform (`_type: uniform`) distributions are featured. Normal distributions are defined by the parameters `mean` and `standard_deviation`, uniform distributions by two `bounds` given as a list.

## Stages

Practical baseline simulation workflows are often comprised of several steps with vastly different cost and characteristics, such as a main simulation along with pre- and post-processing steps. In PoUnce, these steps are called `stages`. See also the Workflow chapter. Parameters can be passed separately for each stage of a solver by adding a `stages` list to the `solver` section. Parameters given outside this list are passed for every stage. If parameters vary both by stage and level/fidelity, the lists can be nested in either order. 

Different parts of a simulation can be run on different machines. For example, the main simulation can be run on a cluster and post-processing on a local machine. 
 To this end, the `machine` section can be given as a list. The different machine configurations are then assigned to the stages via the list `main_stages` in the `general` section, where each stage gets a `name` and the `machine` to be used for this stage as a parameter. Normally, each stage requires its own adapter in the `solver` directory. As an example for implementation and use, see the adapter source file `src/solver/ice.py` and the parameter file in `ini/ice/parameter_mfmc.yml`.

## General Settings

General settings are given in the `general` section of the parameter file. The `project_name` determines naming of most output files and some stdout. PoUnce can be restarted. To this end, its state is written to a `Python pickle` file after each sub-step if `do_pickle: True` is set. 

## Extension
 
Due to its strictly modular design, the framework can be easily extended by new options for each of these modules, if, for example, a new HPC cluster is present. 

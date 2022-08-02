# Features


## UQ methods

PoUnce currently features three UQ methods: 

- **The non-intrusive polynomial chaos method:** This method is implemented based on the ChaosPy [@ChaosPyFeinberg2015] package and includes the possibility of using sparse grids. Since this method in its basic form only requires one iteration of sample simulations of similar computational cost, the implementation is simple and can be easily extended to more advanced methods, such as adaptive sparse grids. 
- **The multilevel Monte Carlo method:** If this method is run with two iterations (computing pilot samples in a first iteration and the rest of an approximately optimal number of samples in the second), it corresponds to the standard MLMC method as described in [@Giles2008] with a fixed set of resolution levels. However, in the implemented version, more iterations (usually three or four) can be used to carefully approach the optimal number of samples on every level while updating the estimates of these optimal numbers. This avoids overshooting the optimal sample numbers based on inaccurate estimates. Details on the method can be found in [@Beck2020]. 
- **The multifidelity Monte Carlo method:** The method is implemented following [@Peherstorfer2016], with the additional option to re-use pilot samples for the eventual estimators.

## Baseline solvers

PoUnce currently features adapters to the following solvers: 

- Two external dummy Python solvers to demonstrate different strategies for interaction with baseline solvers. Either the baseline codes can be adapted to this way of interaction, or the according adapters in PoUnce. The external dummy solvers are included in the repository. 
- In internal Python dummy solver for testing of the UQ methods. It avoids spawning subprocesses for sample calculations, which makes execution faster.
- A version of the open-source flow solver FLEXI\footnote{\url{http://flexi-project.org}} [@Krais2019] adapted for UQ simulations. The solver can be found in [https://github.com/flexi-framework/flexi-extensions/tree/pounce](https://github.com/flexi-framework/flexi-extensions/tree/pounce); Furthermore, an extended version of this code adapted for a study on airfoil icing detailed below, which is located in the same GitHub repository. 
- The educational flow solver CFDFV, which is located in [https://github.com/flexi-framework/cfdfv](https://github.com/flexi-framework/cfdfv).
- Surrogate models. In particular, linear interpolation and Kriging [@Krige1951] are implemented.

## HPC clusters 

PoUnce includes the interaction with cluster software. In particular, this means determining the required resources (number of nodes and wall time), generating a job script, submitting it to a scheduler, and monitoring its status. The following clusters are implemented: 

- A non-scheduling-based computer with the name 'local'. Assumes that compute resources can be accessed directly without submitting a job request. 
- The 'Hawk' cluster at HLRS Stuttgart. It is based on the PBSPro batch system. The ideal parameters for resource use are tailored to this specific system, but can be easily adapted. An extension to other schedulers such as Slurm is also easily possible.

Different parts of a simulation can be run on different machines. For example, the main simulation can be run on a cluster and post-processing on a local machine.

## Extension

Due to its strictly modular design, the framework can be easily extended by new options for these modules, if, for example, a new HPC cluster is present. 

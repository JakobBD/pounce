# POUNCE

POUNCE (Propagation Of UNCErtainties) is a framework fully automatized runs of non-intrusive forward UQ simulations. 
It is designed for efficiency on HPC clusters. It is written in object-oriented Python. 
For details about the scheduling approach, please refer to the reference given below.

POUNCE is suited to be customized by users and tailored to their needs. Users are advised to familiarize themselves with the source code prior to use. 
Extending the code and adding an API for your own baseline solver and cluster/scheduler is therefore comparatively simple due to the light-weight nature  and modular design of POUNCE.

POUNCE therefore hopes to head-start for your own UQ implementation.

## Reference / Please cite

TODO (Reference Paper Also contains design paradigms)

## Basic code design

Usage and code structure are interdependent. 
The setup of pounce is modular. For different modules of the code, the user can choose between different module versions or add new ones. These include: 
* The used UQ method
* The baseline solver(s) for model evaluations at sample points
* Quantities of interest which are evaluated for each model. Several QoIs can be evaluated in the same simulaion.
* The machines that computations are carried out on
* Random variables with different distributions

One UQ simulation can include several solvers (for example as low-fidelity models in MFMC) and different parts of the baseline model (such as pre- and post-processing along the main simulations) can be run on different machines or with different machine configurations (such as to run post-processing tasks on fewer cores)

Each of these code modules is realized as a class. Each module thus contains a parent with the common functionality and interfaces, and a subclass for each of the module versions. For example, there is a UQMethod class and sub-classes of it for each of the different UQ methods such as MLMC and MFMC. 

POUNCE runs are configured using a YAML input file. For each code module, the sub-class is chosen according to its name (e.g. the UQ method sub-class is chosen be specifying the name of the sub-class. Parameters can be specified for each of these classes. Defaults for these parameters are given in each parent class, which can be overwritten by the respective sub-classes and finally by the user in the YAML file. The setup mechanism including choosing the sub-class by name and determining defaults are handled by a BaseClass, which is a common parent to most class in POUNCE.

The main program is located in the file pounce.py. It calls a config routine in the helpers/config.py file. This routine sets up the classes and their configuration. The driver class is the UQ method class, which is therefore set up first. This main class also contains a method called run, which is called from the main program after the setup and executes the whole UQ simulation. As parts of the class layout are dependent on the UQ method which is used (for example, different solvers may be necessary in MFMC, but not in polynomial chaos), parts of the conifg routine are located in the respective QqMethod sub-classes.


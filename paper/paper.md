---
title: 'PoUnce: A framework for automized uncertainty quantification simulations on high-performance clusters'
tags:
  - Uncertainty quantification
  - High performance computing
  - Python
  - Mulitlevel Monte Carlo
  - Multifidelity Monte Carlo
authors:
  - name: Jakob Duerrwaechter
    orcid: 0000-0001-8961-5340
    corresponding: true # (This is how to denote the corresponding author)
    affiliation: 1
  - name: Thomas Kuhn
    affiliation: 1
  - name: Fabian Meyer
    affiliation: 1
  - name: Andrea Beck
    affiliation: "1, 2"
  - name: Claus-Dieter Munz
    affiliation: 1
affiliations:
 - name: Institute of Aerodynamics and Gas Dynamics, University of Stuttgart, Germany
   index: 1
 - name: The Laboratory of Fluid Dynamics and Technical Flows, Otto von Guericke University Magdeburg, Germany
   index: 2
date: 11 July 2022
bibliography: paper.bib

# Optional fields if submitting to a AAS journal too, see this blog post:
# https://blog.joss.theoj.org/2018/12/a-new-collaboration-with-aas-publishing
# aas-doi: 10.3847/xxxxx <- update this with the DOI from AAS once you know it.
# aas-journal: Astrophysical Journal <- The name of the AAS journal.
---

# Summary

PoUnce (Propagation Of UNCErtainties) is a framework fully automatized runs of non-intrusive forward UQ simulations on high-performance computers.
In uncertainty quantification (UQ), some physical input parameters are not known precisely, but are uncertain with a given random distribution. In non-intrusive UQ methods, a standard simulation model is evaluated several times with different input parameter values and the model ouputs are post-processed to obtain information about the output quantity of interest (QoI). In Multilevel Monte Carlo [@Heinrich2001; @Giles2008] and Multifidelity Monte Carlo [@Peherstorfer2016; @Peherstorfer2018] methods, different models with vastly different cost and fidelity are combined. The number of evaluations with each model is usually determined adaptively and iteratively during simulation runtime.

Pounce serves as a connecting piece between UQ methods, simulation codes, and cluster software. 
An adapter can be written to existing baseline simulation codes to run UQ simulations with them.
The framework is designed to generate simulation input for each single model evaluation, schedule and run all model evaluations on a high-performance computing cluster, and post-process their results.

# Statement of need

Uncertainty Quantification has become a central tool over the last years to increase reliability in numerical simulations across a wide range of scientific fields. It captures simulation input data as a potential source of error. 

Most existing UQ toolkits rather focus on the methods themselves, rather than providing an integrated framework for fully automatized UQ runs. Some provide basic scheduling capabilities, which entail, however, several performance bottlenecks, as outlined below. PoUnce closes this gap and provides the following features which are not provided by other packages:

- **Focus on Multilevel and Multifidelity Monte Carlo methods**: These methods entail 
- **Integration and automatization:** A large-scale UQ simulation involves many individual steps, which are usually carried out separately by hand: Stochastic input generation for sample simulations, determining the required HPC resources, interaction with a HPC scheduler, extracting post-processed quantities of interest from the sample simulations ansd stochadstic evaluation. In some methods, these steps evene have to be carried out several times in an iterative loop. Contrary to other packages, PoUnce fully automatizes these runs, such that they can be executed with one single command. 
- **Efficiency on HPC clusters:** Non-intrusive UQ simulations consist of large numbers of smaller sample simulations. This is particularly the case in Multilevel and Multifidelity Monte Carlo simulations, where the cost between the computationally least and most expensive sample simulations can differ by many orders of magnitude. HPC clusters are not designed for this ind of applications, which entails efficiency bottlenecks, if no measures are taken to prevent them. This includes I/O bottlenecks due to very large numbers of relatively small files, as well as sub-optimal simulation-internal scheduling and idle times. PoUnce overcomes these issues by grouping large numbers of sample simulations into a commmon program execution with a common file I/O. Furthermore, in the interaction with theHPC scheduler, separate large-scale compute jobs are used for sample simulations of similar size, and post-processing is performed outside of these large compute jobs. This makes internal scheduling much more efficient and reduces idle times. Details can be found in the code documentation. 
- **Potential for extension**: The modularity of PoUnce together with its very compact source code lower the threshold to extend the code and daptat it to every user's individual needs. This includes adding adapters to new source codes, adapting interaction with new HPC clusters, and adding new UQ methods. Since users base UQ simulations on their own baseline codes and use different clusters, this modulairtyand extensibility is vital.

# Features

## UQ methods

PoUnce currently features three UQ methods: 

- **The non-intrusive polynomial chaos method:** This method is implemented based on the ChaosPy (todo: CITE) package and includes the possibility of using sparse grids. Since this method in its basic form only requires one iteration of sample simulations of similar computational cost, the implementation is simple and can be easily extended to more advanced methods, such as adaptive sparse grids. 
- **The Multilevel Monte Carlo method:** If this method is run with two iterations, it corresponds to the standard MLMC method as described in [@Giles2008] with a fixed set of resolution levels. More iterations can be used to carefully approach the optimal number of samples on every level while updating the estimates of these optimal numbers. This avoids overshooting the optimal sample numbes based on inaccurate estimates. Details on the method can be found in [@Beck2020]. 
- **The Multifidelity Monte Carlo method:** The method is implemented following [@Peherstorfer2016], with the additional option to re-use pilot samples for the eventual estimators.

More details on the methods can be found in the documentation.

## Baseline solvers

PoUnce currently features adapters to the following solvers: 

- Two external dummy Python solvers to demonstrate different strategies for interaction with baseline solvers. Either the baseline codes can be adapted to this way of interaction, or the according adapters in PoUnce. The external dummy solvers are included in the repository. 
- In internal Python dummy solver for testing of the UQ methods. It avoids spawning subprocesses for sample calculations.
- A version of the open-source flow solver FLEXI\footnote{\url{http://flexi-project.org}} [@Krais2019] adapted for UQ simulations. The solver can be found in [https://github.com/flexi-framework/flexi-extensions/tree/pounce](https://github.com/flexi-framework/flexi-extensions/tree/pounce); Furthermore, an extensded version of this code adapted for a study on airfoil icing etailed below, which is located in the same GitHub repository. 
- The educational flow solver CFDFV, which is located in [https://github.com/flexi-framework/cfdfv](https://github.com/flexi-framework/cfdfv).
- Surrogate models. In particular, linear interpolation and Kriging [@Krige1951] are implemented.

## HPC clusters 

PoUnce includes the interaction with cluster software. In particular, this means determining the required resources (numberof nodes and walltime), generating a job script, submitting it toa scheduler, and monitoring its status. The following clusters are implemented: 

- A non-scheduling-based computer with the name 'local'. Assumes that compute resources can be accessed directly without submitting a job request. 
- The 'Hawk' cluster at HLRS Stuttgart. It is based on the PBSPro batch system. The ideal parameters for resource use are taileored to this specific system, but can be easily adapted. An extension to other schedulers such as slurm is also easily possible.

Different parts of a simulation can be run on different machines. For example, the main simulation can be run on a cluster and post-processing on a local machine.

# Research based on PoUnce

Studies on uncertainty quantification for cavity aeroacoustics [@Kuhn2018] as well as on hp-MLMC methods [@Beck2020] are based on earlier versions of this software. A publication on uncertainty quantification for iced airfoil performance based on a recent version of the software is currently in preparation. 

# Acknowledgements

The development of PoUnce was funded by the Elisabeth and Friedrich Boysen Foundation.

PoUnce makes use of several libararies which we would like to acknowledge. This includes GNU parallel [@Tange2011a], chaospy [@ChaosPyFeinberg2015] and pyKriging [@Paulson2015].

# References

---
title: 'PoUnce: A framework for automatized uncertainty quantification simulations on high-performance clusters'
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

# Summary

PoUnce (Propagation Of UNCErtainties) is a framework fully automatized runs of non-intrusive forward uncertainty quantification (UQ) simulations on high performance computers.

In UQ, some physical input parameters are not known precisely, but are uncertain with a given random distribution. In non-intrusive UQ methods, a standard simulation model is evaluated several times with different input parameter values and the model outputs are post-processed to obtain information about the output quantity of interest (QoI). In Multilevel Monte Carlo [@Heinrich2001; @Giles2008] and Multifidelity Monte Carlo [@Peherstorfer2016; @Peherstorfer2018] methods, different models with vastly different cost and fidelity are combined. The number of evaluations with each model is usually determined adaptively and iteratively at simulation runtime.

Pounce enables UQ simulations with a computational cost that requires high performance computing (HPC) clusters. It serves as a connecting piece between UQ methods, simulation codes, and cluster software. 
The framework is designed to generate simulation input for each single model evaluation, schedule and run all model evaluations on the cluster, and post-process their results. It can be easily adapted to individual needs, such as new means of interaction with different baseline simulation codes. 

# Statement of need

Uncertainty Quantification has become a central tool over the last years to increase reliability in numerical simulations across a wide range of scientific fields. It captures simulation input data as a potential source of error. 

Most existing UQ tool kits (such as The Dakota toolbox [@Dakota] is the most prominent, other examples include the UQ toolkit [@DebusscherePCE2004,DebusschereUQTk2017], UQpy [@Olivier2020], PyMLMC [@PyMLMCSukys2017], ChaosPy [@ChaosPyFeinberg2015], UQLab [@Marelli2014] and UQit [@Rezaeiravesh2021b]) often provide a large variety of UQ methods, but generally do not provide an integrated framework for fully automatized UQ runs. Some provide basic scheduling capabilities, which entail, however, several performance bottlenecks, as outlined below. PoUnce closes this gap and provides the following capabilities which are not provided by other packages:

- **Integration and automatization:** A large-scale UQ simulation involves many individual steps, which are usually carried out separately by hand: Stochastic input generation for sample simulations, determining the required HPC resources, interaction with a HPC scheduler, extracting post-processed quantities of interest from the sample simulations and stochastic evaluation. In some methods, these steps even have to be carried out several times in an iterative loop. Contrary to other packages, PoUnce fully automatizes these runs, such that they can be executed with one single command. 
- **Efficiency on HPC clusters:** Non-intrusive UQ simulations consist of large numbers of smaller sample simulations. This is particularly the case in Multilevel and Multifidelity Monte Carlo simulations, where the cost between the computationally least and most expensive sample simulations can differ by many orders of magnitude. HPC clusters are not designed for this kind of applications, which entails performance bottlenecks, if no measures are taken to prevent them. This includes I/O bottlenecks due to very large numbers of relatively small files, as well as sub-optimal job-internal scheduling and idle times. PoUnce overcomes these issues by grouping large numbers of sample simulations into a common program execution with a common file I/O. Furthermore, in the interaction with the HPC scheduler, separate large-scale compute jobs are used for sample simulations of similar size, and post-processing is performed outside of these large compute jobs. This makes internal scheduling much more efficient and reduces idle times. Details can be found in the code documentation. 
- **Potential for extension**: The modularity of PoUnce together with its very compact source code lower the threshold to extend the code and adapt it to every users' individual needs. This includes adding adapters to new source codes, adapting interaction with new HPC clusters, and adding new UQ methods. Since users base UQ simulations on their own baseline codes and use different clusters, this modularity and extensibility is vital for PoUnce's applicability.

# UQ methods

PoUnce currently features three UQ methods: 

- **The non-intrusive polynomial chaos (NIPC) method:** This method is implemented based on the ChaosPy [@ChaosPyFeinberg2015] package and includes the possibility of using sparse grids. Since this method in its basic form only requires one iteration of sample simulations of similar computational cost, the implementation is simple and can be easily extended to more advanced methods, such as adaptive sparse grids. 
- **The Multilevel Monte Carlo (MLMC) method:** If this method is run with two iterations, it corresponds to the standard MLMC method as described in [@Giles2008] with a fixed set of resolution levels. More iterations can be used to carefully approach the optimal number of samples on every level while updating the estimates of these optimal numbers. This avoids overshooting the optimal sample numbers based on inaccurate estimates. Details on the method can be found in [@Beck2020]. 
- **The Multifidelity Monte Carlo (MFMC) method:** The method is implemented following [@Peherstorfer2016], with the additional option to re-use pilot samples for the eventual estimators.

More details on the implemented methods can be found in the documentation.

# Research based on PoUnce

Studies on uncertainty quantification for cavity aeroacoustics [@Kuhn2018] as well as on hp-MLMC methods [@Beck2020] are based on earlier versions of this software. A publication on uncertainty quantification for iced airfoil performance based on a recent version of the software is currently in preparation. 

# Acknowledgements

The development of PoUnce was funded by the Elisabeth and Friedrich Boysen Foundation.

PoUnce makes use of several libraries which we would like to acknowledge. This includes GNU parallel [@Tange2011a], chaospy [@ChaosPyFeinberg2015] and pyKriging [@Paulson2015].

# References

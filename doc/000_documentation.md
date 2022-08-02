---
title: PoUnce Documentation
author: 
  - Numerics Research Group
  - Institute for Aerodynamics and Gas Dynamics
  - University of Stuttgart, Germany
date: \today
documentclass: scrreprt
lang: en-US
papersize: a4
colorlinks: yes
toc: yes
header-includes:
  - \input{header}

---

# Introduction

PoUnce (Propagation of Uncertainties) is a Python framework for fully automatized runs of non-intrusive forward uncertainty quantification (UQ) simulations on high performance computers.

In UQ, some input parameters are not known precisely, but are uncertain with a given random distribution. In non-intrusive UQ methods, a standard simulation model is evaluated many times with different input parameter values and the model outputs are post-processed to obtain information about the output quantity of interest (QoI). In Multilevel Monte Carlo [@Heinrich2001; @Giles2008] and Multifidelity Monte Carlo [@Peherstorfer2016; @Peherstorfer2018] methods, different models with vastly different cost and fidelity are combined. The number of evaluations with each model is usually determined adaptively and iteratively at simulation runtime.

PoUnce enables UQ simulations with a computational cost that requires high performance computing (HPC) clusters. It serves as a connecting piece between UQ methods, simulation codes, and cluster software. 
The framework is designed to generate simulation input for each single model evaluation, schedule and run all model evaluations on the cluster, and post-process their results. It can be easily adapted to individual needs, such as new means of interaction with different baseline simulation codes. 

## About this guide 

Users of PoUnce probably have to familiarize themselves with at least parts of the source code, since they need to adapt it to their own baseline solver and possibly their own cluster.
This guide is therefore a mixed user and developer guide. Apart from basic usage, some high level design principles of the code are given. 

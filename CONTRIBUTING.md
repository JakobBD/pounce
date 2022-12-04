# How to contribute to PoUnce


## Before you start

Please read the documentation in the [doc](doc) folder, either online or by downloading and compiling it.

It contains sections on how to extend the code and on integration tests. 

## Possible contributions

Here are some possible ways to extend or improve PoUnce 

### Extensions:

- Add an adapter for your baseline solver to PoUnce, ideally for a widely used one
- Add support for new machines, ideally with additional schedulers
- Add additional UQ methods
- Add additional surrogate models
- Add additional random distributions
- Add additional sampling techniques (quasi Monte Carlo, Latin Hypercube, ...)
- Add additional stochastic quantities for output (such as higher moments in polynomial chaos)

### Improvements: 

- Exchange Kriging surrogate model implementation for a more performant and/or parallel one
- Improve user-friendly modification of parameters for a restart, for example via modified input parameter file
- Enable printing of default parameter files with comment strings for a given configuration

### Refactoring and code quality: 

- Report what is hard to understand when reading into the source code
- Flatten some of the inheritance schemes, for example by integrating the `Simulation` class in `UqMethod`.
- Break up some long routines, such as in [src/uqmethod/mfmc.py](uqmethod/mfmc.py) or [src/machines/hawk.py](machines/hawk.py).
- Enable linting and maybe add to integration actions

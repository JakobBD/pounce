# PoUnce

PoUnce (Propagation Of UNCErtainties) is a framework fully automatized runs of non-intrusive forward UQ simulations. 
It is designed for efficiency on HPC clusters.

Extending the code and adding an API for your own baseline solver and cluster/scheduler is comparatively simple due to the light-weight nature and modular design of PoUnce.
PoUnce therefore hopes to head-start for your own UQ implementation.

## Requirements

Required Python packages are given in [src/requirements.txt](src/requirements.txt).

## Quick start / basic run

Runs are configured using a YAML input file. Example input files are located in the `ini` folder.

For a test run, go to `ini/internal_local` and run 

```
python3 ../../src/pounce.py parameter_mlmc.py
```

## Contributors

The authors of PoUnce are:

Jakob Dürrwächter\
Thomas Kuhn\
Fabian Meyer\
Andrea Beck\
Claus-Dieter Munz

## License 

FLEXI is Copyright (C) 2022, Jakob Dürrwächter, Prof. Dr. Andrea Beck, and Prof. Dr. Claus-Dieter Munz and is 
released under the terms of the
GNU General Public License v3.0. For the full license terms see
the included license file [license](LICENSE.md).

## Reference / Please cite

References will be added shortly. In the meantime, please cite

A. Beck, J. Dürrwächter, T. Kuhn, F. Meyer, C.-D. Munz, C. Rohde.\
“hp-multilevel Monte Carlo methods for uncertainty quantification of compressible Navier–Stokes equations”. \
SIAM J. Sci. Comput. (Aug. 2020). \
DOI: https://doi.org/10.1137/18M1210575 \

## Documentation

Further documentation can be found in the `doc` folder. The guide can be compiled by simply running

```
make
```

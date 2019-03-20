# e3sm-unified

A metapackage for a unified anaconda environment for analysis of results from
the Energy Exascale Earth System Model (E3SM).

E3SM-Unified currently supports both linux and OSX, as well as python verions
2.7, 3.6 and 3.7.  A Windows version is not currently available.

To install the metapackage with x-windows support under CDAT, use:
```
conda create -n e3sm-unified-x -c conda-forge -c e3sm -c cdat \
   -c cdat/label/v81 e3sm-unified
```
To install without x-windows, use:
```
conda create -n e3sm-unified-nox -c conda-forge -c e3sm -c cdat \
   -c cdat/label/v81 e3sm-unified mesalib
```


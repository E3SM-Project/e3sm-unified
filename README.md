# e3sm-unified

A metapackage for a unified anaconda environment for analysis of results from
the Energy Exascale Earth System Model (E3SM).

Note, only linux (and compatible HPC environments) are supported.  OSX and Windows version are not currently available.

To install the metapackage with x-windows support under CDAT, use:
```
conda install -c conda-forge -c e3sm -c cdat e3sm-unified
```
To install without x-windows, use:
```
conda install -c conda-forge -c e3sm -c cdat e3sm-unified mesalib
```


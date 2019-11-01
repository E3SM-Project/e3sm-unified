# e3sm-unified

[![Build Status](https://travis-ci.org/E3SM-Project/e3sm-unified.svg?branch=master)](https://travis-ci.org/E3SM-Project/e3sm-unified)

A metapackage for a unified anaconda environment for analyzing results from
the Energy Exascale Earth System Model (E3SM).

E3SM-Unified currently supports linux and OSX, and python versions 3.6 and 3.7.  
A Windows version is not available and the development of one is not planned. Support
for python 2.7 was dropped in v1.3.0 of the package, but is available in earlier
versions.

Users can create a new anaconda environment either with or without x-windows support
within CDAT packages (if you do not plan to use CDAT or e3sm_diags, either version is
fine).  To create an E3SM-Unified environment with x-windows support under CDAT, use:
```
conda create -n e3sm-unified-x -c conda-forge -c defaults -c e3sm -c cdat/label/v82 \
    e3sm-unified
```
To create and environment without x-windows under CDAT, use:
```
conda create -n e3sm-unified-nox -c conda-forge -c defaults -c e3sm -c cdat/label/v82 \
    e3sm-unified mesalib
```

 The following packages are only available for linux and not OSX:
 - processflow
 - zstash

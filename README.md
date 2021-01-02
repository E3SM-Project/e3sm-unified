# e3sm-unified

[![Build Status](https://travis-ci.org/E3SM-Project/e3sm-unified.svg?branch=master)](https://travis-ci.org/E3SM-Project/e3sm-unified)

A metapackage for a unified anaconda environment for analyzing results from
the Energy Exascale Earth System Model (E3SM).

E3SM-Unified currently supports linux and OSX, and python >= 3.6.   A Windows 
version is not available and the development of one is not planned.

Users can create a new anaconda environment either with or without MPI support
from conda.  To create the latest version of the E3SM-Unified environment with 
MPI support from the `mpich` package, use:
```
conda config --add channels conda-forge
conda config --set channel_priority strict
conda create -n e3sm-unified-mpich -c conda-forge -c defaults -c e3sm \
    python=3.8 "e3sm-unified=*=mpi_mpich_*"
```
To create and environment without MPI, use:
```
conda config --add channels conda-forge
conda config --set channel_priority strict
conda create -n e3sm-unified-nompi -c conda-forge -c defaults -c e3sm \
    python=3.8 "e3sm-unified=*=nompi_*"
```

 The following packages are only available for linux and not OSX:
 - processflow
 - zstash
 - ncl

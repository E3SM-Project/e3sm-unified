# E3SM-Unified

A metapackage for a unified conda environment for analyzing results from
the Energy Exascale Earth System Model (E3SM).

E3SM-Unified currently supports linux and OSX, and python >=3.8,<3.11.
A Windows  version is not available and the development of one is not planned.

Users can create a new anaconda environment either with or without MPI support
from conda.  To create the latest version of the E3SM-Unified environment with 
MPI support from the `mpich` package (appropriate for laptops and some HPC 
login nodes), use:
```
conda config --add channels conda-forge
conda config --set channel_priority strict
conda create -n e3sm-unified-mpich -c conda-forge -c defaults -c e3sm \
    python=3.10 "e3sm-unified=*=mpi_mpich_*"
```

 The following package is only available for linux and not OSX:
 - zstash

For the full list of packages in the current version of the metapackages, see:
https://github.com/E3SM-Project/e3sm-unified/blob/master/recipes/e3sm-unified/meta.yaml

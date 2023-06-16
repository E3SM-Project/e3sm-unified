#!/bin/bash

set -e

rm -rf ~/mambaforge/conda-bld
upload=False
dev=True

if [ $dev == "True" ]
then
  channels="-c conda-forge/label/mache_dev \
            -c conda-forge/label/mpas_analysis_dev \
            -c conda-forge/label/zppy_dev \
            -c conda-forge \
            -c defaults"
else
  channels="-c conda-forge -c defaults -c e3sm"
fi

for file in configs/mpi_hpc_python3.9.yaml
#for file in configs/mpi_*_python*.yaml
do
  conda mambabuild -m $file --override-channels $channels .
done

if [ $upload == "True" ]
then
   anaconda upload -u e3sm ${HOME}/miniconda3/conda-bld/linux-64/e3sm-unified-*.tar.bz2
fi

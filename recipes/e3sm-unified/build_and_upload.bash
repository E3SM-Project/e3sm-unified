#!/bin/bash

set -e

conda_dir=${HOME}/miniforge
os_dir=linux-64
upload=False
dev=True

rm -rf ${conda_dir}/conda-bld

if [ $dev == "True" ]
then

  channels="-c conda-forge/label/e3sm_diags_dev \
            -c conda-forge/label/e3sm_to_cmip_dev \
            -c conda-forge/label/mpas_analysis_dev \
            -c conda-forge/label/zppy_dev \
            -c conda-forge"

  for file in configs/mpi_mpich_python3.10.yaml configs/mpi_hpc_python3.10.yaml
  do
    conda build -m $file --override-channels --use-local $channels .
  done

  if [ $upload == "True" ]
  then
    anaconda upload -u e3sm -l e3sm_dev ${conda_dir}/conda-bld/${os_dir}/e3sm-unified-*.tar.bz2
  fi

else

  channels="-c conda-forge"
  for file in configs/mpi_*_python*.yaml
  do
    conda build -m $file --override-channels $channels .
  done

  if [ $upload == "True" ]
  then
    anaconda upload -u e3sm ${conda_dir}/conda-bld/${os_dir}/e3sm-unified-*.tar.bz2
  fi
fi

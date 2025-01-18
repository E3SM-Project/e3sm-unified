#!/bin/bash

set -e

conda_dir=${HOME}/miniforge3
dev=True

rm -rf ${conda_dir}/conda-bld

if [ $dev == "True" ]
then

  channels="-c conda-forge/label/chemdyg_dev \
            -c conda-forge/label/e3sm_diags_dev \
            -c conda-forge/label/mache_dev \
            -c conda-forge/label/mpas_analysis_dev \
            -c conda-forge/label/zppy_dev \
            -c conda-forge/label/zstash_dev \
            -c conda-forge"

  for file in configs/mpi_mpich_python3.10.yaml configs/mpi_hpc_python3.10.yaml
  do
    conda build -m $file --override-channels $channels .
  done

else

  channels="-c conda-forge -c e3sm"
  for file in configs/mpi_*_python*.yaml
  do
    conda build -m $file --override-channels $channels .
  done

fi

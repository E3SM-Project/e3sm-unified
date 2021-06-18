#!/bin/bash

set -e

rm -rf ~/miniconda3/conda-bld
upload=False
dev=True

if [ $dev == "True" ]
then
  channels="-c e3sm/label/e3sm_dev -c conda-forge/label/e3sm_dev \
  -c conda-forge -c defaults -c e3sm"
else
  channels="-c conda-forge -c defaults -c e3sm"
fi

for file in configs/mpi_*_python*.yaml
do
  conda build -m $file --override-channels $channels .
done

if [ $upload == "True" ]
then
   anaconda upload -u e3sm ${HOME}/miniconda3/conda-bld/linux-64/e3sm-unified-*.tar.bz2
fi

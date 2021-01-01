#!/bin/bash

rm -rf ~/miniconda3/conda-bld
upload=False

for file in configs/mpi_*_python*.yaml
do
  conda build -m $file --override-channels -c conda-forge -c defaults -c e3sm .
done

if [ $upload == "True" ]
then
   anaconda upload -u e3sm ${HOME}/miniconda3/conda-bld/linux-64/e3sm-unified-*.tar.bz2
fi

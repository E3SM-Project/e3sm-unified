#!/bin/bash

#conda build -c conda-forge -c defaults -c e3sm -c cdat/label/v81 meta.yaml

upload=True
version=1.2.6
pythons=(27 36 37)
build=0

if [ $upload == "True" ]
then
   for python in "${pythons[@]}"
   do
      anaconda upload -u e3sm /home/${USER}/miniconda3/conda-bld/linux-64/e3sm-unified-${version}-py${python}_${build}.tar.bz2
   done
fi

#!/bin/bash

conda build -c conda-forge -c defaults meta.yaml

upload=False
version=1.0.0
pythons=(27 36 37)
build=1

if [ $upload == "True" ]
then
   for python in "${pythons[@]}"
   do
      anaconda upload -u e3sm ${HOME}/miniconda3/conda-bld/linux-64/cime-env-${version}-py${python}_${build}.tar.bz2
   done
fi

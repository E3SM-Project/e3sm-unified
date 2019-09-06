#!/bin/bash

conda build --override-channels -c conda-forge -c defaults -c e3sm -c cdat/label/v82 meta.yaml

upload=False
version=1.3.0
pythons=(36 37)
build=0

if [ $upload == "True" ]
then
   for python in "${pythons[@]}"
   do
      anaconda upload -u e3sm ${HOME}/miniconda3/conda-bld/linux-64/e3sm-unified-${version}-py${python}_${build}.tar.bz2
   done
fi

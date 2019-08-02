#!/bin/bash

#conda build -c conda-forge -c defaults -c e3sm -c cdat/label/v81 meta.yaml

upload=True
unified_version=1.2.6
simple_version=1.0.0
names=("unified" "simple")
pythons=(27 36 37)
build=0

if [ $upload == "True" ]
then
   for python in "${pythons[@]}"
   do
      for name in names
      do
        if [ $name == "unified" ]
        then
          version=$unified_version
        else
          version=$simple_version
        fi
        anaconda upload -u e3sm /home/xylar/miniconda3/conda-bld/linux-64/e3sm-${name}-${version}-py${python}_${build}.tar.bz2
      done
   done
fi

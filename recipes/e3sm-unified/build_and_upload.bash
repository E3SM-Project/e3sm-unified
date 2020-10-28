#!/bin/bash

rm -rf ~/miniconda3/conda-bld

conda build --override-channels -c conda-forge -c defaults -c e3sm .

upload=False

if [ $upload == "True" ]
then
   anaconda upload -u e3sm ${HOME}/miniconda3/conda-bld/linux-64/e3sm-unified-*.tar.bz2
fi

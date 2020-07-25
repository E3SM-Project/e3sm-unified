#!/bin/bash

conda build --override-channels -c conda-forge -c defaults -c e3sm -c cdat/label/v82 .

upload=False

if [ $upload == "True" ]
then
   anaconda upload -u e3sm ${HOME}/miniconda3/conda-bld/linux-64/e3sm-unified-*.tar.bz2
fi

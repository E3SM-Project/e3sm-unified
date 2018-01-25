#!/bin/bash

# Modify the following to update the e3sm-unified version,
# the python version or to specify whether to support x-windows
# under uv-cdat (x) or not (nox).  Typically, run the script once
# each for x and nox
version=1.1.2
python=2
x_or_nox=nox

# The rest of the script should not need to be modified
machine=$NERSC_HOST

miniconda=Miniconda${python}-latest-Linux-x86_64.sh
base_path=/global/project/projectdirs/acme/software/anaconda_envs/${machine}_e3sm_unified_${version}_py${python}_${x_or_nox}

channels="-c conda-forge -c e3sm -c acme -c uvcdat"
if [ $x_or_nox = "x" ]; then
   packages="e3sm-unified=${version}"
else
   packages="e3sm-unified=${version} mesalib"
fi

wget https://repo.continuum.io/miniconda/$miniconda
/bin/bash $miniconda -b -p $base_path
rm $miniconda
export PATH="$base_path/bin:$PATH"
conda config --add channels conda-forge
conda update -y --all
conda install -y $channels $packages
# force reinstallation of several packages:
# * six gets messed up by vtk-cdat
# * the rest are messed up by gcc
conda install -y --force -c conda-forge six libgcc libgcc-ng libstdcxx-ng
cd $base_path
chown -R $USER:acme .
chmod -R g+rX .
chmod -R g-w .
chmod -R o-rwx .

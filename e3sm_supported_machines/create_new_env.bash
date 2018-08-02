#!/bin/bash

# Modify the following to choose which e3sm-unified version(s)
# the python version(s) are installed and whether to make an environment with
# x-windows support under cdat (x), without (nox) or both (nox x).  Typically,
# both x and nox environments should be created.
versions=(1.2.1)
pythons=(2.7)
x_or_noxs=(nox x)

# Any subsequent commands which fail will cause the shell script to exit
# immediately
set -e

world_read="False"

# The rest of the script should not need to be modified
if [[ $HOSTNAME = "edison"* ]]; then
  env_path="/global/project/projectdirs/acme/software/anaconda_envs/edison"
  group="acme"
elif [[ $HOSTNAME = "cori"* ]]; then
  env_path="/global/project/projectdirs/acme/software/anaconda_envs/cori"
  group="acme"
elif [[ $HOSTNAME = "acme1"* ]] || [[ $HOSTNAME = "aims4"* ]]; then
  env_path="/usr/local/e3sm_unified/envs"
  group="climate"
elif [[ $HOSTNAME = "blogin"* ]]; then
  env_path="/lcrc/soft/climate/e3sm-unified"
  group="climate"
elif [[ $HOSTNAME = "rhea"* ]]; then
  env_path="/ccs/proj/cli900/sw/rhea/e3sm-unified"
  group="cli900"
  world_read="True"
elif [[ $HOSTNAME = "cooley"* ]]; then
  env_path="/lus/theta-fs0/projects/ccsm/acme/tools/e3sm-unified"
  group="ccsm"
  world_read="True"
else
  echo "Unknown host name $HOSTNAME.  Add env_path and group for this machine to the script."
fi

channels="-c conda-forge -c e3sm -c cdat"
base_path=$env_path/base

if [ ! -d $base_path ]; then
  miniconda=Miniconda2-latest-Linux-x86_64.sh
  wget https://repo.continuum.io/miniconda/$miniconda
  /bin/bash $miniconda -b -p $base_path
  rm $miniconda
fi

# activate the new environment
. $base_path/etc/profile.d/conda.sh
conda activate

conda config --add channels conda-forge
conda update -y --all

for version in "${versions[@]}"
do
  for python in "${pythons[@]}"
  do
    for x_or_nox in "${x_or_noxs[@]}"
    do
      packages="python=$python e3sm-unified=${version}"
      if [ $x_or_nox = "nox" ]; then
        packages="$packages mesalib"
      fi
      env_name=e3sm_unified_${version}_py${python}_${x_or_nox}
      conda create -n $env_name -y $channels $packages
      # force reinstallation of several packages:
      # * six gets messed up by vtk-cdat
      # * the rest are messed up by gcc
      conda install -y -n $env_name --force -c conda-forge six libgcc libgcc-ng libstdcxx-ng

      conda activate $env_name
      python -c "import vcs"
      python -c "import mpas_analysis"
      livv --version

    done
  done
done

# delete the tarballs and any unused packages
conda clean -y -p -t
cd $base_path
chown -R $USER:$group .
if [ $world_read == "True" ]; then
  chmod -R go+rX .
  chmod -R go-w
else
  chmod -R g+rX .
  chmod -R g-w .
  chmod -R o-rwx .
fi

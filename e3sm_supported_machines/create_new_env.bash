#!/bin/bash

check_env () {
  echo "Checking the environment $env_name"
  python -c "import vcs"
  if [ $? -eq 0 ]; then
    echo "  vcs failed"
    exit 1
  else
    echo "  vcs passed"
  fi
  python -c "import mpas_analysis"
  if [ $? -eq 0 ]; then
    echo "  mpas_analysis failed"
    exit 1
  else
    echo "  mpas_analysis passed"
  fi
  livv --version
  if [ $? -eq 0 ]; then
    echo "  livvkit failed"
    exit 1
  else
    echo "  livvkit passed"
  fi
  python -c "import acme_diags"
  if [ $? -eq 0 ]; then
    echo "  acme_diags failed"
    exit 1
  else
    echo "  acme_diags passed"
  fi
  if [[ $HOSTNAME == "blogin"* || $HOSTNAME == "rhea"* ]]; then
    echo "  skipping processflow"
  else
    processflow.py -v
    if [ $? -eq 0 ]; then
      echo "  processflow failed"
      exit 1
    else
      echo "  processflow passed"
    fi
  fi
}


# Modify the following to choose which e3sm-unified version(s)
# the python version(s) are installed and whether to make an environment with
# x-windows support under cdat (x), without (nox) or both (nox x).  Typically,
# both x and nox environments should be created.
versions=(1.2.2)
pythons=(2.7)
x_or_noxs=(nox x)

default_python=2.7
default_x_or_nox=nox

# Any subsequent commands which fail will cause the shell script to exit
# immediately
set -e

world_read="False"
support_mod="True"
channels="-c conda-forge -c e3sm -c cdat"

# The rest of the script should not need to be modified
if [[ $HOSTNAME = "edison"* ]]; then
  base_path="/global/project/projectdirs/acme/software/anaconda_envs/edison/base"
  mod_path="/global/project/projectdirs/acme/software/modulefiles/all"
  group="acme"
elif [[ $HOSTNAME = "cori"* ]]; then
  base_path="/global/project/projectdirs/acme/software/anaconda_envs/cori/base"
  mod_path="/global/project/projectdirs/acme/software/modulefiles/all"
  group="acme"
elif [[ $HOSTNAME = "acme1"* ]] || [[ $HOSTNAME = "aims4"* ]]; then
  base_path="/usr/local/e3sm_unified/envs/base"
  mod_path="/usr/local/e3sm_unified/modulefiles"
  group="climate"
elif [[ $HOSTNAME = "blogin"* ]]; then
  base_path="/lcrc/soft/climate/e3sm-unified/base"
  group="climate"
  support_mod="False"
elif [[ $HOSTNAME = "rhea"* ]]; then
  base_path="/ccs/proj/cli900/sw/rhea/e3sm-unified/base"
  mod_path="/ccs/proj/cli900/sw/rhea/modulefiles/all"
  group="cli900"
  world_read="True"
elif [[ $HOSTNAME = "cooley"* ]]; then
  base_path="/lus/theta-fs0/projects/ccsm/acme/tools/e3sm-unified/base"
  mod_path="/lus/theta-fs0/projects/ccsm/acme/tools/modulefiles"
  group="ccsm"
  world_read="True"
elif [[ $HOSTNAME = "gr-fe"* ]]; then
  base_path="/usr/projects/climate/SHARED_CLIMATE/anaconda_envs/base"
  mod_path="/usr/projects/climate/SHARED_CLIMATE/modulefiles/all"
  group="climate"
elif [[ $HOSTNAME = "eleven"* ]]; then
  base_path="/home/xylar/miniconda3"
  mod_path="/home/xylar/test_mod"
  support_mod="False"
  group="xylar"
  channels="$channels --use-local"
else
  echo "Unknown host name $HOSTNAME.  Add env_path and group for this machine to the script."
fi

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

template_downloaded="False"
if [ ! -f module_template ]; then
  wget https://raw.githubusercontent.com/E3SM-Project/e3sm-unified/master/e3sm_supported_machines/module_template
  template_downloaded="True"
fi

for version in "${versions[@]}"
do
  for python in "${pythons[@]}"
  do
    for x_or_nox in "${x_or_noxs[@]}"
    do
      packages="python=$python e3sm-unified=${version}"
      if [ $x_or_nox == "nox" ]; then
        packages="$packages mesalib"
      fi
      env_name=e3sm_unified_${version}_py${python}_${x_or_nox}
      conda remove -n $env_name -y --all
      conda create -n $env_name -y $channels $packages

      conda activate $env_name
      if [[ $HOSTNAME = "blogin"* ]]; then
        unset LD_LIBRARY_PATH
      fi
      check_env
      conda deactivate

      # make module files
      if [ $support_mod == "True" ]; then
        mkdir -p $mod_path/e3sm-unified
        mod_name=e3sm-unified/${version}_py${python}_${x_or_nox}
        sed "s#@version#$version#g; s#@python#$python#g; s#@x_or_nox#$x_or_nox#g; s#@base_path#$base_path/envs/$env_name#g" module_template > $mod_path/$mod_name

        if [[ $python == $default_python && $x_or_nox == $default_x_or_nox ]]; then
          # make this the default version
          ln -sfn ${version}_py${python}_${x_or_nox} $mod_path/e3sm-unified/${version}
        fi
        module use $mod_path
        module load $mod_name
        check_env
        module unload $mod_name

      fi

    done
  done
done

if [ $template_downloaded == "True" ]; then
  rm -rf module_template
fi

# delete the tarballs and any unused packages
conda clean -y -p -t
cd $base_path
chown -R $USER:$group .
if [ $world_read == "True" ]; then
  chmod -R go+rX .
  chmod -R go-w .
else
  chmod -R g+rX .
  chmod -R g-w .
  chmod -R o-rwx .
fi


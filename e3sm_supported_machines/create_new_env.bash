#!/bin/bash

check_env () {
  echo "Checking the environment $env_name"
  python -c "import vcs"
  if [ $? -eq 0 ]; then
    echo "  vcs passed"
  else
    echo "  vcs failed"
    exit 1
  fi
  python -c "import mpas_analysis"
  if [ $? -eq 0 ]; then
    echo "  mpas_analysis passed"
  else
    echo "  mpas_analysis failed"
    exit 1
  fi
  livv --version
  if [ $? -eq 0 ]; then
    echo "  livvkit passed"
  else
    echo "  livvkit failed"
    exit 1
  fi
  python -c "import acme_diags"
  if [ $? -eq 0 ]; then
    echo "  acme_diags passed"
  else
    echo "  acme_diags failed"
    exit 1
  fi
  processflow -v
  if [ $? -eq 0 ]; then
    echo "  processflow passed"
  else
    echo "  processflow failed"
    exit 1
  fi
}


# Modify the following to choose which e3sm-unified version(s)
# the python version(s) are installed and whether to make an environment with
# x-windows support under cdat (x), without (nox) or both (nox x).  Typically,
# both x and nox environments should be created.
versions=(1.2.3)
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
  activ_path="/global/project/projectdirs/acme/software/anaconda_envs"
  group="acme"
elif [[ $HOSTNAME = "cori"* ]]; then
  base_path="/global/project/projectdirs/acme/software/anaconda_envs/cori/base"
  activ_path="/global/project/projectdirs/acme/software/anaconda_envs"
  group="acme"
elif [[ $HOSTNAME = "acme1"* ]] || [[ $HOSTNAME = "aims4"* ]]; then
  base_path="/usr/local/e3sm_unified/envs/base"
  activ_path="/usr/local/e3sm_unified/envs"
  group="climate"
elif [[ $HOSTNAME = "blogin"* ]]; then
  base_path="/lcrc/soft/climate/e3sm-unified/base"
  activ_path="/lcrc/soft/climate/e3sm-unified"
  group="climate"
  support_mod="False"
elif [[ $HOSTNAME = "rhea"* ]]; then
  base_path="/ccs/proj/cli900/sw/rhea/e3sm-unified/base"
  activ_path="/ccs/proj/cli900/sw/rhea/e3sm-unified"
  group="cli900"
  world_read="True"
elif [[ $HOSTNAME = "cooley"* ]]; then
  base_path="/lus/theta-fs0/projects/ccsm/acme/tools/e3sm-unified/base"
  activ_path="/lus/theta-fs0/projects/ccsm/acme/tools/e3sm-unified"
  group="ccsm"
  world_read="True"
elif [[ $HOSTNAME = "gr-fe"* ]] || [[ $HOSTNAME = "wf-fe"* ]]; then
  base_path="/usr/projects/climate/SHARED_CLIMATE/anaconda_envs/base"
  activ_path="/usr/projects/climate/SHARED_CLIMATE/anaconda_envs"
  group="climate"
elif [[ $HOSTNAME = "eleven"* ]]; then
  base_path="/home/xylar/miniconda3"
  activ_path="/home/xylar/Desktop"
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
      if [ ! -d $base_path/envs/$env_name ]; then
        echo creating $env_name
        conda create -n $env_name -y $channels $packages
      else
        echo $env_name already exists
      fi

      conda activate $env_name
      if [[ $HOSTNAME = "blogin"* ]]; then
        unset LD_LIBRARY_PATH
      fi
      check_env
      conda deactivate

      # make activation scripts
      for ext in sh csh
      do
        script=""
        if [ $support_mod == "True" ]; then
          script="module unload python e3sm-unified"
        fi
        if [[ $HOSTNAME = "edison"* ]] || [[ $HOSTNAME = "cori"* ]]; then
          script="${script}"$'\n'
          script="${script}source /global/project/projectdirs/acme/software/anaconda_envs/"
          script="${script}"'${NERSC_HOST}'"/base/etc/profile.d/conda.${ext}"
        else
          script="${script}"$'\n'"source ${base_path}/etc/profile.d/conda.${ext}"
        fi
        script="${script}"$'\n'"conda activate $env_name"
        if [[ $HOSTNAME = "blogin"* ]]; then
          script="${script}"$'\n'"unset LD_LIBRARY_PATH"
        fi
        if [[ $python == $default_python && $x_or_nox == $default_x_or_nox ]]; then
          file_name=$activ_path/load_latest_e3sm_unified.${ext}
        elif [[ $python == $default_python ]]; then
          file_name=$activ_path/load_latest_e3sm_unified_${x_or_nox}.${ext}
        else
          file_name=$activ_path/load_latest_e3sm_unified_py${python}_${x_or_nox}.${ext}
        fi
        rm -f "$file_name"
        echo "${script}" > "$file_name"
      done
    done
  done
done

# delete the tarballs and any unused packages
conda clean -y -p -t

echo "changing permissions on activation scripts"
chown -R $USER:$group $activ_path/load_latest_e3sm_unified*
if [ $world_read == "True" ]; then
  chmod -R go+r $activ_path/load_latest_e3sm_unified*
  chmod -R go-w $activ_path/load_latest_e3sm_unified*
else
  chmod -R g+r $activ_path/load_latest_e3sm_unified*
  chmod -R g-w $activ_path/load_latest_e3sm_unified*
  chmod -R o-rwx $activ_path/load_latest_e3sm_unified*
fi

echo "changing permissions on environments"
cd $base_path
  echo "  changing owner"
chown -R $USER:$group .
if [ $world_read == "True" ]; then
  echo "  adding group/world read"
  chmod -R go+rX .
  echo "  removing group/world write"
  chmod -R go-w .
else
  echo "  adding group read"
  chmod -R g+rX .
  echo "  removing group write"
  chmod -R g-w .
  echo "  removing world read/write"
  chmod -R o-rwx .
fi
  echo "  done."


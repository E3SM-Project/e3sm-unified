#!/bin/bash

check_env () {
  echo "Checking the environment $env_name"
  python -c "import evv4esm"
  if [ $? -eq 0 ]; then
    echo "  evv4esm passed"
  else
    echo "  evv4esm failed"
    exit 1
  fi
  evv --version
  if [ $? -eq 0 ]; then
    echo "  evv passed"
  else
    echo "  evv failed"
    exit 1
  fi
}


# Modify the following to choose which e3sm-simple version(s)
# the python version(s) are installed
versions=(1.0.0)
pythons=(3.7 2.7)

default_python=3.7

# Any subsequent commands which fail will cause the shell script to exit
# immediately
set -e

world_read="False"
channels="-c conda-forge -c defaults -c e3sm"

# The rest of the script should not need to be modified
if [[ $HOSTNAME = "cori"* ]] || [[ $HOSTNAME = "dtn"* ]]; then
  base_path="/global/project/projectdirs/acme/software/anaconda_envs/cori/base"
  activ_path="/global/project/projectdirs/acme/software/anaconda_envs"
  group="acme"
elif [[ $HOSTNAME = "acme1"* ]] || [[ $HOSTNAME = "aims4"* ]]; then
  base_path="/usr/local/e3sm_unified/envs/base"
  activ_path="/usr/local/e3sm_unified/envs"
  group="climate"
elif [[ $HOSTNAME = "blueslogin"* ]]; then
  base_path="/lcrc/soft/climate/e3sm-unified/base"
  activ_path="/lcrc/soft/climate/e3sm-unified"
  group="climate"
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
elif [[ $HOSTNAME = "compy"* ]]; then
  base_path="/compyfs/software/e3sm-unified/base"
  activ_path="/compyfs/software/e3sm-unified"
  group="users"
elif [[ $HOSTNAME = "gr-fe"* ]] || [[ $HOSTNAME = "wf-fe"* ]]; then
  base_path="/usr/projects/climate/SHARED_CLIMATE/anaconda_envs/base"
  activ_path="/usr/projects/climate/SHARED_CLIMATE/anaconda_envs"
  group="climate"
elif [[ $HOSTNAME = "eleven"* ]]; then
  base_path="/home/xylar/miniconda3"
  activ_path="/home/xylar/Desktop"
  group="xylar"
  channels="$channels --use-local"
elif [[ $HOSTNAME = "lap101101" ]] || [[ $HOSTNAME = "pc0101123" ]]; then
  base_path="/home/fjk/miniconda3"
  activ_path="/home/fjk/Documents/Code/E3SM/"
  group="users"
  channels="$channels --use-local"
else
  echo "Unknown host name $HOSTNAME.  Add env_path and group for this machine to the script."
  exit 1
fi

if [ ! -d $base_path ]; then
  miniconda=Miniconda3-latest-Linux-x86_64.sh
  wget https://repo.continuum.io/miniconda/$miniconda
  /bin/bash $miniconda -b -p $base_path
  rm $miniconda
fi

# activate the new environment
. $base_path/etc/profile.d/conda.sh
conda activate

conda config --add channels conda-forge
conda config --set channel_priority strict
conda update -y --all

for version in "${versions[@]}"
do
  for python in "${pythons[@]}"
  do
    packages="python=$python e3sm-simple=${version}"

    if [[ $python == $default_python ]]; then
      suffix=""
    else
      suffix=_py${python}
    fi

    env_name=e3sm_simple_${version}${suffix}
    if [ ! -d $base_path/envs/$env_name ]; then
      echo creating $env_name
      conda create -n $env_name -y $channels $packages
    else
      echo $env_name already exists
    fi

    conda activate $env_name
    check_env
    conda deactivate

    # make activation scripts
    for ext in sh csh
    do
      if [[ $ext = "sh" ]]; then
        script="if [ -x \"\$(command -v module)\" ] ; then"
        script="${script}"$'\n'"  module unload python"
        script="${script}"$'\n'"fi"
      else
        script=""
      fi
      script="${script}"$'\n'"source ${base_path}/etc/profile.d/conda.${ext}"
      script="${script}"$'\n'"conda activate $env_name"
      file_name=$activ_path/load_latest_e3sm_simple${suffix}.${ext}
      rm -f "$file_name"
      echo "${script}" > "$file_name"
    done
  done
done

# delete the tarballs and any unused packages
conda clean -y -p -t

echo "changing permissions on activation scripts"
chown -R $USER:$group $activ_path/load_latest_e3sm_simple*
if [ $world_read == "True" ]; then
  chmod -R go+r $activ_path/load_latest_e3sm_simple*
  chmod -R go-w $activ_path/load_latest_e3sm_simple*
else
  chmod -R g+r $activ_path/load_latest_e3sm_simple*
  chmod -R g-w $activ_path/load_latest_e3sm_simple*
  chmod -R o-rwx $activ_path/load_latest_e3sm_simple*
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


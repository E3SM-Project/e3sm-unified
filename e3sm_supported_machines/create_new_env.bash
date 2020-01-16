#!/bin/bash

check_env () {
  echo "Checking the environment $env_name"
  export CDAT_ANONYMOUS_LOG=no

  if [ "$env_type" != "sysmpi" ]; then
    if python -c "import vcs"; then
      echo "  vcs passed"
    else
      echo "  vcs failed"
      exit 1
    fi
   if python -c "import ILAMB"; then
      echo "  ILAMB passed"
    else
      echo "  ILAMB failed"
      exit 1
    fi
    if python -c "import acme_diags"; then
      echo "  import acme_diags passed"
    else
      echo "  import acme_diags failed"
      exit 1
    fi

    if e3sm_diags --help; then
      echo "  e3sm_diags passed"
    else
      echo "  e3sm_diags failed"
      exit 1
    fi
  fi

  if python -c "import mpas_analysis"; then
    echo "  import mpas_analysis passed"
  else
    echo "  import mpas_analysis failed"
    exit 1
  fi

  if mpas_analysis -h; then
    echo "  mpas_analysis passed"
  else
    echo "  mpas_analysis failed"
    exit 1
  fi

  if python -c "import livvkit"; then
    echo "  livvkit passed"
  else
    echo "  livvkit failed"
    exit 1
  fi

  if livv --version; then
    echo "  livv passed"
  else
    echo "  livv failed"
    exit 1
  fi

  if python -c "import IPython"; then
    echo "  IPython passed"
  else
    echo "  IPython failed"
    exit 1
  fi

  if  python -c "import globus_cli"; then
    echo "  globus_cli passed"
  else
    echo "  globus_cli failed"
    exit 1
  fi

  if globus --help; then
    echo "  globus passed"
  else
    echo "  globus failed"
    exit 1
  fi

  if python -c "import zstash"; then
    echo "  import zstash passed"
  else
    echo "  import zstash failed"
    exit 1
  fi

  if zstash --help; then
    echo "  zstash passed"
  else
    echo "  zstash failed"
    exit 1
  fi

  if zstash --help; then
    echo "  zstash passed"
  else
    echo "  zstash failed"
    exit 1
  fi

  if GenerateCSMesh --res 64 --alt --file gravitySam.000000.3d.cubedSphere.g; then
    echo "  tempest-remap passed"
  else
    echo "  tempest-remap failed"
    exit 1
  fi
  if processflow -v; then
    echo "  processflow passed"
  else
    echo "  processflow failed"
    exit 1
  fi

}


# Modify the following to choose which e3sm-unified version(s) the python version(s) are installed and whether to make
# an environment with x-windows support under cdat (cdatx), without (nox), and/or with system MPI (sysmpi).  Typically,
# all three environments should be created.
versions=(1.3.0)
pythons=(3.7)
env_types=(nox cdatx sysmpi)

default_python=3.7
default_env_type=nox

mpi4py_ver=3.0.2

# Any subsequent commands which fail will cause the shell script to exit
# immediately
set -e

world_read="True"

# The rest of the script should not need to be modified
if [[ $HOSTNAME = "cori"* ]] || [[ $HOSTNAME = "dtn"* ]]; then
  base_path="/global/cfs/cdirs/acme/software/anaconda_envs/base"
  activ_path="/global/cfs/cdirs/acme/software/anaconda_envs"
  group="acme"
  module unload PrgEnv-intel
  module load PrgEnv-gnu
  module unload craype-hugepages2M
  custom_script="echo module unlaod PrgEnv-intel"
  custom_script="${custom_script}"$'\n'"module unload PrgEnv-intel"
  custom_script="${custom_script}"$'\n'"echo module load PrgEnv-gnu"
  custom_script="${custom_script}"$'\n'"module laod PrgEnv-gnu"
  custom_script="${custom_script}"$'\n'"echo module unload craype-hugepages2M"
  custom_script="${custom_script}"$'\n'"module unload craype-hugepages2M"
  mpicc="$(which cc) -shared"
elif [[ $HOSTNAME = "acme1"* ]] || [[ $HOSTNAME = "aims4"* ]]; then
  base_path="/usr/local/e3sm_unified/envs/base"
  activ_path="/usr/local/e3sm_unified/envs"
  group="climate"
elif [[ $HOSTNAME = "blueslogin"* ]]; then
  base_path="/lcrc/soft/climate/e3sm-unified/base"
  activ_path="/lcrc/soft/climate/e3sm-unified"
  group="climate"
  mpicc="$(which mpicc)"
elif [[ $HOSTNAME = "rhea"* ]]; then
  base_path="/ccs/proj/cli900/sw/rhea/e3sm-unified/base"
  activ_path="/ccs/proj/cli900/sw/rhea/e3sm-unified"
  group="cli900"
elif [[ $HOSTNAME = "cooley"* ]]; then
  base_path="/lus/theta-fs0/projects/ccsm/acme/tools/e3sm-unified/base"
  activ_path="/lus/theta-fs0/projects/ccsm/acme/tools/e3sm-unified"
  group="ccsm"
  mpicc="$(which mpicc)"
elif [[ $HOSTNAME = "compy"* ]]; then
  base_path="/compyfs/software/e3sm-unified/base"
  activ_path="/compyfs/software/e3sm-unified"
  group="users"
  module load gcc/4.8.5
  module load mvapich2/2.3.1
  custom_script="echo module load gcc/4.8.5"
  custom_script="${custom_script}"$'\n'"module load gcc/4.8.5"
  custom_script="${custom_script}"$'\n'"echo module load mvapich2/2.3.1"
  custom_script="${custom_script}"$'\n'"module load mvapich2/2.3.1"
  mpicc="$(which mpicc)"
elif [[ $HOSTNAME = "gr-fe"* ]] || [[ $HOSTNAME = "wf-fe"* ]]; then
  base_path="/usr/projects/climate/SHARED_CLIMATE/anaconda_envs/base"
  activ_path="/usr/projects/climate/SHARED_CLIMATE/anaconda_envs"
  group="climate"
  module load intel
  module load openmpi
  custom_script="echo module load intel"
  custom_script="${custom_script}"$'\n'"module load intel"
  custom_script="${custom_script}"$'\n'"echo module load openmpi"
  custom_script="${custom_script}"$'\n'"module load openmpi"
  mpicc="$(which mpicc)"
elif [[ $HOSTNAME = "burnham"* ]]; then
  base_path="/home/xylar/Desktop/test_e3sm_unified/base"
  activ_path="/home/xylar/Desktop/test_e3sm_unified"
  group="xylar"
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
source $base_path/etc/profile.d/conda.sh
conda activate

conda config --add channels conda-forge
conda config --set channel_priority strict
conda update -y --all

if [[ -n $mpicc ]]; then
  if [ ! -f "mpi4py-${mpi4py_ver}.tar.gz" ]; then
    wget "https://bitbucket.org/mpi4py/mpi4py/downloads/mpi4py-${mpi4py_ver}.tar.gz"
  fi
  rm -rf "mpi4py-${mpi4py_ver}"
  tar zxvf "mpi4py-${mpi4py_ver}.tar.gz"
fi

for version in "${versions[@]}"
do
  for python in "${pythons[@]}"
  do
    for env_type in "${env_types[@]}"
    do
      if [ "$env_type" == "sysmpi" ]; then
        channels="--override-channels -c e3sm -c conda-forge -c defaults -c cdat/label/v82"
        if [[ -n $mpicc ]]; then
          packages="python=$python e3sm-unified-hpc=${version} mesalib"
        else
          # no system MPI defined, so don't build this version
          continue
        fi
      elif [ "$env_type" == "nox" ]; then
        channels="--override-channels -c conda-forge -c defaults -c e3sm -c cdat/label/v82"
        packages="python=$python e3sm-unified=${version} mesalib"
      else
        channels="--override-channels -c conda-forge -c defaults -c e3sm -c cdat/label/v82"
        packages="python=$python e3sm-unified=${version}"
      fi

      if [[ "$python" == "$default_python" && "$env_type" == "$default_env_type" ]]; then
        suffix=""
      elif [[ "$python" == "$default_python" ]]; then
        suffix="_${env_type}"
      else
        suffix="_py${python}_${env_type}"
      fi

      env_name=e3sm_unified_${version}${suffix}
      if [ ! -d "$base_path/envs/$env_name" ]; then
        echo creating "$env_name"
        conda create -n "$env_name" -y $channels $packages
        conda activate "$env_name"
        if [ "$env_type" == "sysmpi" ]; then
          cd "mpi4py-${mpi4py_ver}"
          python setup.py build --mpicc="$mpicc"
          python setup.py install
          cd ..
          conda install -y -c conda-forge -c defaults --no-deps ilamb=2.5
        fi
        conda deactivate
      else
        echo "$env_name" already exists
      fi

      conda activate "$env_name"
      check_env
      conda deactivate

      mkdir -p "$activ_path"

      # make activation scripts
      for ext in sh csh
      do
        if [[ -n $custom_script && "$env_type" == "sysmpi" ]]; then
          script=$custom_script
        else
          script=""
        fi
        if [[ $ext = "sh" ]]; then
          script="${script}"$'\n'"if [ -x \"\$(command -v module)\" ] ; then"
          script="${script}"$'\n'"  module unload python"
          script="${script}"$'\n'"fi"
        fi
        script="${script}"$'\n'"source ${base_path}/etc/profile.d/conda.${ext}"
        script="${script}"$'\n'"conda activate $env_name"
        file_name=$activ_path/load_latest_e3sm_unified${suffix}.${ext}
        rm -f "$file_name"
        echo "${script}" > "$file_name"
      done
    done
  done
done

# delete the tarballs and any unused packages
conda clean -y -p -t

# continue if errors happen from here on
set +e

echo "changing permissions on activation scripts"
chown -R "$USER":$group $activ_path/load_latest_e3sm_unified*
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
chown -R "$USER:$group" .
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


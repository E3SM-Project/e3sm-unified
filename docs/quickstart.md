# Quickstart Guide

```{note}
E3SM-Unified is supported only on Linux, OSX and HPC platforms. It is **not**
supported on Windows.
```

## Accessing E3SM-Unified on Supported Machines

On most E3SM-supported HPC systems, E3SM-Unified is already installed and
ready to use via a generated load script.

### Example Activation Commands

```bash
# Andes
source /ccs/proj/cli115/software/e3sm-unified/load_latest_e3sm_unified_andes.sh

# Anvil
source /lcrc/soft/climate/e3sm-unified/load_latest_e3sm_unified_anvil.sh

# Chrysalis
source /lcrc/soft/climate/e3sm-unified/load_latest_e3sm_unified_chrysalis.sh

# Compy
source /share/apps/E3SM/conda_envs/load_latest_e3sm_unified_compy.sh

# Dane
source /usr/workspace/e3sm/apps/e3sm-unified/load_latest_e3sm_unified_dane.sh

# Frontier
source /ccs/proj/cli115/software/e3sm-unified/load_latest_e3sm_unified_frontier.sh

# Perlmutter
source /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_pm-cpu.sh

# Polaris (ALCF)
source /lus/grand/projects/E3SMinput/soft/e3sm-unified/load_latest_e3sm_unified_polaris.sh

# Ruby
source /usr/workspace/e3sm/apps/e3sm-unified/load_latest_e3sm_unified_ruby.sh
```

Once the script is sourced, you'll have access to the tools provided by
E3SM-Unified. On systems deployed in a dual-layout configuration, the script
typically activates a login-friendly environment on login nodes and switches to
the compute-node environment automatically inside an interactive or batch job.

## Verifying Installation

After activation, verify that the environment is correctly loaded:

```python
python -c "import xarray, e3sm_diags, mpas_analysis, zppy"
```

On HPC systems, you can also check which package variant is active:

```bash
echo "$E3SMU_MPI"
```

Typical values are `NOMPI`, `mpich`, `openmpi`, or `SYSTEM` (for the `hpc`
variant).

## Running on Compute Nodes (Optional but Recommended)

Many E3SM-Unified tools benefit from running on compute nodes, especially when
the active deployment uses the `hpc` package variant together with
machine-specific system libraries.

Check your system documentation for how to launch interactive compute sessions
(e.g., `srun`, `salloc`, or `qsub`).

## Installing E3SM-Unified on an Unsupported System

E3SM-Unified can also be installed directly from conda-forge on Linux or macOS
systems using `miniforge3`.

### Step-by-Step (Linux):

```bash
# Install miniforge3
wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash "Miniforge3-$(uname)-$(uname -m).sh"

# Create a new environment
conda create -n e3sm-unified -c conda-forge python=3.13 e3sm-unified

# Activate it
conda activate e3sm-unified
```

If you need an MPI-enabled conda package instead of the default `nompi`
variant, select one explicitly:

```bash
conda create -n e3sm-unified -c conda-forge python=3.13 "e3sm-unified=*=mpi_mpich_*"
```

**Note**: The above instructions also work for macOS machines with Intel
hardware.

### Step-by-Step (macOS with Apple Silicon)

```bash
# starts a shell in "Rosetta" mode
arch -x86_64 /bin/bash --login

# create the conda environment to install e3sm-unified within
CONDA_SUBDIR=osx-64 conda create -n e3sm-unified python=3.13

# activate the environment and set an environmental variable
conda activate e3sm-unified
conda env config vars set CONDA_SUBDIR=osx-64

# deactivate and re-activate the environment for the above command to propagate
conda deactivate
conda activate e3sm-unified

# now you can actually install e3sm-unified
conda install -c conda-forge e3sm-unified

# exit the "Rosetta" mode shell
exit
```

## Notes for Maintainers Testing HPC Deployments

This branch uses `mache deploy` to create the HPC environments and load
scripts. If you are validating a fresh deployment rather than consuming an
existing shared install, start with the maintainer docs in
[Deployment and Testing](releasing/testing/overview.md).

**Checking if your macOS machine has Apple Silicon**:
1. Click the Apple menu at the top-left of your screen.
2. Select "About This Mac": from the dropdown menu.
3. If you see "Chip" followed by M1, M2, M3, or M4, your Mac has Apple
   silicon.

## Related Pages

* [Introduction to E3SM-Unified](introduction.md)
* [Using E3SM-Unified Tools](using-tools.md)
* [Troubleshooting](troubleshooting.md)

```{admonition} Need Help?
- Slack: #e3sm-help-postproc
- GitHub Issues: https://github.com/E3SM-Project/e3sm-unified/issues
- Email: xylar@lanl.gov
```

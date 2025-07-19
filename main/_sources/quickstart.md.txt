# Quickstart Guide

```{note}
E3SM-Unified is supported only on Linux, OSX and HPC platforms. It is **not**
supported on Windows.
```

## Accessing E3SM-Unified on Supported Machines

On most E3SM-supported HPC systems, E3SM-Unified is already installed and
ready to use via an activation script.

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

Once the script is sourced, you'll have access to all the tools provided by
E3SM-Unified in your environment.

## Verifying Installation

After activation, you can verify that the environment is correctly loaded by
testing if major packages are importable:

```python
python -c "import xarray, e3sm_diags, mpas_analysis, zppy"
```

## Running on Compute Nodes (Optional but Recommended)

Many E3SM-Unified tools (e.g., MOAB, MPAS-Analysis, NCO, TempestRemap) benefit
from running on compute nodes using MPI-enabled system builds.

Check your system documentation for how to launch interactive compute sessions
(e.g., `srun`, `salloc`, or `qsub`).

## Installing E3SM-Unified on an Unsupported System

E3SM-Unified is not officially supported on Linux or Mac laptops or
workstations, but users can install it using `miniforge3`.

### Step-by-Step (Linux/macOS):

```bash
# Install miniforge3
wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash "Miniforge3-$(uname)-$(uname -m).sh"

# Create a new environment
conda create -n esm-unified -c conda-forge e3sm-unified

# Activate it
conda activate e3sm-unified
```

Note: On macOS with M1/M2 chips, install the x86\_64 version and use Rosetta 2
for compatibility.

---

## Related Pages

* [Introduction to E3SM-Unified](introduction.md)
* [Using E3SM-Unified Tools](using-tools.md)
* [Troubleshooting](troubleshooting.md)

```{admonition} Need Help?
- Slack: #e3sm-help-postproc
- GitHub Issues: https://github.com/E3SM-Project/e3sm-unified/issues
- Email: xylar@lanl.gov
```

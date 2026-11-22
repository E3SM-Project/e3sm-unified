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

Typical values are `NOMPI` (the `nompi` variant, used on login nodes) or
`SYSTEM` (the `hpc` variant, used on compute nodes).

## Running on Compute Nodes (Optional but Recommended)

Many E3SM-Unified tools benefit from running on compute nodes, especially when
the active deployment uses the `hpc` package variant together with
machine-specific system libraries.

Check your system documentation for how to launch interactive compute sessions
(e.g., `srun`, `salloc`, or `qsub`).

## Installing E3SM-Unified on an Unsupported System

E3SM-Unified can also be installed directly from conda-forge on Linux
(`x86_64` and `aarch64`) or macOS (Intel and Apple Silicon) systems using
`miniforge3`.

### Step-by-Step (Linux and macOS):

```bash
# Install miniforge3
wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash "Miniforge3-$(uname)-$(uname -m).sh"

# Create a new environment
conda create -n e3sm-unified -c conda-forge python=3.13 e3sm-unified

# Activate it
conda activate e3sm-unified
```

This installs the default `nompi` package variant. Conda-forge MPI variants
(`mpich` and `openmpi`) have not been built since E3SM-Unified 1.12.0, so
`"e3sm-unified=*=mpi_mpich_*"` and similar build-string constraints will not
find 1.13.0 or newer. See the [Package Catalog](packages.md) for details.

**Note**: Starting with 1.14.0, E3SM-Unified is built natively for Apple
Silicon (`osx-arm64`), so the above instructions work on all Macs. Earlier
versions required installing the `osx-64` package under Rosetta.

## Notes for Maintainers Testing HPC Deployments

This branch uses `mache deploy` to create the HPC environments and load
scripts. If you are validating a fresh deployment rather than consuming an
existing shared install, start with the maintainer docs in
[Deployment and Testing](releasing/testing/overview.md).

## Related Pages

* [Introduction to E3SM-Unified](introduction.md)
* [Using E3SM-Unified Tools](using-tools.md)
* [Troubleshooting](troubleshooting.md)

```{admonition} Need Help?
- Slack: #e3sm-help-postproc
- GitHub Issues: https://github.com/E3SM-Project/e3sm-unified/issues
- Email: xylar@lanl.gov
```

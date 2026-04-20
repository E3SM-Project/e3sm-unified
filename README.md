# E3SM-Unified

![E3SM-Unified](docs/logo/e3sm_unified_logo_200.png)

E3SM-Unified is the shared analysis and post-processing environment for the
Energy Exascale Earth System Model (E3SM). It is distributed as an
`e3sm-unified` conda package and deployed on supported HPC systems with
`mache deploy`.

## Documentation

[Latest documentation](http://docs.e3sm.org/e3sm-unified/main) for users,
developers, and maintainers.

## Getting Started

E3SM-Unified supports Linux, macOS, and several E3SM-supported HPC systems.
Windows is not supported.

On supported HPC machines, source the generated load script for your system,
for example:

```bash
source /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_pm-cpu.sh
```

On laptops, workstations, or unsupported systems, install
[Miniforge3](https://github.com/conda-forge/miniforge?tab=readme-ov-file#requirements-and-installers)
and create an environment from conda-forge:

```bash
conda create -n e3sm-unified -c conda-forge python=3.13 e3sm-unified
conda activate e3sm-unified
```

If you need a specific package variant, you can select it explicitly, for
example:

```bash
conda create -n e3sm-unified -c conda-forge python=3.13 "e3sm-unified=*=mpi_mpich_*"
```

The authoritative recipe and package list live in
`recipes/e3sm-unified/e3sm-unified-feedstock/recipe/recipe.yaml`.

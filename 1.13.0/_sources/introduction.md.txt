# Introduction to E3SM-Unified

```{image} logo/e3sm_unified_logo_200.png
:align: center
:width: 200 px
```

## What is E3SM-Unified?

E3SM-Unified is a curated analysis environment for the Energy Exascale Earth
System Model (E3SM). It packages the tools most commonly used for analysis,
diagnostics, visualization, and data transformation into a single install that
can be used locally or deployed on shared HPC systems.

The core product is the `e3sm-unified` conda package. On laptops and
workstations, users typically install that package directly from conda-forge.
On supported HPC systems, maintainers deploy Pixi environments and optional
Spack-backed system-library views with `mache deploy`, then publish load
scripts for users.

## Key Features

* Combines analysis, diagnostics, and workflow tools into one install.
* Supports multiple package variants, including `nompi`, `mpich`, `openmpi`,
  and `hpc`.
* Uses machine-aware deployment on supported HPC systems through `mache`.
* Is fully open source and maintained in GitHub.

## Common Use Cases

* Diagnostics and evaluation (e.g., `e3sm_diags`, `MPAS-Analysis`)
* CMIP output conversion (`e3sm_to_cmip`)
* Time series generation, viewer creation, and archiving (`zppy`, `zstash`)
* Domain generation and mesh visualization (`cime_gen_domain`, `mosaic`)

## Supported Platforms

E3SM-Unified is available on many E3SM-supported systems:

* Andes
* Anvil
* Chrysalis
* Compy
* Dane
* Frontier
* Perlmutter
* Polaris (ALCF)
* Ruby

It can also be installed on Linux or macOS laptops for limited use (see
[Quickstart Guide](quickstart.md)). Windows is not supported.

## How the Deployment Model Works

There are two common ways to use E3SM-Unified:

* Install `e3sm-unified` directly from conda-forge on a personal system.
* Source a maintainer-provided load script on a supported HPC machine.

HPC deployments can use a dual-layout setup, where login nodes use a lighter
Pixi environment and compute nodes switch to an MPI-capable environment with
system libraries provided through Spack. This lets the same load script work
well on both login and compute nodes.

## Getting Help

* [Quickstart Guide](quickstart.md)
* GitHub: [E3SM-Unified repository](https://github.com/E3SM-Project/e3sm-unified)
* Slack: `#e3sm-help-postproc`
* Issues/questions: GitHub Issues or contact [xylar@lanl.gov](mailto:xylar@lanl.gov)

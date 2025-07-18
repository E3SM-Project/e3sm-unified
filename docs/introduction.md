# Introduction to E3SM-Unified

```{image} logo/e3sm_unified_logo_200.png
:align: center
:width: 200 px
```

## What is E3SM-Unified?

E3SM-Unified is a unified conda-based environment that provides pre- and
post-processing tools for the Energy Exascale Earth System Model (E3SM). It is
designed to streamline the analysis, visualization, and transformation of model
output for scientists and developers.

This environment bundles together a curated set of Python and compiled tools
that work well across supported platforms, particularly on E3SM-managed
high-performance computing (HPC) systems.

## Key Features

* Combines dozens of packages into one environment, eliminating setup friction.
* Maintains consistency across HPC platforms (Anvil, Chrysalis, Compy, etc.).
* Offers both Conda and Spack-installed components for MPI performance.
* Fully open source and community-maintained via GitHub.

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

## Getting Help

* [Quickstart Guide](quickstart.md)
* GitHub: [E3SM-Unified repository](https://github.com/E3SM-Project/e3sm-unified)
* Slack: `#e3sm-help-postproc`
* Issues/questions: GitHub Issues or contact [xylar@lanl.gov](mailto:xylar@lanl.gov)

# Package Catalog

This page lists the packages in the E3SM-Unified `1.14.0` recipe, along with
the most important package constraints. The authoritative source is
`recipes/e3sm-unified/e3sm-unified-feedstock/recipe/recipe.yaml`.

---

## Notes

E3SM-Unified `1.14.0` is published on conda-forge for Python 3.12, 3.13 and
3.14 on `linux-64`, `linux-aarch64`, `osx-64` and `osx-arm64`.

The exact environment depends on the selected package variant. Two variants
are published:

* `nompi` is the default conda-only variant. Use it on laptops, workstations
  and unsupported systems.
* `hpc` omits several system-library-heavy packages from the conda package so
  they can be provided by the HPC deployment through Spack. It is meant for
  shared deployments on supported HPC machines.

Conda-forge MPI variants (`mpich` and `openmpi`) were last published for
E3SM-Unified `1.12.0`. Starting with `1.13.0`, they are not built because
`e3sm_diags` requires the `nompi` build of `esmf`
([e3sm_diags#1051](https://github.com/E3SM-Project/e3sm_diags/issues/1051)).

## Core Tooling

| Package Name | Version Constraint |
|--------------|--------------------|
| cdo | unpinned, Linux only |
| chemdyg | ==1.1.1 |
| cprnc | ==1.1.7 |
| e3sm_compareview | ==1.11.5 |
| e3sm_diags | ==3.3.0 |
| e3sm-quickview | ==2.11.0 |
| e3sm_to_cmip | ==1.15.0 |
| e3sm-tools | ==3.1.0 on Linux |
| geometric_features | ==1.6.3 |
| globus-cli | >=3.15.0 |
| livvext | ==1.1.2 |
| livvkit | ==3.3.1 |
| mache | ==5.5.2 |
| mosaic | ==1.3.1 |
| mpas-analysis | ==1.16.0 |
| mpas_tools | ==2.2.1 |
| pcmdi_metrics | ==4.2.1 |
| squadgen | ==1.2.2 on Linux |
| uxarray-base | >=2026.09.1 |
| xcdat | ==0.11.5 |
| zppy | ==3.3.0 |
| zppy-interfaces | ==0.3.0 |
| zstash | ==1.6.1 on Linux |

## Variant-Sensitive Packages

| Package Name | Version Constraint |
|--------------|--------------------|
| moab | ==5.6.0 in the `nompi` variant |
| nco | ==5.4.2 in the `nompi` variant |
| tempest-remap | ==2.2.0 in the `nompi` variant |
| tempest-extremes | ==2.4.2 in the `nompi` variant |
| cython | included in the `hpc` variant |
| cf-units | >=2.0.0 in the `hpc` variant |
| pandas | included in the `hpc` variant |
| psutil | included in the `hpc` variant |

In `hpc` deployments, ESMF, MOAB, NCO, TempestRemap and TempestExtremes come
from Spack. `mpi4py` and `ilamb` are installed with `pip` against the system
MPI (see the `[spack]` and `[hpc]` sections of `deploy/pins.cfg`).

## Selected Shared Dependencies

| Package Name | Version Constraint |
|--------------|--------------------|
| cartopy | ==0.26.0 |
| dask | ==2026.8.0 |
| esmf | ==8.9.1 |
| esmpy | ==8.9.1 |
| hdf5 | ==1.14.6 |
| libnetcdf | ==4.10.1 |
| matplotlib-base | ==3.11.1 |
| ncview | ==2.1.11 |
| ncvis-climate | ==2026.10.07 |
| netcdf4 | ==1.7.4 `nompi_*` |
| numpy | >=2.0.0,<3.0.0 |
| output_viewer | ==1.3.3 |
| proj | ==9.9.0 |
| pyproj | ==3.8.0 |
| pytorch | ==2.13.0 |
| xarray | ==2026.7.0 |
| xesmf | ==0.9.2 |

R and the R packages (`r-tidyverse`, `r-dplyr`, `r-ggplot2`) were included in
`1.13.0` but are not in `1.14.0`. NCO 5.4.2 requires GSL 2.8, the only R built
against GSL 2.8 is R 4.6, and these R packages do not yet have R 4.6 builds.

---

Refer to the recipe itself for the full dependency list and all
platform/variant-specific conditionals.

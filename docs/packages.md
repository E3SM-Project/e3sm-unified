# Package Catalog

This page provides a complete inventory of packages included in the latest
E3SM-Unified recipe (`1.13.0rc1` at the time of this branch), along with the
most important package constraints. The authoritative source is
`recipes/e3sm-unified/e3sm-unified-feedstock/recipe/recipe.yaml`.

---

## Notes

The exact environment depends on the selected package variant:

* `nompi` is the default conda-only variant.
* `mpich` and `openmpi` add MPI-enabled conda packages.
* `hpc` omits several system-library-heavy packages from the conda package so
  they can be provided by the HPC deployment through Spack.

## Core Tooling

| Package Name | Version Constraint |
|--------------|--------------------|
| chemdyg | ==1.1.1 |
| e3sm_diags | ==3.1.0 |
| e3sm_to_cmip | ==1.13.0 |
| geometric_features | ==1.6.1 |
| livvkit | ==3.2.0 |
| mache | ==3.3.0rc1 |
| mosaic | ==1.2.1 |
| mpas-analysis | ==1.14.0 |
| mpas_tools | ==1.4.0 |
| pcmdi_metrics | ==4.0.1 |
| uxarray | >=2024.12.0 |
| xcdat | ==0.10.1 |
| zppy | ==3.1.0 |
| zppy-interfaces | ==0.2.0 |
| zstash | ==1.5.0 on Linux |

## Variant-Sensitive Packages

| Package Name | Version Constraint |
|--------------|--------------------|
| moab | ==5.6.0 for non-`hpc` variants |
| nco | ==5.3.6 for non-`hpc` variants |
| tempest-remap | ==2.2.0 for non-`hpc` variants |
| tempest-extremes | ==2.4 for non-`hpc` variants |
| ilamb | ==2.7.2 for MPI-enabled conda variants |
| mpi4py | included for MPI-enabled conda variants |
| openssh | included for the `openmpi` variant |
| cython | included for the `hpc` variant |
| cf-units | >=2.0.0 for the `hpc` variant |
| pandas | included for the `hpc` variant |
| psutil | included for the `hpc` variant |

## Selected Shared Dependencies

| Package Name | Version Constraint |
|--------------|--------------------|
| dask | ==2025.9.1 |
| esmf | ==8.9.0 |
| esmpy | ==8.9.0 |
| hdf5 | ==1.14.6 |
| libnetcdf | ==4.9.3 |
| matplotlib-base | ==3.10.6 |
| ncview | ==2.1.8 |
| netcdf4 | ==1.7.2 `nompi_*` |
| numpy | >=2.0.0 |
| output_viewer | ==1.3.3 |
| proj | ==9.6.2 |
| pyproj | ==3.7.2 |
| xarray | ==2025.9.0 |
| xesmf | ==0.8.8 |

---

Refer to the recipe itself for the full dependency list and all
platform/variant-specific conditionals.

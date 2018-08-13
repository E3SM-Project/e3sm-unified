#!/bin/bash
BUILD=0
VERSION=1.2.2


conda metapackage -c conda-forge -c e3sm -c cdat \
    e3sm-unified ${VERSION} --build-number ${BUILD} \
    --dependencies \
    "cdat ==8.0" \
    "cdat_info ==8.0" \
    "distarray ==2.12.2" \
    "cdms2 ==3.0.1" \
    "cdtime ==3.0" \
    "cdutil ==8.0" \
    "genutil ==8.0" \
    "vtk-cdat ==8.0.1.8.0" \
    "dv3d ==8.0" \
    "vcs ==8.0" \
    "vcsaddons ==8.0" \
    "output_viewer ==1.2.5" \
    "wk ==8.0" \
    "thermo ==8.0" \
    "cdp ==1.3.3" \
    "e3sm_nex ==0.0.2" \
    "e3sm_diags ==1.3.4" \
    "cibots ==0.2" \
    "xarray ==0.10.8" \
    "dask ==0.18.2" \
    "nco ==4.7.6" \
    "lxml" \
    "sympy" \
    "pyproj" \
    "pytest" \
    "shapely" \
    "cartopy" \
    "progressbar2" \
    "pillow" \
    "numpy >1.13" \
    "scipy" \
    "matplotlib" \
    "basemap" \
    "blas" \
    "jupyter" \
    "nb_conda" \
    "ipython" \
    "plotly" \
    "bottleneck" \
    "hdf5 ==1.10.2" \
    "netcdf4 ==1.4.1" \
    "evtk ==1.1.1" \
    "f90nml" \
    "globus-cli" \
    "globus-sdk" \
    "mpas_analysis ==1.0" \
    "processflow ==2.0.2" \
    "tabulate" \
    "cmocean" \
    "gsw" \
    "libnetcdf ==4.6.1" \
    "livvkit ==2.1.6"


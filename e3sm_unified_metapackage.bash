export UVCDAT_VERSION=2.12
export BUILD=0
export VERSION=1.1.3


conda metapackage -c conda-forge -c e3sm -c acme -c uvcdat \
    e3sm-unified ${VERSION} --build-number ${BUILD}  \
    --dependencies \
    "cdat_info ==${UVCDAT_VERSION}" \
    "distarray ==${UVCDAT_VERSION}" \
    "cdms2 ==${UVCDAT_VERSION}" \
    "cdtime ==${UVCDAT_VERSION}" \
    "cdutil ==${UVCDAT_VERSION}" \
    "genutil ==${UVCDAT_VERSION}" \
    "vtk-cdat ==7.1.0.${UVCDAT_VERSION}" \
    "dv3d ==${UVCDAT_VERSION}" \
    "vcs ==${UVCDAT_VERSION}" \
    "vcsaddons ==${UVCDAT_VERSION}" \
    "acme_diags ==1.2.1" \
    "cibots ==0.2" \
    "output_viewer ==1.2.2" \
    "xarray ==0.10.0" \
    "dask ==0.16.0" \
    "nco ==4.7.3" \
    "lxml ==4.1.1" \
    "sympy ==1.1.1" \
    "pyproj ==1.9.5.1" \
    "pytest ==3.2.2" \
    "shapely  ==1.6.2" \
    "cartopy  ==0.15.1" \
    "progressbar ==2.3" \
    "pillow ==4.3.0" \
    "numpy >1.13" \
    "scipy <1.0.0" \
    "matplotlib" \
    "basemap" \
    "blas" \
    "jupyter" \
    "nb_conda" \
    "ipython" \
    "plotly" \
    "bottleneck ==1.2.1" \
    "hdf5 ==1.8.18" \
    "netcdf4 ==1.3.1" \
    "pyevtk ==1.0.1" \
    "f90nml" \
    "globus-cli" \
    "globus-sdk" \
    "mpas_analysis ==0.7.0" \
    "processflow ==1.0.1"

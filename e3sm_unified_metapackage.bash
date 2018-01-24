export UVCDAT_VERSION=2.12
export BUILD=0
export VERSION=1.1.2

# For nightly set OPERATOR to ">="
export OPERATOR="=="

conda metapackage -c conda-forge -c e3sm -c acme -c uvcdat \
    e3sm-unified ${VERSION} --build-number ${BUILD}  \
    --dependencies \
    "cdat_info ${OPERATOR}${UVCDAT_VERSION}" \
    "distarray ${OPERATOR}${UVCDAT_VERSION}" \
    "cdms2 ${OPERATOR}${UVCDAT_VERSION}" \
    "cdtime ${OPERATOR}${UVCDAT_VERSION}" \
    "cdutil ${OPERATOR}${UVCDAT_VERSION}" \
    "genutil ${OPERATOR}${UVCDAT_VERSION}" \
    "vtk-cdat ${OPERATOR}7.1.0.${UVCDAT_VERSION}" \
    "dv3d ${OPERATOR}${UVCDAT_VERSION}" \
    "vcs ${OPERATOR}${UVCDAT_VERSION}" \
    "vcsaddons ${OPERATOR}${UVCDAT_VERSION}" \
    "acme_diags ${OPERATOR}1.1.0" \
    "cibots ${OPERATOR}0.2" \
    "output_viewer ${OPERATOR}1.2.2" \
    "xarray ${OPERATOR}0.10.0" \
    "dask ${OPERATOR}0.16.0" \
    "nco ${OPERATOR}4.7.0" \
    "lxml ${OPERATOR}4.1.1" \
    "sympy ${OPERATOR}1.1.1" \
    "pyproj ${OPERATOR}1.9.5.1" \
    "pytest ${OPERATOR}3.2.2" \
    "shapely  ${OPERATOR}1.6.2" \
    "cartopy  ${OPERATOR}0.15.1" \
    "progressbar ${OPERATOR}2.3" \
    "pillow ${OPERATOR}4.3.0" \
    "numpy >1.13" \
    "scipy <1.0.0" \
    "matplotlib" \
    "basemap" \
    "blas" \
    "jupyter" \
    "nb_conda" \
    "ipython" \
    "plotly" \
    "bottleneck ${OPERATOR}1.2.1" \
    "hdf5 ${OPERATOR}1.8.18" \
    "netcdf4 ${OPERATOR}1.3.1" \
    "pyevtk ${OPERATOR}1.0.1" \
    "f90nml" \
    "globus-cli" \
    "globus-sdk"

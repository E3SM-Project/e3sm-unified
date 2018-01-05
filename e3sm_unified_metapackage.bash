export UVCDAT_VERSION=2.12
export BUILD=0
export VERSION=1.1.1

# For nightly set OPERATOR to ">="
export OPERATOR="=="

conda metapackage -c conda-forge -c uvcdat -c acme -c opengeostat \
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
    "thermo ${OPERATOR}${UVCDAT_VERSION}" \
    "wk ${OPERATOR}${UVCDAT_VERSION}" \
    "vistrails ${OPERATOR}${UVCDAT_VERSION}" \
    "xmgrace ${OPERATOR}${UVCDAT_VERSION}" \
    "hdf5tools ${OPERATOR}${UVCDAT_VERSION}" \
    "asciidata ${OPERATOR}${UVCDAT_VERSION}" \
    "binaryio ${OPERATOR}${UVCDAT_VERSION}" \
    "cssgrid ${OPERATOR}${UVCDAT_VERSION}" \
    "dsgrid ${OPERATOR}${UVCDAT_VERSION}" \
    "lmoments ${OPERATOR}${UVCDAT_VERSION}" \
    "natgrid ${OPERATOR}${UVCDAT_VERSION}" \
    "ort ${OPERATOR}${UVCDAT_VERSION}" \
    "regridpack ${OPERATOR}${UVCDAT_VERSION}" \
    "shgrid ${OPERATOR}${UVCDAT_VERSION}" \
    "trends ${OPERATOR}${UVCDAT_VERSION}" \
    "zonalmeans ${OPERATOR}${UVCDAT_VERSION}" \
    "cdp ${OPERATOR}1.1.0" \
    "acme_diags ${OPERATOR}1.0.0" \
    "cibots ${OPERATOR}0.2" \
    "output_viewer ${OPERATOR}1.2.2" \
    "xarray ${OPERATOR}0.9.6" \
    "dask ${OPERATOR}0.15.2" \
    "nco ${OPERATOR}4.6.9" \
    "lxml ${OPERATOR}3.8.0" \
    "sympy ${OPERATOR}1.1.1" \
    "pyproj ${OPERATOR}1.9.5.1" \
    "pytest ${OPERATOR}3.2.2" \
    "shapely  ${OPERATOR}1.6.1" \
    "cartopy  ${OPERATOR}0.15.1" \
    "progressbar ${OPERATOR}2.3" \
    "matplotlib" \
    "basemap" \
    "jupyter" \
    "nb_conda" \
    "ipython" \
    "bottleneck ${OPERATOR}1.2.1" \
    "netcdf4 ${OPERATOR}1.2.9" \
    "pyevtk ${OPERATOR}1.0.0"
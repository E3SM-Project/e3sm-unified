# bash snippet for adding e3sm-unified-specific environment variables

export E3SMU_SCRIPT="${E3SM_UNIFIED_LOAD_SCRIPT}"
export E3SMU_MACHINE="${E3SM_UNIFIED_MACHINE:-}"
export CIME_MODEL="ENVIRONMENT_RUNNING_E3SM_UNIFIED_USE_ANOTHER_TERMINAL"
export HDF5_USE_FILE_LOCKING=FALSE

if [ "${MACHE_DEPLOY_ACTIVE_PIXI_MPI:-}" = "nompi" ]; then
    export E3SMU_MPI="NOMPI"
else
    if [ "${MACHE_DEPLOY_ACTIVE_PIXI_MPI:-}" = "hpc" ]; then
        export E3SMU_MPI="SYSTEM"
    else
        export E3SMU_MPI="${MACHE_DEPLOY_ACTIVE_PIXI_MPI}"
    fi
fi

if command -v nc-config >/dev/null 2>&1; then
    export NETCDF="$(dirname "$(dirname "$(command -v nc-config)")")"
fi

if command -v nf-config >/dev/null 2>&1; then
    export NETCDFF="$(dirname "$(dirname "$(command -v nf-config)")")"
fi

if command -v pnetcdf-config >/dev/null 2>&1; then
    export PNETCDF="$(dirname "$(dirname "$(command -v pnetcdf-config)")")"
fi

if [ -n "${MACHE_DEPLOY_SPACK_LIBRARY_VIEW:-}" ]; then
    export PIO="${MACHE_DEPLOY_SPACK_LIBRARY_VIEW}"
    export METIS_ROOT="${MACHE_DEPLOY_SPACK_LIBRARY_VIEW}"
    export PARMETIS_ROOT="${MACHE_DEPLOY_SPACK_LIBRARY_VIEW}"
    if [ -f "${MACHE_DEPLOY_SPACK_LIBRARY_VIEW}/lib/esmf.mk" ]; then
        export ESMFMKFILE="${MACHE_DEPLOY_SPACK_LIBRARY_VIEW}/lib/esmf.mk"
    fi
elif [ -n "${CONDA_PREFIX:-}" ] && [ -f "${CONDA_PREFIX}/lib/esmf.mk" ]; then
    export ESMFMKFILE="${CONDA_PREFIX}/lib/esmf.mk"
fi

#!/usr/bin/env python
import subprocess

specs = ['python=3.10',
         'ncvis-climate 2023.09.12',
         'libnetcdf 4.9.2 mpi_mpich_*',
         'chemdyg 0.1.4',
         'e3sm_diags 2.9.0',
         'e3sm_to_cmip 1.11.0',
         'geometric_features 1.2.0',
         'globus-cli >=3.15.0',
         'ilamb 2.7',
         'ipython',
         'jupyter',
         'livvkit 3.0.1',
         'mache 1.17.0',
         'moab 5.5.1',
         'mpas-analysis 1.9.1rc1',
         'mpas_tools 0.27.0',
         'nco 5.1.9',
         'pcmdi_metrics 2.3.1',
         'tempest-remap 2.2.0',
         'tempest-extremes 2.2.1',
         'xcdat 0.6.1',
         'zppy 2.3.1',
         'zstash 1.4.2rc1',
         'mpich',
         'blas',
         'bottleneck',
         'cartopy >=0.17.0',
         'cdat_info 8.2.1',
         'cdms2 3.1.5',
         'cdtime 3.1.4',
         'cdutil 8.2.1',
         'cmocean',
         'dask 2023.6.0',
         'dogpile.cache',
         'eofs',
         'esmf 8.4.2 mpi_mpich_*',
         'esmpy 8.4.2',
         'f90nml',
         'ffmpeg',
         'genutil 8.2.1',
         'globus-sdk',
         'gsw',
         'hdf5 1.14.2 mpi_mpich_*',
         'ipygany',
         'lxml',
         'matplotlib 3.7.1',
         'metpy',
         'mpi4py',
         'nb_conda',
         'nb_conda_kernels',
         'ncview 2.1.8',
         'ncvis-climate 2023.09.12',
         'netcdf4 1.6.4 nompi_*',
         'notebook <7.0.0',
         'numpy >1.13',
         'output_viewer 1.3.3',
         'pillow',
         'plotly',
         'progressbar2',
         'proj 9.3.1',
         'pyevtk',
         'pyproj 3.6.1',
         'pyremap',
         'pytest',
         'pywavelets',
         'scikit-image',
         'scipy >=0.9.0',
         'shapely',
         'sympy >=0.7.6',
         'tabulate',
         'xarray 2023.5.0',
         'xesmf',
         'cython',
         'cf-units >=2.0.0',
         'psutil',
         'pandas'
         ]

base_command = ['conda', 'create', '-y', '-n', 'dry-run', '--dry-run',
                '--override-channels',
                '-c', 'conda-forge/label/mpas_analysis_dev',
                '-c', 'conda-forge/label/zstash_dev',
                '-c', 'conda-forge']

prevEnd = None
highestValid = -1
lowestInvalid = len(specs)
endIndex = len(specs)
while highestValid != lowestInvalid-1:
    subset_specs = specs[0:endIndex]
    print('last: {}'.format(subset_specs[-1]))

    command = base_command + subset_specs

    try:
        subprocess.check_call(command, stdout=subprocess.DEVNULL)
        highestValid = endIndex-1
        endIndex = int(0.5 + 0.5*(highestValid + lowestInvalid)) + 1
        print('  Succeeded!')
    except subprocess.CalledProcessError:
        lowestInvalid = endIndex-1
        endIndex = int(0.5 + 0.5*(highestValid + lowestInvalid)) + 1
        print('  Failed!')
    print('  valid: {}, invalid: {}, end: {}'.format(
        highestValid, lowestInvalid, endIndex))

if lowestInvalid == len(specs):
    print('No failures!')
else:
    print('First failing package: {}'.format(specs[lowestInvalid]))

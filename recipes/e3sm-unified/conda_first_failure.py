#!/usr/bin/env python
import subprocess

specs = ['python=3.10',
         'openssl >=3.1.0,<4.0a0',
         #'globus-cli',
         'hdf5=1.14.0 nompi_*',
         'libnetcdf 4.9.2 nompi_*',
         'netcdf4 1.6.4 nompi_*',
         'xarray 2023.5.0',
         'dask 2023.6.0',
         'proj 9.2.1',
         'pyproj 3.6.0',
         #'e3sm_diags 2.8.0',
         #'e3sm_to_cmip 1.9.1',
         'geometric_features 1.2.0',
         'ipython',
         'jupyter',
         'livvkit 3.0.1',
         'mache 1.16.0rc1',
         'mpas-analysis 1.9.0rc1',
         'mpas_tools 0.20.0',
         'pcmdi_metrics 2.3.1',
         #'xcdat 0.5.0',
         #'zstash 1.3.0',
         'zppy 2.3.0rc1',
         'blas',
         'bottleneck',
         'cartopy >=0.17.0',
         'cdat_info 8.2.1',
         'cdms2 3.1.5',
         'cdtime 3.1.4',
         'cdutil 8.2.1',
         'cmocean',
         'dogpile.cache',
         'eofs',
         'f90nml',
         'ffmpeg',
         'genutil 8.2.1',
         'globus-sdk',
         'gsw',
         'ipygany',
         'lxml',
         'matplotlib',
         'metpy',
         'nb_conda',
         'nb_conda_kernels',
         'ncview 2.1.8',
         'ncvis-climate',
         'numpy >1.13',
         'output_viewer 1.3.3',
         'pillow',
         'plotly',
         'progressbar2',
         'pyevtk',
         'pyremap',
         'pytest',
         'pywavelets',
         'scikit-image',
         'scipy >=0.9.0',
         'shapely',
         'sympy >=0.7.6',
         'tabulate',
         'xesmf',
         'cython',
         'cf-units >=2.0.0',
         'psutil',
         'pandas',
         ]

base_command = ['mamba', 'create', '-y', '-n', 'test', '--dry-run',
                '--override-channels',
                '-c', 'conda-forge/label/mache_dev',
                '-c', 'conda-forge/label/mpas_analysis_dev',
                '-c', 'conda-forge/label/zppy_dev',
                '-c', 'conda-forge',
                '-c', 'defaults']

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

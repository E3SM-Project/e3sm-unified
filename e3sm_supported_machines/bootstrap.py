#!/usr/bin/env python3

import os
import subprocess
import shutil
from jinja2 import Template
from importlib import resources
from configparser import ConfigParser

from mache import discover_machine
from mache.spack import make_spack_env, get_spack_script, \
    get_modules_env_vars_and_mpi_compilers
from mache.permissions import update_permissions
from shared import (
    check_call,
    get_conda_base,
    get_rc_dev_labels,
    install_miniforge3,
    parse_args,
)


def get_config(config_file, machine):
    here = os.path.abspath(os.path.dirname(__file__))
    default_config = os.path.join(here, 'default.cfg')
    config = ConfigParser()
    print('Adding config options from:')
    print(f'  {default_config}')
    config.read(default_config)

    if machine is not None:
        machine_config = resources.files('mache.machines') / f'{machine}.cfg'
        print(f'  {str(machine_config)}')
        config.read(str(machine_config))

        local_mache_config = os.path.join(here, f'{machine}.cfg')
        if os.path.exists(local_mache_config):
            print(f'  {str(local_mache_config)}')
            config.read(local_mache_config)

    if config_file is not None:
        print(f'  {config_file}')
        config.read(config_file)

    return config


def get_env_setup(args, config, machine):

    if args.python is not None:
        python = args.python
    else:
        python = config.get('e3sm_unified', 'python')

    if args.recreate is not None:
        recreate = args.recreate
    else:
        recreate = config.getboolean('e3sm_unified', 'recreate')

    if args.compiler is not None:
        compiler = args.compiler
        if compiler == 'None':
            compiler = None
    elif config.has_option('e3sm_unified', 'compiler'):
        compiler = config.get('e3sm_unified', 'compiler')
    else:
        compiler = None

    if args.mpi is not None:
        mpi = args.mpi
    elif config.has_option('e3sm_unified', 'mpi'):
        mpi = config.get('e3sm_unified', 'mpi')
    else:
        mpi = 'mpich'

    if machine is not None and compiler is not None:
        conda_mpi = 'hpc'
        env_suffix = '_compute'
    else:
        conda_mpi = mpi
        env_suffix = '_login'

    if machine is not None:
        activ_suffix = f'_{machine}'
    else:
        activ_suffix = ''

    activ_path = config.get('e3sm_unified', 'base_path')

    return python, recreate, compiler, mpi, conda_mpi,  activ_suffix, \
        env_suffix, activ_path


def build_env(is_test, recreate, compiler, mpi, conda_mpi, version,
              python, conda_base, activ_suffix, env_suffix, activate_base,
              local_conda_build, config):

    if compiler is not None:
        build_dir = f'build{activ_suffix}'

        try:
            shutil.rmtree(build_dir)
        except OSError:
            pass
        try:
            os.makedirs(build_dir)
        except FileExistsError:
            pass

        os.chdir(build_dir)

    env_name = f'e3sm_unified_{version}{env_suffix}'
    env_path = os.path.join(conda_base, 'envs', env_name)

    if conda_mpi in ['nompi', 'hpc']:
        mpi_prefix = conda_mpi
    else:
        mpi_prefix = f'mpi_{conda_mpi}'

    nco_spec = config.get('spack_specs', 'nco')

    # whether to remove esmpy and xesmf, becasue they will be installed
    # manually with pip
    remove_esmf_esmpy_xesmf = (
        config.get('e3sm_unified', 'esmpy') != 'None' and
        config.get('e3sm_unified', 'xesmf') != 'None')

    if is_test:

        channels = '--override-channels'
        if local_conda_build is not None:
            channels = f'{channels} -c {local_conda_build}'

        if 'rc' in version:
            channels = f'{channels} -c conda-forge/label/e3sm_unified_dev'

        meta_yaml_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "recipes",
            "e3sm-unified",
            "meta.yaml"
        )
        dev_labels = get_rc_dev_labels(meta_yaml_path)
        for dev_label in dev_labels:
            channels = f'{channels} -c conda-forge/label/{dev_label}'
        channels = f'{channels} ' \
                   f'-c conda-forge '
    else:
        channels = '--override-channels -c conda-forge'

    packages = f'python={python} pip "setuptools>=41.2" setuptools_scm ' \
               f'setuptools-git-versioning'

    source_activation_scripts = \
        f'source {conda_base}/etc/profile.d/conda.sh'

    activate_env = f'{source_activation_scripts} && conda activate {env_name}'

    if not os.path.exists(env_path) or recreate:
        print(f'creating {env_name}')
        packages = f'{packages} "e3sm-unified={version}={mpi_prefix}_*"'
        commands = f'{activate_base} && ' \
                   f'conda create -y -n {env_name} {channels} {packages}'
        check_call(commands)

        if conda_mpi == 'hpc':
            remove_packages = 'tempest-remap'
            if nco_spec != 'None':
                remove_packages = f'nco {remove_packages}'

            if remove_esmf_esmpy_xesmf:
                remove_packages = f'{remove_packages} esmf esmpy xesmf'

            # remove conda-forge versions so we're sure to use Spack versions
            commands = f'{activate_base} && conda remove -y --force ' \
                       f'-n {env_name} {remove_packages}'
            check_call(commands)

    else:
        print(f'{env_name} already exists')

    return env_path, env_name, activate_env, channels


def install_mache_from_branch(activate_env, fork, branch):
    print('Clone and install local mache\n')
    commands = f'{activate_env} && ' \
               f'cd build_mache/mache && ' \
               f'python -m pip install --no-deps .'

    check_call(commands)


def build_sys_ilamb_esmpy(config, machine, compiler, mpi, template_path,
                          activate_env, channels, spack_base):

    mpi4py_version = config.get('e3sm_unified', 'mpi4py')
    ilamb_version = config.get('e3sm_unified', 'ilamb')
    build_mpi4py = mpi4py_version != 'None'
    build_ilamb = ilamb_version != 'None'

    esmpy_version = config.get('e3sm_unified', 'esmpy')
    build_esmpy = esmpy_version != 'None'

    xesmf_version = config.get('e3sm_unified', 'xesmf')
    build_xesmf = xesmf_version != 'None'

    mpicc, _, _, modules = \
        get_modules_env_vars_and_mpi_compilers(machine, compiler, mpi,
                                               shell='sh')

    script_filename = 'build_ilamb_esmpy_xesmf.bash'

    with open(f'{template_path}/build.template', 'r') as f:
        template = Template(f.read())

    # need to activate the conda environment to install mpi4py and ilamb, and
    # possibly for compilers and MPI library (if not on a supported machine)
    activate_env_lines = activate_env.replace(' && ', '\n')
    modules = f'{activate_env_lines}\n{modules}'

    spack_view = f'{spack_base}/var/spack/environments/' \
                 f'e3sm_spack_env/.spack-env/view'
    script = template.render(
        mpicc=mpicc, modules=modules, template_path=template_path,
        mpi4py_version=mpi4py_version, build_mpi4py=str(build_mpi4py),
        ilamb_version=ilamb_version, build_ilamb=str(build_ilamb),
        ilamb_channels=channels, esmpy_version=esmpy_version,
        build_esmpy=str(build_esmpy), xesmf_version=xesmf_version,
        build_xesmf=str(build_xesmf), spack_view=spack_view)
    print(f'Writing {script_filename}')
    with open(script_filename, 'w') as handle:
        handle.write(script)

    command = f'/bin/bash {script_filename}'
    check_call(command)

    if build_esmpy:
        # use spack esmf
        esmf_mk = f'export ESMFMKFILE={spack_view}/lib/esmf.mk'
    else:
        # use conda esmf
        esmf_mk = 'export ESMFMKFILE=${CONDA_PREFIX}/lib/esmf.mk'
    return esmf_mk


def build_spack_env(config, machine, compiler, mpi, env_name, tmpdir):

    base_path = config.get('e3sm_unified', 'base_path')
    spack_base_path = (
        f'{base_path}/{env_name}/{machine}/spack/spack_for_{compiler}_{mpi}'
    )

    if config.has_option('e3sm_unified', 'use_e3sm_hdf5_netcdf'):
        use_e3sm_hdf5_netcdf = config.getboolean('e3sm_unified',
                                                 'use_e3sm_hdf5_netcdf')
    else:
        use_e3sm_hdf5_netcdf = False

    if config.has_option('e3sm_unified', 'spack_mirror'):
        spack_mirror = config.get('e3sm_unified', 'spack_mirror')
    else:
        spack_mirror = None

    specs = list()
    section = config['spack_specs']
    for option in section:
        # skip redundant specs if using E3SM packages
        if use_e3sm_hdf5_netcdf and \
                option in ['hdf5', 'netcdf_c', 'netcdf_fortran',
                           'parallel_netcdf']:
            continue
        value = section[option]
        if value != '':
            specs.append(f'{value}')

    make_spack_env(spack_path=spack_base_path, env_name='e3sm_spack_env',
                   spack_specs=specs, compiler=compiler, mpi=mpi,
                   machine=machine, tmpdir=tmpdir, include_e3sm_lapack=True,
                   include_e3sm_hdf5_netcdf=use_e3sm_hdf5_netcdf,
                   spack_mirror=spack_mirror)

    return spack_base_path


def write_load_e3sm_unified(template_path, activ_path, conda_base, is_test,
                            version, activ_suffix, env_name, env_nompi,
                            sys_info, ext, machine, spack_script):

    try:
        os.makedirs(activ_path)
    except FileExistsError:
        pass

    if is_test:
        prefix = f'test_e3sm_unified_{version}'
    else:
        prefix = f'load_e3sm_unified_{version}'

    script_filename = os.path.join(activ_path,
                                   f'{prefix}{activ_suffix}.{ext}')

    filename = os.path.join(template_path,
                            f'load_e3sm_unified.{ext}.template')
    with open(filename, 'r') as f:
        template = Template(f.read())
    if ext == 'sh':
        env_vars = '\n  '.join(sys_info['env_vars'])
    elif ext == 'csh':
        env_vars = [var.replace('export', 'setenv').replace('=', ' ') for var
                    in sys_info['env_vars']]
        env_vars = '\n  '.join(env_vars)
    else:
        raise ValueError(f'Unexpected extension {ext}')

    # the type of environment on compute nodes
    if env_name == env_nompi:
        env_type = 'NOMPI'
    else:
        env_type = 'SYSTEM'

    script = template.render(conda_base=conda_base, env_name=env_name,
                             env_type=env_type,
                             script_filename=script_filename,
                             env_nompi=env_nompi,
                             spack='\n  '.join(spack_script.split('\n')),
                             modules='\n  '.join(sys_info['modules']),
                             env_vars=env_vars,
                             machine=machine)

    # strip out redundant blank lines
    lines = list()
    prev_line = ''
    for line in script.split('\n'):
        line = line.strip()
        if line != '' or prev_line != '':
            lines.append(line)
        prev_line = line

    lines.append('')

    script = '\n'.join(lines)

    print(f'Writing {script_filename}')
    with open(script_filename, 'w') as handle:
        handle.write(script)

    return script_filename


def check_env(script_filename, env_name, conda_mpi, machine):
    print(f'Checking the environment {env_name}')

    activate = f'source {script_filename}'

    imports = ['mpas_analysis', 'livvkit',
               'IPython', 'globus_cli', 'zstash']
    if conda_mpi not in ['nompi', 'hpc']:
        imports.append('ILAMB')
        imports.append('esmpy')

    commands = [['mpas_analysis', '-h'],
                ['livv', '--version'],
                ['globus', '--help'],
                ['zstash', '--help']]

    if machine is None:
        # on HPC machines, these only work on compute nodes because of mpi4py
        commands.append(['e3sm_diags', '--help'])
        imports.append('acme_diags')

    for import_name in imports:
        command = f'{activate} && python -c "import {import_name}"'
        test_command(command, os.environ, import_name)

    for command in commands:
        package = command[0]
        command_str = ' '.join(command)
        command = f'{activate} && {command_str}'
        test_command(command, os.environ, package)


def test_command(command, env, package):
    try:
        check_call(command, env=env)
    except subprocess.CalledProcessError as e:
        print(f'  {package} failed')
        raise e
    print(f'  {package} passes')


def main():
    args = parse_args(bootstrap=True)

    source_path = os.getcwd()
    template_path = f'{source_path}/templates'

    version = args.version
    env_name = f'e3sm_unified_{version}'.replace('.', '_')

    machine = args.machine
    print(f'arg: {machine}')
    if machine is None:
        machine = discover_machine()
        print(f'discovered: {machine}')

    config = get_config(args.config_file, machine)

    local_mache = args.mache_fork is not None and args.mache_branch is not None

    if args.release:
        is_test = False
    else:
        is_test = not config.getboolean('e3sm_unified', 'release')

    conda_base = get_conda_base(
        args.conda_base, config, machine, env_name, shared=True
    )
    conda_base = os.path.abspath(conda_base)

    source_activation_scripts = \
        f'source {conda_base}/etc/profile.d/conda.sh'

    activate_base = f'{source_activation_scripts} && conda activate'

    # install miniconda if needed
    install_miniforge3(conda_base, activate_base)

    python, recreate, compiler, mpi, conda_mpi, activ_suffix, env_suffix, \
        activ_path = get_env_setup(args, config, machine)

    if machine is None:
        compiler = None

    nompi_compiler = None
    nompi_suffix = '_login'
    # first, make environment for login nodes.  We're using no-MPI from
    # conda-forge for now
    conda_env_path, env_nompi, activate_env, _ = build_env(
        is_test, recreate, nompi_compiler, mpi, 'nompi', version,
        python, conda_base, nompi_suffix, nompi_suffix, activate_base,
        args.local_conda_build, config)

    if local_mache:
        install_mache_from_branch(activate_env=activate_env,
                                  fork=args.mache_fork,
                                  branch=args.mache_branch)

    if not is_test:
        # make a symlink to the environment
        link = os.path.join(conda_base, 'envs', 'e3sm_unified_latest')
        check_call(f'ln -sfn {conda_env_path} {link}')

    (
        conda_env_path,
        conda_env_name,
        activate_env,
        channels
    ) = build_env(
        is_test, recreate, compiler, mpi, conda_mpi, version,
        python, conda_base, activ_suffix, env_suffix, activate_base,
        args.local_conda_build, config)

    sys_info = dict(modules=[],
                    env_vars=['export HDF5_USE_FILE_LOCKING=FALSE'])

    if compiler is not None:
        spack_base = build_spack_env(config, machine, compiler, mpi, env_name,
                                     args.tmpdir)
        esmf_mk = build_sys_ilamb_esmpy(config, machine, compiler, mpi,
                                        template_path, activate_env, channels,
                                        spack_base)
        sys_info['env_vars'].append(esmf_mk)
    else:
        spack_base = None

    test_script_filename = None
    for ext in ['sh', 'csh']:
        if compiler is not None:
            spack_script = get_spack_script(
                spack_path=spack_base, env_name="e3sm_spack_env",
                compiler=compiler, mpi=mpi, shell=ext, machine=machine)
        else:
            spack_script = ''

        script_filename = write_load_e3sm_unified(
            template_path, activ_path, conda_base, is_test, version,
            activ_suffix, conda_env_name, env_nompi, sys_info, ext, machine,
            spack_script)
        if ext == 'sh':
            test_script_filename = script_filename
        if not is_test:
            # make a symlink to the activation script
            link = f'load_latest_e3sm_unified_{machine}.{ext}'
            link = os.path.join(activ_path, link)
            check_call(f'ln -sfn {script_filename} {link}')

    check_env(test_script_filename, conda_env_name, conda_mpi, machine)

    commands = f'{activate_base} && conda clean -y -p -t'
    check_call(commands)

    paths = [activ_path, conda_base]
    if spack_base is not None:
        paths.append(spack_base)
    group = config.get('e3sm_unified', 'group')
    #update_permissions(paths, group, show_progress=True,
    #                   group_writable=False, other_readable=True)


if __name__ == '__main__':
    main()

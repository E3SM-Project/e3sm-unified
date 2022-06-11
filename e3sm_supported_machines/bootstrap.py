#!/usr/bin/env python

import os
import subprocess
import shutil
from jinja2 import Template
from importlib.resources import path
from configparser import ConfigParser

from mache import discover_machine
from mache.spack import make_spack_env, get_spack_script, \
    get_modules_env_vars_and_mpi_compilers
from mache.version import __version__ as mache_version
from mache.permissions import update_permissions
from shared import parse_args, check_call, install_miniconda, get_conda_base


def get_config(config_file, machine):
    here = os.path.abspath(os.path.dirname(__file__))
    default_config = os.path.join(here, 'default.cfg')
    config = ConfigParser()
    config.read(default_config)

    if machine is not None:
        with path('mache.machines', '{}.cfg'.format(machine)) as machine_config:
            config.read(str(machine_config))

    if config_file is not None:
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
        mpi = 'nompi'

    if machine is not None and compiler is not None:
        conda_mpi = 'hpc'
        env_suffix = f'_{machine}'
    else:
        conda_mpi = mpi
        env_suffix = f'_{conda_mpi}'

    if machine is not None:
        activ_suffix = f'_{machine}'
    else:
        activ_suffix = ''

    activ_path = config.get('e3sm_unified', 'base_path')

    return python, recreate, compiler, mpi, conda_mpi,  activ_suffix, \
        env_suffix, activ_path


def build_env(is_test, recreate, compiler, mpi, conda_mpi, version,
              python, conda_base, activ_suffix, env_suffix, activate_base,
              local_conda_build, nco_dev):

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

    # add the compiler and MPI library to the spack env name
    spack_env = '{}_{}_{}'.format(env_name, compiler, mpi)
    # spack doesn't like dots
    spack_env = spack_env.replace('.', '_')

    env_path = os.path.join(conda_base, 'envs', env_name)

    if conda_mpi in ['nompi', 'hpc']:
        mpi_prefix = conda_mpi
    else:
        mpi_prefix = f'mpi_{conda_mpi}'

    if is_test:
        channels = '--override-channels'
        if local_conda_build is not None:
            channels = f'{channels} -c {local_conda_build}'

        if nco_dev:
            channels = f'{channels} -c conda-forge/label/nco_dev'
        channels = f'{channels} -c conda-forge/label/e3sm_dev ' \
                   f'-c conda-forge -c defaults -c e3sm/label/e3sm_dev ' \
                   f'-c e3sm/label/compass_dev -c e3sm'
    else:
        channels = '--override-channels -c conda-forge -c defaults ' \
                   '-c e3sm/label/compass -c e3sm'

    packages = f'python={python} pip'

    base_activation_script = os.path.abspath(
        f'{conda_base}/etc/profile.d/conda.sh')

    activate_env = \
        'source {}; conda activate {}'.format(base_activation_script, env_name)

    if not os.path.exists(env_path) or recreate:
        print(f'creating {env_name}')
        packages = f'{packages} "e3sm-unified={version}={mpi_prefix}_*"'
        commands = f'{activate_base}; ' \
                   f'mamba create -y -n {env_name} {channels} {packages}'
        check_call(commands)

        if conda_mpi == 'hpc':
            remove_packages = 'nco tempest-remap'
            # remove conda-forge versions so we're sure to use Spack versions
            commands = f'{activate_base}; conda remove -y --force ' \
                       f'-n {env_name} {remove_packages}'
            check_call(commands)

    else:
        print(f'{env_name} already exists')

    return env_path, env_name, activate_env, channels, spack_env


def build_sys_ilamb(config, machine, compiler, mpi, template_path,
                    activate_env, channels):

    mpi4py_version = config.get('e3sm_unified', 'mpi4py')
    ilamb_version = config.get('e3sm_unified', 'ilamb')
    build_mpi4py = str(mpi4py_version != 'None')
    build_ilamb = str(ilamb_version != 'None')

    mpicc, _, _, modules = \
        get_modules_env_vars_and_mpi_compilers(machine, compiler, mpi,
                                               shell='sh')

    script_filename = 'build.bash'

    with open(f'{template_path}/build.template', 'r') as f:
        template = Template(f.read())

    # need to activate the conda environment to install mpi4py and ilamb, and
    # possibly for compilers and MPI library (if not on a supported machine)
    activate_env_lines = activate_env.replace('; ', '\n')
    modules = f'{activate_env_lines}\n{modules}'

    script = template.render(
        mpicc=mpicc, modules=modules, template_path=template_path,
        mpi4py_version=mpi4py_version, build_mpi4py=build_mpi4py,
        ilamb_version=ilamb_version, build_ilamb=build_ilamb,
        ilamb_channels=channels)
    print(f'Writing {script_filename}')
    with open(script_filename, 'w') as handle:
        handle.write(script)

    command = '/bin/bash build.bash'
    check_call(command)


def build_spack_env(config, machine, compiler, mpi, spack_env, tmpdir):

    base_path = config.get('e3sm_unified', 'base_path')
    spack_base = f'{base_path}/spack/spack_for_mache_{mache_version}'

    specs = list()
    section = config['spack_specs']
    for option in section:
        value = section[option]
        if value != '':
            specs.append(value)

    make_spack_env(spack_path=spack_base, env_name=spack_env,
                   spack_specs=specs, compiler=compiler, mpi=mpi,
                   machine=machine, tmpdir=tmpdir)

    return spack_base


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

    commands = [['mpas_analysis', '-h'],
                ['livv', '--version'],
                ['globus', '--help'],
                ['zstash', '--help'],
                ['processflow', '-v']]

    if machine is None:
        # on HPC machines, these only work on compute nodes because of mpi4py
        commands.append(['e3sm_diags', '--help'])
        imports.append('acme_diags')

    for import_name in imports:
        command = f'{activate}; python -c "import {import_name}"'
        test_command(command, os.environ, import_name)

    for command in commands:
        package = command[0]
        command_str = ' '.join(command)
        command = f'{activate}; {command_str}'
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

    machine = args.machine
    print(f'arg: {machine}')
    if machine is None:
        machine = discover_machine()
        print(f'discovered: {machine}')

    config = get_config(args.config_file, machine)

    if args.release:
        is_test = False
    else:
        is_test = not config.getboolean('e3sm_unified', 'release')

    conda_base = get_conda_base(args.conda_base, config, shared=True)
    base_activation_script = os.path.abspath(
        f'{conda_base}/etc/profile.d/conda.sh')

    activate_base = f'source {base_activation_script}; conda activate'

    # install miniconda if needed
    install_miniconda(conda_base, activate_base)

    python, recreate, compiler, mpi, conda_mpi, activ_suffix, env_suffix, \
        activ_path = get_env_setup(args, config, machine)

    if machine is None:
        compiler = None

    nco_spec = config.get('spack_specs', 'nco')
    nco_dev = ('alpha' in nco_spec or 'beta' in nco_spec)

    nompi_compiler = None
    nompi_suffix = '_nompi'
    # first, make nompi environment
    env_path, env_nompi, _, _, _ = build_env(
        is_test, recreate, nompi_compiler, mpi, 'nompi', version,
        python, conda_base, nompi_suffix, nompi_suffix, activate_base,
        args.local_conda_build, nco_dev)

    if not is_test:
        # make a symlink to the environment
        link = os.path.join(conda_base, 'envs', 'e3sm_unified_latest')
        check_call(f'ln -sfn {env_path} {link}')

    env_path, env_name, activate_env, channels, spack_env = build_env(
        is_test, recreate, compiler, mpi, conda_mpi, version,
        python, conda_base, activ_suffix, env_suffix, activate_base,
        args.local_conda_build, nco_dev)

    sys_info = dict(modules=[],
                    env_vars=['export HDF5_USE_FILE_LOCKING=FALSE'])

    if compiler is not None:
        spack_base = build_spack_env(config, machine, compiler, mpi, spack_env,
                                     args.tmpdir)
        build_sys_ilamb(config, machine, compiler, mpi, template_path,
                        activate_env, channels)
    else:
        spack_base = None

    test_script_filename = None
    for ext in ['sh', 'csh']:
        if compiler is not None:
            spack_script = get_spack_script(
                spack_path=spack_base, env_name=spack_env, compiler=compiler,
                mpi=mpi, shell=ext, machine=machine)
        else:
            spack_script = ''

        script_filename = write_load_e3sm_unified(
            template_path, activ_path, conda_base, is_test, version,
            activ_suffix, env_name, env_nompi, sys_info, ext, machine,
            spack_script)
        if ext == 'sh':
            test_script_filename = script_filename
        if not is_test:
            # make a symlink to the activation script
            link = f'load_latest_e3sm_unified_{machine}.{ext}'
            link = os.path.join(activ_path, link)
            check_call(f'ln -sfn {script_filename} {link}')

    check_env(test_script_filename, env_name, conda_mpi, machine)

    commands = f'{activate_base}; conda clean -y -p -t'
    check_call(commands)

    paths = [activ_path, conda_base]
    if spack_base is not None:
        paths.append(spack_base)
    group = config.get('e3sm_unified', 'group')
    update_permissions(paths, group, show_progress=True,
                       group_writable=False, other_readable=True)


if __name__ == '__main__':
    main()

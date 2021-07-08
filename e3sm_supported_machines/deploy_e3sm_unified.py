#!/usr/bin/env python

from __future__ import print_function

import argparse
import os
import socket
import warnings
import platform
try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

import subprocess
import sys

try:
    from configparser import ConfigParser
except ImportError:
    from six.moves import configparser
    import six

    if six.PY2:
        ConfigParser = configparser.SafeConfigParser
    else:
        ConfigParser = configparser.ConfigParser

bootstrap = False
try:
    import glob
    import stat
    import grp
    import shutil
    import requests
    import progressbar
    from lxml import etree
    from jinja2 import Template
except ImportError:
    # we need to install these packages into the base environment and try again
    bootstrap = True


def get_config(machine, config_file):
    here = os.path.abspath(os.path.dirname(__file__))
    default_config = os.path.join(here, 'default.cfg')
    config = ConfigParser()
    config.read(default_config)

    if machine is not None:
        machine_config = os.path.join(here, 'machines',
                                      '{}.cfg'.format(machine))
        config.read(machine_config)

    if config_file is not None:
        config.read(config_file)

    return config


def get_machine(machine):
    if machine is None:
        hostname = socket.gethostname()
        if hostname.startswith('acme1'):
            machine = 'acme1'
        elif hostname.startswith('andes'):
            machine = 'andes'
        elif hostname.startswith('blueslogin'):
            machine = 'anvil'
        elif hostname.startswith('ba-fe'):
            machine = 'badger'
        elif hostname.startswith('burnham'):
            machine = 'burnham'
        elif hostname.startswith('chrlogin'):
            machine = 'chrysalis'
        elif hostname.startswith('compy'):
            machine = 'compy'
        elif hostname.startswith('cooley'):
            machine = 'cooley'
        elif hostname.startswith('cori'):
            warnings.warn('defaulting to cori-haswell.  Use -m cori-knl if you'
                          ' wish to run on KNL.')
            machine = 'cori-haswell'
        elif hostname.startswith('gr-fe'):
            machine = 'grizzly'

    return machine


def get_conda_base(config):
    conda_base = os.path.abspath(os.path.join(
        config.get('deploy', 'base_path'), 'base'))
    return conda_base


def do_bootstrap(prevent_bootstrap, conda_base, activate_base):
    if bootstrap and prevent_bootstrap:
        print('At least one dependency is missing and couldn\'t be installed '
              'for you.\nYou need requests, progressbar2, lxml and jinja2')
        sys.exit(1)

    if bootstrap:
        # we don't have all the packages we need, so we need to add them
        # to the base environment, activate it and rerun
        install_miniconda(conda_base, activate_base)

        print('Rerunning the command from new conda environment')
        command = '{}; ' \
                  '{} --no-bootstrap'.format(activate_base, ' '.join(sys.argv))
        check_call(command)
        sys.exit(0)


def get_env_setup(args, config, machine):

    if args.python is not None:
        python = args.python
    else:
        python = config.get('deploy', 'python')

    if args.recreate is not None:
        recreate = args.recreate
    else:
        recreate = config.getboolean('deploy', 'recreate')

    if args.compiler is not None:
        compiler = args.compiler
        if compiler == 'None':
            compiler = None
    elif config.has_option('deploy', 'compiler'):
        compiler = config.get('deploy', 'compiler')
    else:
        compiler = None

    if args.mpi is not None:
        mpi = args.mpi
    elif config.has_option('deploy', 'mpi'):
        mpi = config.get('deploy', 'mpi')
    else:
        mpi = 'nompi'

    if machine is not None:
        conda_mpi = 'nompi'
    else:
        conda_mpi = mpi

    if machine is not None and compiler is not None:
        activ_suffix = '_{}'.format(machine)
    elif machine is not None or conda_mpi != 'nompi':
        activ_suffix = '_{}'.format(mpi)
    else:
        activ_suffix = ''

    env_suffix = activ_suffix

    activ_path = config.get('deploy', 'base_path')

    return python, recreate, compiler, mpi, conda_mpi,  activ_suffix, \
        env_suffix, activ_path


def build_env(is_test, recreate, compiler, mpi, conda_mpi, version,
              python, conda_base, activ_suffix, env_suffix, activate_base):

    if compiler is not None:
        build_dir = 'build{}'.format(activ_suffix)

        try:
            shutil.rmtree(build_dir)
        except OSError:
            pass
        try:
            os.makedirs(build_dir)
        except FileExistsError:
            pass

        os.chdir(build_dir)

    env_name = 'e3sm_unified_{}{}'.format(version, env_suffix)
    env_path = os.path.join(conda_base, 'envs', env_name)

    install_miniconda(conda_base, activate_base)

    if conda_mpi == 'nompi':
        mpi_prefix = 'nompi'
    else:
        mpi_prefix = 'mpi_{}'.format(mpi)

    if is_test:
        channels = '--override-channels -c conda-forge/label/e3sm_dev ' \
                   '-c conda-forge/label/nco_dev -c conda-forge -c defaults ' \
                   '-c e3sm/label/e3sm_dev -c e3sm'
    else:
        channels = '--override-channels -c conda-forge -c defaults -c e3sm'

    packages = 'python={} pip'.format(python)

    base_activation_script = os.path.abspath(
        '{}/etc/profile.d/conda.sh'.format(conda_base))

    activate_env = \
        'source {}; conda activate {}'.format(base_activation_script, env_name)

    if not os.path.exists(env_path) or recreate:
        print('creating {}'.format(env_name))
        packages = '{} "e3sm-unified={}={}_*"'.format(
            packages, version, mpi_prefix)
        commands = '{}; conda create -y -n {} {} {}'.format(
            activate_base, env_name, channels, packages)
        check_call(commands)
    else:
        print('{} already exists'.format(env_name))

    return env_path, env_name, activate_env, channels


def get_e3sm_compiler_and_mpi(machine, compiler, mpilib, template_path):

    root = etree.parse('{}/config_machines.xml'.format(template_path))

    machines = next(root.iter('config_machines'))

    mach = None
    for mach in machines:
        if mach.tag == 'machine' and mach.attrib['MACH'] == machine:
            break

    if mach is None:
        raise ValueError('{} does not appear to be an E3SM supported machine. '
                         'E3SM-Unified cannot be deployed with system '
                         'compilers.')

    compilers = None
    for child in mach:
        if child.tag == 'COMPILERS':
            compilers = child.text.split(',')
            break

    if compiler not in compilers:
        raise ValueError('Compiler {} not found on {}. Try: {}'.format(
            compiler, machine, compilers))

    mpilibs = None
    for child in mach:
        if child.tag == 'MPILIBS':
            mpilibs = child.text.split(',')
            break

    if mpilib not in mpilibs:
        raise ValueError('MPI library {} not found on {}. Try: {}'.format(
            mpilib, machine, mpilibs))

    machine_os = None
    for child in mach:
        if child.tag == 'OS':
            machine_os = child.text
            break

    mod_commands = []
    modules = next(mach.iter('module_system'))
    for module in modules:
        if module.tag == 'modules':
            include = True
            if 'compiler' in module.attrib and \
                    module.attrib['compiler'] != compiler:
                include = False
            if 'mpilib' in module.attrib and \
                    module.attrib['mpilib'] != mpilib and \
                    module.attrib['mpilib'] != '!mpi-serial':
                include = False
            if include:
                for command in module:
                    if command.tag == 'command':
                        text = 'module {}'.format(command.attrib['name'])
                        if command.text is not None:
                            text = '{} {}'.format(text, command.text)
                        mod_commands.append(text)

    root = etree.parse('{}/config_compilers.xml'.format(template_path))

    compilers = next(root.iter('config_compilers'))

    mpicc = None
    mpifc = None
    mpicxx = None
    for comp in compilers:
        if comp.tag != 'compiler':
            continue
        if 'COMPILER' in comp.attrib and comp.attrib['COMPILER'] != compiler:
            continue
        if 'OS' in comp.attrib and comp.attrib['OS'] != machine_os:
            continue
        if 'MACH' in comp.attrib and comp.attrib['MACH'] != machine:
            continue

        # okay, this is either a "generic" compiler section or one for this
        # machine

        for child in comp:
            if 'MPILIB' in child.attrib:
                mpi = child.attrib['MPILIB']
                if mpi[0] == '!':
                    mpi_match = mpi[1:] != mpilib
                else:
                    mpi_match = mpi == mpilib
            else:
                mpi_match = True

            if not mpi_match:
                continue

            if child.tag == 'MPICC':
                mpicc = child.text.strip()
            elif child.tag == 'MPICXX':
                mpicxx = child.text.strip()
            elif child.tag == 'MPIFC':
                mpifc = child.text.strip()

    return mpicc, mpicxx, mpifc, mod_commands


def get_sys_info(machine, compiler, mpilib, mpicc, mpicxx, mpifc,
                 mod_commands):

    if machine is None:
        machine = 'None'

    env_vars = []

    if 'intel' in compiler:
        esmf_compilers = '    export ESMF_COMPILER=intel'
    elif compiler == 'pgi':
        esmf_compilers = '    export ESMF_COMPILER=pgi\n' \
                         '    export ESMF_F90={}\n' \
                         '    export ESMF_CXX={}'.format(mpifc, mpicxx)
    else:
        esmf_compilers = '    export ESMF_F90={}\n' \
                         '    export ESMF_CXX={}'.format(mpifc, mpicxx)

    if mpilib == 'mvapich':
        esmf_comm = 'mvapich2'
        env_vars.extend(['export MV2_ENABLE_AFFINITY=0',
                         'export MV2_SHOW_CPU_BINDING=1'])
    elif mpilib == 'mpich':
        esmf_comm = 'mpich3'
    elif mpilib == 'impi':
        esmf_comm = 'intelmpi'
    else:
        esmf_comm = mpilib

    if 'cori' in machine:
        esmf_comm = 'user'
        esmf_compilers = \
            '{}\n' \
            '    export ESMF_CXXLINKLIBS="-L${{NETCDF_DIR}}/lib ' \
            '-lnetcdff -lnetcdf -mkl -lpthread"\n' \
            '    export ESMF_F90LINKLIBS="-L${{NETCDF_DIR}}/lib ' \
            '-lnetcdff -lnetcdf -mkl -lpthread"'.format(esmf_compilers)

    if machine == 'grizzly' or machine == 'badger':
        esmf_netcdf = \
            '    export ESMF_NETCDF="split"\n' \
            '    export ESMF_NETCDF_INCLUDE=$NETCDF_C_PATH/include\n' \
            '    export ESMF_NETCDF_LIBPATH=$NETCDF_C_PATH/lib64'
    else:
        esmf_netcdf = '    export ESMF_NETCDF="nc-config"'

    if 'cori' in machine:
        netcdf_paths = 'export NETCDF_C_PATH=$NETCDF_DIR\n' \
                       'export NETCDF_FORTRAN_PATH=$NETCDF_DIR\n' \
                       'export PNETCDF_PATH=$PNETCDF_DIR'
    else:
        netcdf_paths = \
            'export NETCDF_C_PATH=$(dirname $(dirname $(which nc-config)))\n' \
            'export NETCDF_FORTRAN_PATH=$(dirname $(dirname $(which nf-config)))\n' \
            'export PNETCDF_PATH=$(dirname $(dirname $(which pnetcdf-config)))'

    sys_info = dict(modules=mod_commands, mpicc=mpicc, mpicxx=mpicxx,
                    mpifc=mpifc, esmf_comm=esmf_comm, esmf_netcdf=esmf_netcdf,
                    esmf_compilers=esmf_compilers, netcdf_paths=netcdf_paths,
                    env_vars=env_vars)

    return sys_info


def build_system_libraries(config, machine, compiler, mpi, version,
                           template_path, env_path, activate_env, channels):

    mpi4py_version = config.get('deploy', 'mpi4py')
    ilamb_version = config.get('deploy', 'ilamb')
    build_mpi4py = str(compiler is not None and mpi4py_version != 'None')
    build_ilamb = str(compiler is not None and ilamb_version != 'None')
    if compiler is not None:
        esmf = config.get('deploy', 'esmf')
        tempest_extremes = config.get('deploy', 'tempest_extremes')
    else:
        # stick with the conda-forge ESMF and TempestExtremes
        esmf = 'None'
        tempest_extremes = 'None'

    force_build = False
    if machine is not None:
        mpicc, mpicxx, mpifc, mod_commands = get_e3sm_compiler_and_mpi(
            machine, compiler, mpi, template_path)
        system_libs = os.path.join(config.get('deploy', 'base_path'), 'system',
                                   machine)
        compiler_path = os.path.join(
            system_libs, 'e3sm_unified_{}'.format(version), compiler, mpi)
        esmf_path = os.path.join(compiler_path, 'esmf_{}'.format(esmf))
        tempest_extremes_path = os.path.join(
            compiler_path, 'tempest_extremes_{}'.format(tempest_extremes))
    else:
        # using conda-forge compilers
        mpicc = 'mpicc'
        mpicxx = 'mpicxx'
        mpifc = 'mpifort'
        mod_commands = []
        system_libs = None
        esmf_path = env_path
        tempest_extremes_path = env_path
        force_build = True

    sys_info = get_sys_info(machine, compiler, mpi, mpicc, mpicxx,
                            mpifc, mod_commands)

    if esmf != 'None':
        sys_info['env_vars'].append('export PATH="{}:$PATH"'.format(
            os.path.join(esmf_path, 'bin')))
        sys_info['env_vars'].append(
            'export LD_LIBRARY_PATH={}:$LD_LIBRARY_PATH'.format(
                os.path.join(esmf_path, 'lib')))

    if tempest_extremes != 'None':
        sys_info['env_vars'].append('export PATH="{}:$PATH"'.format(
            os.path.join(tempest_extremes_path, 'bin')))

    build_esmf = 'False'
    if esmf == 'None':
        esmf_branch = 'None'
    else:
        esmf_branch = 'ESMF_{}'.format(esmf.replace('.', '_'))
        if not os.path.exists(esmf_path) or force_build:
            build_esmf = 'True'

    build_tempest_extremes = 'False'
    if tempest_extremes == 'None':
        tempest_extremes_branch = 'None'
    else:
        tempest_extremes_branch = tempest_extremes
        if not os.path.exists(tempest_extremes_path) or force_build:
            build_tempest_extremes = 'True'

    script_filename = 'build.bash'

    with open('{}/build.template'.format(template_path), 'r') as f:
        template = Template(f.read())

    modules = '\n'.join(sys_info['modules'])

    # need to activate the conda environment to install mpi4py and ilamb, and
    # possibly for compilers and MPI library (if not on a supported machine)
    modules = '{}\n{}'.format(activate_env.replace('; ', '\n'), modules)

    script = template.render(
        sys_info=sys_info, modules=modules, template_path=template_path,
        mpi4py_version=mpi4py_version, build_mpi4py=build_mpi4py,
        ilamb_version=ilamb_version, build_ilamb=build_ilamb,
        ilamb_channels=channels,
        esmf_path=esmf_path, esmf_branch=esmf_branch, build_esmf=build_esmf,
        tempest_extremes_path=tempest_extremes_path,
        tempest_extremes_branch=tempest_extremes_branch,
        build_tempest_extremes=build_tempest_extremes)
    print('Writing {}'.format(script_filename))
    with open(script_filename, 'w') as handle:
        handle.write(script)

    command = '/bin/bash build.bash'
    check_call(command)

    return sys_info, system_libs


def write_load_e3sm_unified(template_path, activ_path, conda_base, is_test,
                            version, activ_suffix, env_name, env_nompi,
                            sys_info, ext):

    try:
        os.makedirs(activ_path)
    except FileExistsError:
        pass

    if is_test:
        prefix = 'test_e3sm_unified_{}'.format(version)
    else:
        prefix = 'load_e3sm_unified_{}'.format(version)

    script_filename = os.path.join(activ_path,
                                   '{}{}.{}'.format(prefix, activ_suffix, ext))

    filename = os.path.join(template_path,
                            'load_e3sm_unified.{}.template'.format(ext))
    with open(filename, 'r') as f:
        template = Template(f.read())
    if ext == 'sh':
        env_vars = '\n  '.join(sys_info['env_vars'])
    elif ext == 'csh':
        env_vars = [var.replace('export', 'setenv').replace('=', ' ') for var
                    in sys_info['env_vars']]
        env_vars = '\n  '.join(env_vars)
    else:
        raise ValueError('Unexpected extension {}'.format(ext))

    script = template.render(conda_base=conda_base, env_name=env_name,
                             env_nompi=env_nompi,
                             modules='\n  '.join(sys_info['modules']),
                             env_vars=env_vars)

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

    print('Writing {}'.format(script_filename))
    with open(script_filename, 'w') as handle:
        handle.write(script)

    return script_filename


def check_env(script_filename, env_name, conda_mpi, machine):
    print("Checking the environment {}".format(env_name))

    activate = 'source {}'.format(script_filename)

    imports = ['mpas_analysis', 'livvkit',
               'IPython', 'globus_cli', 'zstash']
    if conda_mpi != 'nompi':
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
        command = '{}; python -c "import {}"'.format(activate, import_name)
        test_command(command, os.environ, import_name)

    for command in commands:
        package = command[0]
        command = '{}; {}'.format(activate, ' '.join(command))
        test_command(command, os.environ, package)


def test_command(command, env, package):
    try:
        check_call(command, env=env)
    except subprocess.CalledProcessError as e:
        print('  {} failed'.format(package))
        raise e
    print('  {} passes'.format(package))


def check_call(commands, env=None):
    print('running: {}'.format(commands))
    proc = subprocess.Popen(commands, env=env, executable='/bin/bash',
                            shell=True)
    proc.wait()
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, commands)


def install_miniconda(conda_base, activate_base):
    if not os.path.exists(conda_base):
        print('Installing Miniconda3')
        if platform.system() == 'Linux':
            system = 'Linux'
        elif platform.system() == 'Darwin':
            system = 'MacOSX'
        else:
            system = 'Linux'
        miniconda = 'Miniconda3-latest-{}-x86_64.sh'.format(system)
        url = 'https://repo.continuum.io/miniconda/{}'.format(miniconda)
        if bootstrap:
            print(url)
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            f = urlopen(req)
            html = f.read()
            with open(miniconda, 'wb') as outfile:
                outfile.write(html)
            f.close()
        else:
            r = requests.get(url)
            with open(miniconda, 'wb') as outfile:
                outfile.write(r.content)

        command = '/bin/bash {} -b -p {}'.format(miniconda, conda_base)
        check_call(command)
        os.remove(miniconda)

    print('Doing initial setup')
    commands = '{}; ' \
               'conda config --add channels conda-forge; ' \
               'conda config --set channel_priority strict; ' \
               'conda install -y requests lxml progressbar2 jinja2 pip; ' \
               'conda update -y --all'.format(activate_base)

    check_call(commands)


def update_permissions(config, is_test, activ_path, conda_base, system_libs):
    group = config.get('deploy', 'group')

    new_uid = os.getuid()
    new_gid = grp.getgrnam(group).gr_gid

    print('changing permissions on activation scripts')
    activation_files = glob.glob('{}/*_e3sm_unified*.*'.format(
        activ_path))

    read_perm = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
    exec_perm = (stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
                 stat.S_IRGRP | stat.S_IXGRP |
                 stat.S_IROTH | stat.S_IXOTH)

    mask = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO

    for file_name in activation_files:
        os.chmod(file_name, read_perm)
        os.chown(file_name, new_uid, new_gid)

    print('changing permissions on environments')

    # first the base directories that don't seem to be included in
    # os.walk()
    directories = [conda_base]
    if system_libs is not None:
        directories.append(system_libs)
    for directory in directories:
        try:
            dir_stat = os.stat(directory)
        except OSError:
            continue

        perm = dir_stat.st_mode & mask

        if perm == exec_perm and dir_stat.st_uid == new_uid and \
                dir_stat.st_gid == new_gid:
            continue

        try:
            os.chown(directory, new_uid, new_gid)
            os.chmod(directory, exec_perm)
        except OSError:
            continue

    files_and_dirs = []
    for base in directories:
        for root, dirs, files in os.walk(base):
            files_and_dirs.extend(dirs)
            files_and_dirs.extend(files)

    widgets = [progressbar.Percentage(), ' ', progressbar.Bar(),
               ' ', progressbar.ETA()]
    bar = progressbar.ProgressBar(widgets=widgets,
                                  maxval=len(files_and_dirs),
                                  maxerror=False).start()
    progress = 0
    for base in directories:
        for root, dirs, files in os.walk(base):
            for directory in dirs:
                progress += 1
                bar.update(progress)

                directory = os.path.join(root, directory)

                try:
                    dir_stat = os.stat(directory)
                except OSError:
                    continue

                perm = dir_stat.st_mode & mask

                if perm == exec_perm and dir_stat.st_uid == new_uid and \
                        dir_stat.st_gid == new_gid:
                    continue

                try:
                    os.chown(directory, new_uid, new_gid)
                    os.chmod(directory, exec_perm)
                except OSError:
                    continue

            for file_name in files:
                progress += 1
                bar.update(progress)
                file_name = os.path.join(root, file_name)
                try:
                    file_stat = os.stat(file_name)
                except OSError:
                    continue

                perm = file_stat.st_mode & mask

                if perm & stat.S_IXUSR:
                    # executable, so make sure others can execute it
                    new_perm = exec_perm
                else:
                    new_perm = read_perm

                if perm == new_perm and file_stat.st_uid == new_uid and \
                        file_stat.st_gid == new_gid:
                    continue

                try:
                    os.chown(file_name, new_uid, new_gid)
                    os.chmod(file_name, perm)
                except OSError:
                    continue

    bar.finish()
    print('  done.')


def main():
    parser = argparse.ArgumentParser(
        description='Deploy a compass conda environment')
    parser.add_argument("--version", dest="version", default="1.5.0rc7",
                        help="The version of E3SM-Unified to deploy")
    parser.add_argument("-m", "--machine", dest="machine",
                        help="The name of the machine for loading machine-"
                             "related config options")
    parser.add_argument("-p", "--python", dest="python", type=str,
                        help="The python version to deploy")
    parser.add_argument("-i", "--mpi", dest="mpi", type=str,
                        help="The MPI library (nompi, mpich, openmpi or a "
                             "system flavor) to deploy")
    parser.add_argument("-c", "--compiler", dest="compiler", type=str,
                        help="The name of the compiler")
    parser.add_argument("--recreate", dest="recreate", action='store_true',
                        help="Recreate the environment if it exists")
    parser.add_argument("-f", "--config_file", dest="config_file",
                        help="Config file to override deployment config "
                             "options")
    parser.add_argument("--no-bootstrap", dest="no_bootstrap",
                        action='store_true',
                        help="Prevent installing Miniconda3 and rerunning "
                             "this script")
    parser.add_argument("--release", dest="release", action='store_true',
                        help="Indicates that this is a release, not a test, "
                             "build")

    args = parser.parse_args(sys.argv[1:])

    source_path = os.getcwd()
    template_path = '{}/templates'.format(source_path)

    version = args.version

    machine = get_machine(args.machine)

    config = get_config(machine, args.config_file)

    if args.release:
        is_test = False
    else:
        is_test = not config.getboolean('deploy', 'release')

    conda_base = get_conda_base(config)

    base_activation_script = os.path.abspath(
        '{}/etc/profile.d/conda.sh'.format(conda_base))

    activate_base = 'source {}; conda activate'.format(base_activation_script)

    do_bootstrap(args.no_bootstrap, conda_base, activate_base)

    python, recreate, compiler, mpi, conda_mpi, activ_suffix, env_suffix, \
        activ_path = get_env_setup(args, config, machine)

    if machine is None:
        compiler = None

    nompi_compiler = None
    nompi_suffix = '_nompi'
    # first, make nompi environment
    _, env_nompi, _, _ = build_env(
        is_test, recreate, nompi_compiler, mpi, conda_mpi, version,
        python, conda_base, nompi_suffix, nompi_suffix, activate_base)

    env_path, env_name, activate_env, channels = build_env(
        is_test, recreate, compiler, mpi, conda_mpi, version,
        python, conda_base, activ_suffix, env_suffix, activate_base)

    if not is_test:
        # make a symlink to the environment
        link = os.path.join(conda_base, 'envs', 'latest_e3sm_unified')
        check_call('ln -sfn {} {}'.format(env_path, link))

    if compiler is not None:
        sys_info, system_libs = build_system_libraries(
            config, machine, compiler, mpi, version, template_path, env_path,
            activate_env, channels)
    else:
        sys_info = dict(modules=[], env_vars=[], mpas_netcdf_paths='')
        system_libs = None

    sys_info['env_vars'].append('export HDF5_USE_FILE_LOCKING=FALSE')

    test_script_filename = None
    for ext in ['sh', 'csh']:
        script_filename = write_load_e3sm_unified(
            template_path, activ_path, conda_base, is_test, version,
            activ_suffix, env_name, env_nompi, sys_info, ext)
        if ext == 'sh':
            test_script_filename = script_filename
        if not is_test:
            # make a symlink to the activation script
            link = os.path.join(activ_path,
                                'load_latest_e3sm_unified.{}'.format(ext))
            check_call('ln -sfn {} {}'.format(script_filename, link))

    check_env(test_script_filename, env_name, conda_mpi, machine)

    commands = '{}; conda clean -y -p -t'.format(activate_base)
    check_call(commands)

    update_permissions(config, is_test, activ_path, conda_base, system_libs)


if __name__ == '__main__':
    main()

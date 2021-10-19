#!/usr/bin/env python

import os
import subprocess
import glob
import stat
import grp
import shutil
import progressbar
from jinja2 import Template

from mache import discover_machine, MachineInfo
from shared import parse_args, check_call, install_miniconda, get_config


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

    if machine is not None:
        conda_mpi = 'nompi'
    else:
        conda_mpi = mpi

    if machine is not None and compiler is not None:
        env_suffix = f'_{machine}'
    elif machine is not None or conda_mpi != 'nompi':
        env_suffix = f'_{mpi}'
    else:
        env_suffix = ''

    if machine is not None:
        activ_suffix = f'_{machine}'
    else:
        activ_suffix = env_suffix

    activ_path = config.get('e3sm_unified', 'base_path')

    return python, recreate, compiler, mpi, conda_mpi,  activ_suffix, \
        env_suffix, activ_path


def build_env(is_test, recreate, compiler, mpi, conda_mpi, version,
              python, conda_base, activ_suffix, env_suffix, activate_base):

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

    if conda_mpi == 'nompi':
        mpi_prefix = 'nompi'
    else:
        mpi_prefix = f'mpi_{mpi}'

    if is_test:
        channels = '--override-channels -c conda-forge/label/e3sm_dev ' \
                   '-c conda-forge -c defaults ' \
                   '-c e3sm/label/e3sm_dev -c e3sm'
    else:
        channels = '--override-channels -c conda-forge -c defaults -c e3sm'

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
    else:
        print(f'{env_name} already exists')

    return env_path, env_name, activate_env, channels


def get_sys_info(machine, compiler, mpilib, mpicc, mpicxx, mpifc,
                 mod_commands):

    if machine is None:
        machine = 'None'

    env_vars = []

    if 'intel' in compiler:
        esmf_compilers = '    export ESMF_COMPILER=intel'
    elif compiler == 'pgi':
        esmf_compilers = f'    export ESMF_COMPILER=pgi\n' \
                         f'    export ESMF_F90={mpifc}\n' \
                         f'    export ESMF_CXX={mpicxx}'
    else:
        esmf_compilers = f'    export ESMF_F90={mpifc}\n' \
                         f'    export ESMF_CXX={mpicxx}'

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
            f'{esmf_compilers}\n' \
            f'    export ESMF_CXXLINKLIBS="-L${{NETCDF_DIR}}/lib ' \
            f'-lnetcdff -lnetcdf -mkl -lpthread"\n' \
            f'    export ESMF_F90LINKLIBS="-L${{NETCDF_DIR}}/lib ' \
            f'-lnetcdff -lnetcdf -mkl -lpthread"'

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


def build_system_libraries(config, machine, machine_info, compiler, mpi, version,
                           template_path, env_path, activate_env, channels):

    mpi4py_version = config.get('e3sm_unified', 'mpi4py')
    ilamb_version = config.get('e3sm_unified', 'ilamb')
    build_mpi4py = str(compiler is not None and mpi4py_version != 'None')
    build_ilamb = str(compiler is not None and ilamb_version != 'None')
    if compiler is not None:
        esmf = config.get('e3sm_unified', 'esmf')
        tempest_extremes = config.get('e3sm_unified', 'tempest_extremes')
    else:
        # stick with the conda-forge ESMF and TempestExtremes
        esmf = 'None'
        tempest_extremes = 'None'

    force_build = False
    if machine is not None:
        mpicc, mpicxx, mpifc, mod_commands = \
            machine_info.get_modules_and_mpi_compilers(compiler, mpi)
        system_libs = os.path.join(config.get('e3sm_unified', 'base_path'),
                                   'system', machine)
        compiler_path = os.path.join(
            system_libs, f'e3sm_unified_{version}', compiler, mpi)
        esmf_path = os.path.join(compiler_path, f'esmf_{esmf}')
        tempest_extremes_path = os.path.join(
            compiler_path, f'tempest_extremes_{tempest_extremes}')
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
        bin_dir = os.path.join(esmf_path, 'bin')
        sys_info['env_vars'].append(f'export PATH="{bin_dir}:$PATH"')
        lib_dir = os.path.join(esmf_path, 'lib')
        sys_info['env_vars'].append(
            f'export LD_LIBRARY_PATH={lib_dir}:$LD_LIBRARY_PATH')

    if tempest_extremes != 'None':
        bin_dir = os.path.join(tempest_extremes_path, 'bin')
        sys_info['env_vars'].append(f'export PATH="{bin_dir}:$PATH"')

    build_esmf = 'False'
    if esmf == 'None':
        esmf_branch = 'None'
    else:
        esmf_str = esmf.replace('.', '_')
        esmf_branch = f'ESMF_{esmf_str}'
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

    with open(f'{template_path}/build.template', 'r') as f:
        template = Template(f.read())

    modules = '\n'.join(sys_info['modules'])

    # need to activate the conda environment to install mpi4py and ilamb, and
    # possibly for compilers and MPI library (if not on a supported machine)
    activate_env_lines = activate_env.replace('; ', '\n')
    modules = f'{activate_env_lines}\n{modules}'

    script = template.render(
        sys_info=sys_info, modules=modules, template_path=template_path,
        mpi4py_version=mpi4py_version, build_mpi4py=build_mpi4py,
        ilamb_version=ilamb_version, build_ilamb=build_ilamb,
        ilamb_channels=channels,
        esmf_path=esmf_path, esmf_branch=esmf_branch, build_esmf=build_esmf,
        tempest_extremes_path=tempest_extremes_path,
        tempest_extremes_branch=tempest_extremes_branch,
        build_tempest_extremes=build_tempest_extremes)
    print(f'Writing {script_filename}')
    with open(script_filename, 'w') as handle:
        handle.write(script)

    command = '/bin/bash build.bash'
    check_call(command)

    return sys_info, system_libs


def write_load_e3sm_unified(template_path, activ_path, conda_base, is_test,
                            version, activ_suffix, env_name, env_nompi,
                            sys_info, ext, machine):

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


def update_permissions(config, activ_path, conda_base, system_libs):
    group = config.get('e3sm_unified', 'group')

    new_uid = os.getuid()
    new_gid = grp.getgrnam(group).gr_gid

    print('changing permissions on activation scripts')
    activation_files = glob.glob(f'{activ_path}/*_e3sm_unified*.*')

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
    args = parse_args()

    source_path = os.getcwd()
    template_path = f'{source_path}/templates'

    version = args.version

    machine = args.machine
    print(f'arg: {machine}')
    if machine is None:
        machine = discover_machine()
        print(f'discovered: {machine}')

    if machine is not None:
        machine_info = MachineInfo(machine=machine)
    else:
        machine_info = None

    config = get_config(args.config_file, machine)

    if args.release:
        is_test = False
    else:
        is_test = not config.getboolean('e3sm_unified', 'release')

    conda_base = os.path.abspath(os.path.join(
        config.get('e3sm_unified', 'base_path'), 'base'))

    base_activation_script = os.path.abspath(
        f'{conda_base}/etc/profile.d/conda.sh')

    activate_base = f'source {base_activation_script}; conda activate'

    # install miniconda if needed
    install_miniconda(conda_base, activate_base)

    python, recreate, compiler, mpi, conda_mpi, activ_suffix, env_suffix, \
        activ_path = get_env_setup(args, config, machine)

    if machine is None:
        compiler = None

    nompi_compiler = None
    nompi_suffix = '_nompi'
    # first, make nompi environment
    env_path, env_nompi, _, _ = build_env(
        is_test, recreate, nompi_compiler, mpi, conda_mpi, version,
        python, conda_base, nompi_suffix, nompi_suffix, activate_base)

    if not is_test:
        # make a symlink to the environment
        link = os.path.join(conda_base, 'envs', 'e3sm_unified_latest')
        check_call(f'ln -sfn {env_path} {link}')

    env_path, env_name, activate_env, channels = build_env(
        is_test, recreate, compiler, mpi, conda_mpi, version,
        python, conda_base, activ_suffix, env_suffix, activate_base)

    if compiler is not None:
        sys_info, system_libs = build_system_libraries(
            config, machine, machine_info, compiler, mpi, version,
            template_path, env_path, activate_env, channels)
    else:
        sys_info = dict(modules=[], env_vars=[], mpas_netcdf_paths='')
        system_libs = None

    sys_info['env_vars'].append('export HDF5_USE_FILE_LOCKING=FALSE')

    test_script_filename = None
    for ext in ['sh', 'csh']:
        script_filename = write_load_e3sm_unified(
            template_path, activ_path, conda_base, is_test, version,
            activ_suffix, env_name, env_nompi, sys_info, ext, machine)
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

    update_permissions(config, activ_path, conda_base, system_libs)


if __name__ == '__main__':
    main()

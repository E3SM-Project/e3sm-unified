#!/usr/bin/env python3

from __future__ import print_function

import os
import sys

from configparser import ConfigParser

from shared import (
    check_call,
    get_conda_base,
    install_miniforge3,
    parse_args,
)


def get_config(config_file):
    here = os.path.abspath(os.path.dirname(__file__))
    default_config = os.path.join(here, 'default.cfg')
    config = ConfigParser()
    config.read(default_config)

    if config_file is not None:
        config.read(config_file)

    return config


def bootstrap(activate_install_env, source_path, local_conda_build):

    print('Creating the e3sm_unified conda environment')
    bootstrap_command = f'{source_path}/bootstrap.py'
    joined_args = ' '.join(sys.argv[1:])
    command = f'{activate_install_env} && ' \
              f'{bootstrap_command} {joined_args}'
    if local_conda_build is not None:
        command = f'{command} --local_conda_build {local_conda_build}'
    check_call(command)
    sys.exit(0)


def setup_install_env(activate_base, use_local, mache):
    print('Setting up a conda environment for installing E3SM-Unified')
    channels = []
    if use_local:
        channels.append('--use-local')
    if 'rc' in mache:
        channels.append('-c conda-forge/label/mache_dev')
    channels = ' '.join(channels)
    commands = f'{activate_base} && ' \
               f'conda create -y -n temp_e3sm_unified_install ' \
               f'{channels} progressbar2 jinja2 {mache}'

    check_call(commands)


def remove_install_env(activate_base):
    print('Removing conda environment for installing  E3SM-Unified')
    commands = f'{activate_base} && ' \
               f'conda remove -y --all -n ' \
               f'temp_e3sm_unified_install'

    check_call(commands)


def install_mache_from_branch(activate_install_env, fork, branch):
    print('Clone and install local mache\n')
    commands = f'{activate_install_env} && ' \
                f'rm -rf build_mache && ' \
                f'mkdir -p build_mache && ' \
                f'cd build_mache && ' \
                f'git clone -b {branch} ' \
                f'git@github.com:{fork}.git mache && ' \
                f'cd mache && ' \
                f'conda install -y --file spec-file.txt && ' \
                f'python -m pip install --no-deps .'

    check_call(commands)


def main():
    args = parse_args(bootstrap=False)
    source_path = os.getcwd()

    config = get_config(args.config_file)

    conda_base = get_conda_base(args.conda_base, config, shared=False)
    conda_base = os.path.abspath(conda_base)

    source_activation_scripts = \
        f'source {conda_base}/etc/profile.d/conda.sh'

    local_mache = args.mache_fork is not None and args.mache_branch is not None
    if local_mache:
        mache = ''
    else:
        mache_version = config.get('e3sm_unified', 'mache')
        mache = f'"mache={mache_version}"'

    activate_base = f'{source_activation_scripts} && conda activate'

    activate_install_env = \
        f'{source_activation_scripts} && ' \
        f'conda activate temp_e3sm_unified_install'

    # install miniconda if needed
    install_miniforge3(conda_base, activate_base)

    setup_install_env(activate_base, args.use_local, mache)

    if local_mache:
        install_mache_from_branch(activate_install_env=activate_install_env,
                                  fork=args.mache_fork,
                                  branch=args.mache_branch)

    if args.release:
        is_test = False
    else:
        is_test = not config.getboolean('e3sm_unified', 'release')

    if is_test and args.use_local:
        local_conda_build = os.path.abspath(f'{conda_base}/conda-bld')
    else:
        local_conda_build = None

    bootstrap(activate_install_env, source_path, local_conda_build)

    remove_install_env(activate_base)


if __name__ == '__main__':
    main()
